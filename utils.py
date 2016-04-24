"""utils.py - File for collecting general utility functions."""

import logging
from google.appengine.ext import ndb
import endpoints
import re,random

def get_by_urlsafe(urlsafe, model):
    """Returns an ndb.Model entity that the urlsafe key points to. Checks
        that the type of entity returned is of the correct kind. Raises an
        error if the key String is malformed or the entity is of the incorrect
        kind
    Args:
        urlsafe: A urlsafe key string
        model: The expected entity kind
    Returns:
        The entity that the urlsafe Key string points to or None if no entity
        exists.
    Raises:
        ValueError:"""
    try:
        key = ndb.Key(urlsafe=urlsafe)
    except TypeError:
        raise endpoints.BadRequestException('Invalid Key')
    except Exception, e:
        if e.__class__.__name__ == 'ProtocolBufferDecodeError':
            raise endpoints.BadRequestException('Invalid Key')
        else:
            raise

    entity = key.get()
    if not entity:
        return None
    if not isinstance(entity, model):
        raise ValueError('Incorrect Kind')
    return entity


def parseState(state):
    """Parse the game state into list"""
    result = [list(state[:3]),list(state[3:6]),list(state[6:])] 
    return result

def evaluate(state):
    board = parseState(state)
    #win horizontally
    for row in board:
        if row[0] and row[0] == row[1] and row[0] == row[2] and row[0] in "XO":
          return row[0]
    #win vertically
    for col in range(0,3):
      if board[0][col] and board[0][col] == board[1][col] and \
          board[0][col] == board[2][col] and board[0][col] in "XO" :
          return board[0][col]
    #win diagonally
    if (board[0][0] and board[0][0] == board[1][1] and board[0][0] == board[2][2]) \
          and board[0][0] in "XO":
          return board[0][0]
    if (board[2][0] and board[2][0] == board[1][1] and board[2][0] == board[0][2]) \
          and board[2][0] in "XO":
          return board[2][0] 
    return None

def add_random_move(state):
    """Adds a random 'X' to a tictactoe board.
    Args:
        board_state: String; contains only '-', 'X', and 'O' characters.
    Returns:
        A new board with one of the '-' characters converted into an 'X';
        this simulates an artificial intelligence making a move.
    """
    result = list(state)  # Need a mutable object

    free_indices = [match.start()
                    for match in re.finditer('-', state)]
    random_index = random.choice(free_indices)
    result[random_index] = 'X'

    return ''.join(result)