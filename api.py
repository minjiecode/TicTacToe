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

from models import User, Game, Score, GameHistory
from models import StringMessage, NewGameForm, GameForm, MakeMoveForm,\
    ScoreForms, GameHistoryForms, GameForms, UserForms
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
GET_USER_GAME_REQUEST = endpoints.ResourceContainer(user_name = messages.StringField(1, required = True),)

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
        user = User(name=request.user_name, email=request.email, rankingscore = 0)
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

    @endpoints.method(request_message = GET_USER_GAME_REQUEST,
                      response_message = GameForms,
                      path = "game/{user_name}/active",
                      name = 'get_user_games',
                      http_method = 'GET')
    def get_user_game(self,request):
        """Return active games for specified user"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        games = Game.query(Game.user == user.key)
        active_games = games.filter(Game.game_over == False)
        return GameForms(items = [game.to_form("Time to make a move!") for game in active_games])


    @endpoints.method(request_message = GET_GAME_REQUEST,
                       response_message = StringMessage,
                       path = "game/{urlsafe_game_key}/cancel",
                       name = 'cancel_game',
                       http_method = 'DELETE')
    def cancel_game(self,request):
        """Cancel unfinished game"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            if game.game_over:
                return Message(message = "Completed Game cannot be deleted.")
            else:
                try:
                    game.key.delete()
                except Exception:
                    raise endpoints.InternalServerErrorException(
                        'Error in cencelling the game')
            return Message(message = "Game Deleted")
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
            game.history()
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
            game.history()
            game.player = True
            game.put()
            return game.to_form(msg)

# -------- Queries ------------------

    @endpoints.method(request_message = GET_GAME_REQUEST,
                      response_message = GameHistoryForms,
                      path = 'game/{urlsafe_game_key}/history',
                      name = 'get_game_history',
                      http_method = 'GET'
                      )
    def get_game_history(self,request):
        """Return moves for specified game"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        return GameHistoryForms(items = [record.to_form() for record in \
           GameHistory.query(GameHistory.game == game.key).order(GameHistory.movecount)])


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


    @endpoints.method(response_message = UserForms,
                      path = 'ranking',
                      name = 'get_ranking',
                      http_method = 'GET')
    def get_user_rankings(self, request):
        """Get user rankings"""
        users = User.query()
        for user in users:
            games = Score.query(Score.user == user.key)
            win = Score.query().filter(Score.result == 'Win').fetch()
            draw = Score.query().filter(Score.result == 'Draw').fetch()
            lose = Score.query().filter(Score.result == "Lose").fetch()
            # The final score is base on both performance and participation.
            final_score = 5*len(win) + 3*len(win)+ 1*len(lose)
            user.rankingscore = final_score
            user.put()
        return UserForms(items=[user.to_form() for user in User.query().order(-User.rankingscore)])


    @staticmethod
    def _cache_active_games():
        """Populates memcache with the count of active games"""
        games = Game.query(Game.game_over == False).fetch()
        if games:
            count = len(games)
            memcache.set(MEMCACHE_ACTIVE_GAMES,
                         'The number of active game(s) is {}'.format(count))


api = endpoints.api_server([TicTacToeApi])
