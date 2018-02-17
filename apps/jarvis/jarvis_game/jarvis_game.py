import appdaemon.plugins.hass.hassapi as hass
import ast
import sys
import string
import json
import uuid
import requests
import os, re, time
import paho.mqtt.publish as publish
#from fuzzywuzzy import fuzz, process
import urllib


##########################
# Jarvis Game Skill
##########################

class jarvis_game(hass.Hass):

    def initialize(self):
        if not self.args.get('enabled'):
            return
        self.jarvis = self.get_app('jarvis_core')
        self.dialogue = self.get_app('jarvis_dialogue')
        self.jarvis.jarvis_register_intent('play_game',
                                           self.start_game)
        self.session_id = {}
        self.site_id = 'default'
        self.jarvis.enable_intents(state=True)
        self.global_vars['dialogue_enabled'][self.site_id] = False

        self.game = 'zork1'
        self.pid = 0
        self.location = ''
        self.score = 0
        self.move = 0
        self.text = ''

    def start_game(self, data=None, *args, **kwargs):
        self.log("__function__: %s" % data)
        if self.global_vars['dialogue_enabled'].get('self.site_id') == True:
            self.log("__function__: Already running a dialogue!")
        self.site_id = data.get('siteId', 'default')

        game = requests.post('http://localhost:8898/games',
                             json={'game': self.game, 'label': self.game})
        self.pid = game.json().get('pid', 0)
        if not self.pid:
            self.jarvis.jarvis_end_session(
                {'sessionId': data.get('sessionId', ''),
                 'text': 'Sorry, I could not start {}'.format(self.game)})
            return
        else:
            self.jarvis.jarvis_end_session(
                {'sessionId': data.get('sessionId', ''),
                 'text': 'OK, lets play a game'})

        self.parse_game(game.json())

        self.dialogue.start_dialogue(data, dialogue_callback=self.game_callback,
            start_text=self.text)

    def game_callback(self, data, *args, **kwargs):
        self.log("__function__:  data %s" % data)

        for cancel_handle in list(self.dialogue.cancel_dialogue):
            self.dialogue.cancel_listen_event(cancel_handle)
            self.dialogue.cancel_dialogue.remove(cancel_handle)

        if not data.get('text'):
            # Start listening again
            self.dialogue.dialogue_listener_cb(data)
            return

        if 'end' in data.get('text'):
            self.dialogue.end_dialogue(data)
            return

        if 'bye' in data.get('text'):
            self.dialogue.end_dialogue(data)
            return

        game = requests.post('http://localhost:8898/games/{}/action'.format(self.pid), json={'action': data.get('text')})
        self.log("__function__: response {}".format(game.json()))
        self.parse_game(game.json())

        self.dialogue.dialogue_say({'siteId': self.site_id,
                           'text': self.text})

    # Helper to handle parsing the console text
    #TODO Make it better
    def parse_game(self, data):
        self.log("__function__:  data %s" % data)
        if data.get('data'):
            self.text = data.get('data').split('\n\n')[-1].replace('\n', ' ')

            self.location = data.get('data').split('Score', 1)[0].strip()
            self.moves = 0
            self.score = 0
        self.log("__function__: %s ---- %s" %  (self.location, self.text))
