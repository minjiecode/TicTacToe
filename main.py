#!/usr/bin/env python

"""main.py - This file contains handlers that are called by taskqueue and/or
cronjobs."""
import logging

import webapp2
from google.appengine.api import mail, app_identity
from api import TicTacToeApi

from models import User, Game


class SendReminderEmail(webapp2.RequestHandler):
    def get(self):
        """Send a reminder email to each User with an email about games.
        Called every hour using a cron job"""
        app_id = app_identity.get_application_id()
        games = Game.query(Game.game_over == False)
        for game in games:
            user = game.user.get()
            safekey = game.key.urlsafe()
            subject = '{}, You have unfinished game!'.format(user.name)
            body = """
            Hello {}, you have unfinished game!\n
            Click https://tictactoe-mj.appspot.com/game/{} to access the game
            """.format(user.name, safekey)
            # This will send test emails, the arguments to send_mail are:
            # from, to, subject, body
            mail.send_mail('noreply@{}.appspotmail.com'.format(app_id),
                           user.email,
                           subject,
                           body)


class UpdateActiveGames(webapp2.RequestHandler):
    def post(self):
        """Update count of active games announcement in memcache."""
        TicTacToeApi._cache_active_games()
        self.response.set_status(204)


app = webapp2.WSGIApplication([
    ('/crons/send_reminder', SendReminderEmail),
    ('/tasks/cache_active_games', UpdateActiveGames),
], debug=True)
