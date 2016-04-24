# -*- coding: utf-8 -*-`
"""api.py - Create and configure the Game API exposing the resources.
This can also contain game logic. For more complex games it would be wise to
move game logic to another file. Ideally the API will be simple, concerned
primarily with communication to/from the API's users."""


import logging
import endpoints
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue

from models import User, Game, Score, GameRecord
from models import StringMessage, NewGameForm, GameForm, MakeMoveForm,\
    ScoreForms, GameRecordForms
from utils import get_by_urlsafe, evaluate, parseState, add_random_move

NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GET_GAME_REQUEST = endpoints.ResourceContainer(
        urlsafe_game_key=messages.StringField(1),)
MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
        MakeMoveForm,
        urlsafe_game_key=messages.StringField(1),)
GET_RANDOM_MOVE_REQUEST = endpoints.ResourceContainer(urlsafe_game_key = messages.StringField(1),)
USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),
                                           email=messages.StringField(2))
GET_GAME_RECORDS = endpoints.ResourceContainer(
        urlsafe_game_key = messages.StringField(1),)

MEMCACHE_ACTIVE_GAMES = 'ACTIVE_GAMES'

@endpoints.api(name='tic_tac_toe', version='v1')
class TicTacToeApi(remote.Service):
    """Game API"""
    

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                    'A User with that name already exists!')
        user = User(name=request.user_name, email=request.email)
        user.put()
        return StringMessage(message='User {} created!'.format(
                request.user_name))

    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        game = Game.new_game(user.key)
        # Use a task queue to update the active games.
        # This operation is not needed to complete the creation of a new game
        # so it is performed out of sequence.
        taskqueue.add(url='/tasks/cache_active_games')
        return game.to_form('Good luck playing Tic-tac-toe!')

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            if game.player:
                return game.to_form('Time to make a move!')
            else:
                return game.to_form('This is not your turn.')
        else:
            raise endpoints.NotFoundException('Game not found!')


# - - - Moves - - - - - - - - - - - - - - - - -

    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='make_move',
                      http_method='PUT')
    def make_move(self, request):
        """Makes a move. Returns a game state with message. """
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        #check if the game is over, update the score list if needed
        if evaluate(game.state):
            outcome = evaluate(game.state)
            if outcome == "O":
                msg = "Win"
            else:
                msg = "Lose"
            game.end_game(msg)
            game.game_over = True
            game.put()
        else:
            if "-" not in game.state:
              game.end_game("Draw")
              game.game_over = True
        if game.game_over:
            return game.to_form('Game already over!')
        #check if it is player's turn
        if game.player:
            if request.move not in range(0,9):
              raise endpoints.BadRequestException('Invalid Move')
            if game.state[request.move] != "-":
              raise endpoints.BadRequestException('Invalid Move')
            #update the board state
            board = list(game.state)
            board[request.move] = "O" 
            game.state = ''.join(board)
            #update movecount
            game.movecount += 1
            #evaluate the result
            if evaluate(game.state):
                game.end_game("Win")
                return game.to_form('You win!')
            if "-" not in game.state:
                game.end_game("Draw")
                return game.to_form('This is a Draw.')
            msg = "AI's turn"
            game.record()
            game.player = False
            game.put()
            return game.to_form(msg)
        else:
            msg = "This is not your turn"
            return game.to_form(msg)

    @endpoints.method(request_message = GET_RANDOM_MOVE_REQUEST,
                      response_message=GameForm,
                      path = 'game/{urlsafe_game_key}/random',
                      name = "get_random_move",
                      http_method = "PUT")
    def get_random_move(self,request):
        """Get Random Generated Moves"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        #check if the game is over, update the score list if needed
        if evaluate(game.state):
            outcome = evaluate(game.state)
            if outcome == "O":
                msg = "Win"
                game.end_game(msg)
            else:
                msg = "Lose"
                game.end_game(msg)
            game.game_over = True
            game.put()
        else:
            if "-" not in game.state:
              game.end_game("Draw")
              game.game_over = True
        if game.game_over:
            return game.to_form('Game already over!')
        #check if it is ai's turn
        if game.player:
            msg = "Waiting for your move."
            return game.to_form(msg)
        else:
            #update board with a random move
            game.state = add_random_move(game.state)
            #update movecount
            game.movecount += 1
            #evaluate the result
            if evaluate(game.state):
                game.end_game("Lose")
                return game.to_form('You Lose!')
            if "-" not in game.state:
                game.end_game("Draw")
                return game.to_form('This is a Draw.')
            msg = "Your turn"
            game.record()
            game.player = True
            game.put()
            return game.to_form(msg)

    @endpoints.method(request_message = GET_GAME_RECORDS,
                      response_message = GameRecordForms,
                      path = 'game/{urlsafe_game_key}/record',
                      name = 'get_game_records',
                      http_method = 'GET'
                      )
    def get_game_records(self,request):
        """Return moves for specified game"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        return GameRecordForms(items = [record.to_form() for record in \
           GameRecord.query(GameRecord.game == game.key)])


    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """Return all scores"""
        return ScoreForms(items=[score.to_form() for score in Score.query()])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=ScoreForms,
                      path='scores/user/{user_name}',
                      name='get_user_scores',
                      http_method='GET')
    def get_user_scores(self, request):
        """Returns all of an individual User's scores"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        scores = Score.query(Score.user == user.key)
        return ScoreForms(items=[score.to_form() for score in scores])

    @endpoints.method(response_message=StringMessage,
                      path='games/active_games',
                      name='get_active_games',
                      http_method='GET')
    def get_active_games(self, request):
        """Get the cached active games"""
        return StringMessage(message=memcache.get(MEMCACHE_ACTIVE_GAMES) or '')

    @staticmethod
    def _cache_active_games():
        """Populates memcache with the count of active games"""
        games = Game.query(Game.game_over == False).fetch()
        if games:
            count = len(games)
            memcache.set(MEMCACHE_ACTIVE_GAMES,
                         'The number of active game(s) is {}'.format(count))


api = endpoints.api_server([TicTacToeApi])
