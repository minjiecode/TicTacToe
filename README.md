#Tic-Tac-Toe
###Version 1.0 (A simple backend for a Tic Tac Toe game using Google Cloud
###Endpoints, App Engine, and Python) 
####*FSND Project 4: Design a Game*

####Description:
Tic-tac-toe is a  game for two players, X and O, who take turns marking the 
spaces in a 3×3 grid. The player who succeeds in placing three of their marks 
in a horizontal, vertical, or diagonal row wins the game. (Cited from [wiki][1])
![Example of one tic-tac-toe game, won by X](images/example.png)

This version 1.0 is designed for one human player to play with the psuedo AI player. 

####Setup Instructions:
1.  Update the value of application in app.yaml to the app ID you have registered
 in the App Engine admin console and would like to use to host your instance of 
 this sample.
1.  Run the app with the devserver using dev_appserver.py DIR, and ensure it's
 running by visiting the API Explorer - by default localhost:8080/_ah/api/explorer.
1.  (Optional) Generate your client library(ies) with the endpoints tool.
 Deploy your application.

####Files included:
- api.py: Contains endpoints and game playing logic.
- app.yaml: App configuration.
- cron.yaml: Cronjob configuration.
- main.py: Handler for taskqueue handler.
- models.py: Entity and message definitions including helper methods.
- utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.

##Endpoints Included:
 - **create_user**
    - Path: 'user'
    - Method: POST
    - Parameters: user_name, email (optional)
    - Returns: Message confirming creation of the User.
    - Description: Creates a new User. user_name provided must be unique. Will 
    raise a ConflictException if a User with that user_name already exists.
    
 - **new_game**
    - Path: 'game'
    - Method: POST
    - Parameters: user_name, min, max, attempts
    - Returns: GameForm with initial game state.
    - Description: Creates a new Game. user_name provided must correspond to an
    existing user - will raise a NotFoundException if not. Min must be less than
    max. Also adds a task to a task queue to update the total count for active games. 
     
 - **get_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with current game state.
    - Description: Returns the current state of a game.
 

 - **get_user_game**
    - Path: 'game/{user_name}/active'
    - Method: GET
    - Parameters: user_name
    - Returns: GameForms with all active games from the user.
    - Description: Returns all active games from the user.

 - **cancel_game**
    - Path: 'game/{urlsafe_game_key}/cancel',
    - Method: DELETE
    - Parameters: urlsafe_game_key
    - Returns: StringMessage
    - Description: Cancel unfinished game.

 - **make_move**
    - Path: 'game/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key, move
    - Returns: GameForm with new game state.
    - Description: Send and record the move of the human player.

 - **get_random_move**
    - Path: 'game/{urlsafe_game_key}/random'
    - Method: PUT
    - Parameters: urlsafe_game_key
    - Returns: GameForm with new game state.
    - Description: Generate and record the move of the "AI" player.
 
 - **get_game_history**
    - Path: 'game/{urlsafe_game_key}/history'
    - Method: GET
    - Parameters; urlsafe_game_key
    - Returns: GameHistoryForms with game move record.
    - Description: Show the move history of different human and "AI" player took in chronical order.

 - **get_scores**
    - Path: 'scores'
    - Method: GET
    - Parameters: None
    - Returns: ScoreForms.
    - Description: Returns all Scores in the database (unordered).
    
 - **get_user_scores**
    - Path: 'scores/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: ScoreForms. 
    - Description: Returns all Scores recorded by the provided player (unordered).
    Will raise a NotFoundException if the User does not exist.
    
 - **get_active_games**
    - Path: 'games/active_games'
    - Method: GET
    - Parameters: None
    - Returns: StringMessage
    - Description: Gets the count of active games from a previously cached memcache key.

- **get_user_rankings**
    - Path: 'ranking'
    - Method: GET
    - Parameters: None
    - Returns: UserForm ordered by performance index
    - Description: Show the ranking of users


##Models Included:
 - **User**
    - Stores unique user_name and (optional) email address.
    
 - **Game**
    - Stores unique game states. Associated with User model via KeyProperty.
    
 - **Score**
    - Records completed games. Associated with Users model via KeyProperty.

 - **GameHistory**
    - Records every move user/AI player made. Associated with Games via KeyProperty.
    
##Forms Included:
 - **GameForm**
    - Representation of a Game's state (urlsafe_key, attempts_remaining,
    game_over flag, message, user_name).
 - **NewGameForm**
    - Used to create a new game (user_name, min, max, attempts)
 - **MakeMoveForm**
    - Inbound make move form (guess).
 - **GameHistoryForm**
    - Outbound GameHistory Infomation.
 - **GameHistoryForms**
    - Multiple GameHistoryForm container.
 - **ScoreForm**
    - Representation of a completed game's Score (user_name, date, won flag,
    guesses).
 - **ScoreForms**
    - Multiple ScoreForm container.
 - **StringMessage**
    - General purpose String container.
 - **UserForm**
    - Outbound User Information for ranking display.
 - **UserForms**
    - Multiple UserForm container.

 [1]: https://en.wikipedia.org/wiki/Tic-tac-toe



