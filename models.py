"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb


class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email =ndb.StringProperty()


class Game(ndb.Model):
    """Game object"""
    state = ndb.StringProperty(required = True)
    game_over = ndb.BooleanProperty(required=True, default=False)
    user = ndb.KeyProperty(required=True, kind='User')
    player = ndb.BooleanProperty(required = True) #True: Human Player; False: AIPlayer
    movecount = ndb.IntegerProperty(required = True)

    @classmethod
    def new_game(cls, user):
        """Creates and returns a new game"""
        game = Game(user=user,
                    state = "----------",
                    game_over= False,
                    player = True,
                    movecount = 0)
        game.put()
        return game

    def to_form(self, message):
        """Returns a GameForm representation of the Game"""
        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.user_name = self.user.get().name
        form.game_over = self.game_over
        form.message = message
        form.state = self.state
        form.player = self.player
        form.movecount = self.movecount
        return form

    def end_game(self, result):
        """Ends the game - 3 Results("Win", "Lose", "Draw")"""
        self.game_over = True
        self.put()
        # Add the game to the score 'board'
        score = Score(user=self.user, date=date.today(), result = result)
        score.put()

    def record(self):
        if self.player:
            player = self.user.get().name
        else:
            player = "AIPlayer"
        record = GameRecord(game = self.key, state = self.state, player = player, movecount = self.movecount)
        record.put()


class Score(ndb.Model):
    """Score object"""
    user = ndb.KeyProperty(required=True, kind='User')
    date = ndb.DateProperty(required=True)
    result = ndb.StringProperty(required=True)

    def to_form(self):
        return ScoreForm(user_name=self.user.get().name, result=self.result,
                         date=str(self.date))

class GameRecord(ndb.Model):
    """History for each game"""
    state = ndb.StringProperty(required = True)
    player = ndb.StringProperty()
    game = ndb.KeyProperty(required = True, kind = Game)
    movecount = ndb.IntegerProperty(required = True)

    def to_form(self):
        return GameRecordForm(movecount = self.movecount, player = self.player, state = self.state)



class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    state = messages.StringField(2,required = True)
    game_over = messages.BooleanField(3, required=True)
    message = messages.StringField(4, required=True)
    user_name = messages.StringField(5, required=True)
    player = messages.BooleanField(6,required = True)
    movecount = messages.IntegerField(7,required = True)


class NewGameForm(messages.Message):
    """Used to create a new game"""
    user_name = messages.StringField(1, required=True)


class MakeMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    move = messages.IntegerField(1, required=True)


class GameRecordForm(messages.Message):
    """GameRecordForm for outbound move record information"""
    player = messages.StringField(1)
    state = messages.StringField(2,required = True)
    movecount = messages.IntegerField(3)

class GameRecordForms(messages.Message):
    """Return multiple GameRecordForms"""
    items = messages.MessageField(GameRecordForm,1,repeated = True)


class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    user_name = messages.StringField(1, required=True)
    date = messages.StringField(2, required=True)
    result = messages.StringField(3, required=True)


class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)


class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)
