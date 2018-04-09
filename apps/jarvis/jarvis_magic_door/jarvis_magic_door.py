import json
import yaml
import uuid
import requests
import datetime
import os
from urllib.parse import urlparse
import subprocess

import appdaemon.plugins.hass.hassapi as hass

##########################
# Jarvis Magic Door Skill
##########################

class jarvis_magic_door(hass.Hass):

    def initialize(self):
        if not self.args.get('enabled'):
            return
        self.jarvis = self.get_app('jarvis_core')
        with open(os.path.join(os.path.dirname(__file__)) + '/intents.yaml', 'r') as f:
            self.intents = yaml.load(f)
        self.jarvis.jarvis_register_intent('LaunchMagicDoor',
                                           self.start_game)

        for intent in self.intents['intents']:
            self.jarvis.jarvis_register_intent(intent,
                                               self.magic_door_intent)
            # elif 'AMAZON_StopIntent' in intent:
            #     self.jarvis.jarvis_register_intent('AMAZON_StopIntent',
            #                                        self.end_game)
            # elif 'AMAZON_StartOverIntent' in intent:
            #     self.jarvis.jarvis_register_intent('AMAZON_StartOverIntent',
            #                                        self.start_over_game)
            # elif 'AMAZON_YesIntent' in intent:
            #     self.jarvis.jarvis_register_intent('AMAZON_StopIntent',
            #                                        self.yes_intent)
            # elif 'AMAZON_NoIntent' in intent:
            #     self.jarvis.jarvis_register_intent('AMAZON_StopIntent',
            #                                        self.no_intent)
            # else:
            #     self.jarvis.jarvis_register_intent(intent,
            #                                        self.magic_door_intent)
        self.session_id = {}
        self.site_id = 'default'
        self.jarvis.enable_intents(state=True)
        self.md_headers = {'Content-Type': 'application/json',
            'x-api-key': self.args.get('api_key'), 'Accept': '*/*'}

        self.sessionId = ''
        self.game_started = True
        self.global_vars['dialogue_enabled']['remote'] = False
        self.user_id = (self.args.get('user_id') if self.args.get('user_id')
                        else str(uuid.uuid4()))
        self.md_session_id = str(uuid.uuid4())

        self.previous_parameters = {}

    def send_intent(self, intent='', text='', slots={}):
        """Send an intent to the Magic Door endpoint using request.json
           as a template."""
        self.log("__function__: %s %s %s %s" % (intent, text, slots, self.md_headers))
        request_json = dict(json.load(open(os.path.join(os.path.dirname(__file__)) + '/request.json', 'r')))
        request_json['originalRequest']['data']['user']['user_id'] = self.user_id
        request_json['originalRequest']['data']['inputs'][0]['arguments'][0]['raw_text'] = text
        request_json['originalRequest']['data']['inputs'][0]['arguments'][0]['text_value'] = text
        request_json['originalRequest']['data']['inputs'][0]['raw_inputs'][0]['query'] = text
        request_json['result']['resolved_query'] = text
        request_json['originalRequest']['data']['inputs'][0]['intent'] = intent
        request_json['result']['metadata']['intentName'] = intent
        request_json['timestamp'] = datetime.datetime.now().isoformat()
        request_json['result']['parameters'] = slots
        request_json['sessionId'] = self.md_session_id
        # Dump as this_requests.json for debugging
        with open(os.path.join(os.path.dirname(__file__)) + '/this_request.json', 'w') as f:
            f.write(json.dumps(request_json))

        md_response = requests.post('https://magicdoor.todschmidt.com/prod',
                             headers=self.md_headers,
                             data=json.dumps(request_json))
        self.log("__function__: md_response {}".format(md_response.json()))
        return md_response.json()

    def start_game(self, data=None, *args, **kwargs):
        """Generate a new user_id and start the game. Session handling per user
           is handled my the Magic Door endpoint."""
        self.log("__function__: %s" % data)
        # if self.game_started == True:
        #     self.log("__function__: Already running the game!")
        #     # TODO: This should prompt for a startover
        #     return
        self.game_started = True
        self.site_id = data.get('siteId', 'default')
        self.sessionId =  data.get('sessionId', '')
        self.global_vars['dialogue_enabled'][self.site_id] = True

        response = self.send_intent(intent='SPECIAL_LAUNCH_ACTION', text='', slots=[])
        self.previous_parameters = response.get('parameters', {})
        self.log("__function__: response %s" % response)
        http_audio_url = response.get('speech')
        if http_audio_url:
            http_audio_url = http_audio_url.replace('<speak><audio src="', '')
            http_audio_url = http_audio_url.replace('"/></speak>', '')
            http_audio_url = http_audio_url.replace('speak', 'spoke')

            self.log("__function__: http_audio_url %s" % http_audio_url)
            self.jarvis.jarvis_end_session(
                {'siteId': self.site_id,
                 'sessionId': self.sessionId,
                 'text': ''})
            self.jarvis.jarvis_play_http_audio(
                {'siteId': self.site_id,
                 'sessionId': self.sessionId,
                 'url': http_audio_url}, callback=self.magic_door_listener_callback)
        else:
            self.log("__function__: http_audio_url not defined")

    def end_game(self, data=None, *args, **kwargs):
        self.log("__function__: %s" % data)
        # TODO: Prompt for end?
        self.game_started == False
        self.global_vars['dialogue_enabled'][self.site_id] = False
        self.jarvis.register_dialogue_listener_callback(data.get('siteId', self.siteId), None)
        # TODO: This should prompt for a startover
        return

    def start_over_game(self, data=None, *args, **kwargs):
        self.log("__function__: %s" % data)
        # TODO: Prompt for end?
        self.game_started == False
        self.global_vars['dialogue_enabled'][self.site_id] = False
        # TODO: This should prompt for a startover
        return

    def yes_intent(self, data=None, *args, **kwargs):
        self.log("__function__: %s" % data)
        return

    def no_intent(self, data=None, *args, **kwargs):
        self.log("__function__: %s" % data)
        return

    def magic_door_intent(self, data=None, *args, **kwargs):
        """Handle all Magic Door intents."""
        self.log("__function__: %s" % data)
        if self.game_started == False:
            self.log("__function__: No game started!")
            return
        self.site_id = data.get('siteId', 'default')
        intent = data['intent']['intentName'].split(':')[-1]
        if intent.startswith('AMAZON_'):
            intent = intent.replace('AMAZON_', 'AMAZON.')
        slots = {}
        for slot in data.get('slots'):
            slots[slot['slotName']] = slot['value']['value']
        if self.previous_parameters.get('previousIntent'):
            slots.update(self.previous_parameters)
        #self.log("__function__: previous: %s" % self.previous_parameters)
        self.log("__function__: slots: %s" % slots)
        response = self.send_intent(intent=intent,
            text=data.get('input'), slots=slots)
        self.log("__function__: response %s" % response)
        self.previous_parameters = response.get('contextOut')[0].get('parameters')
        http_audio_url = response.get('speech')
        if http_audio_url:
            http_audio_url = http_audio_url.replace('<speak><audio src="', '')
            http_audio_url = http_audio_url.replace('"/></speak>', '')

            self.log("__function__: http_audio_url %s" % http_audio_url)
            self.jarvis.jarvis_play_http_audio(
                {'siteId': self.site_id,
                 'sessionId': self.sessionId,
                 'url': http_audio_url},
                 callback=self.magic_door_listener_callback)

    def magic_door_listener_callback(self, data, *args, **kwargs):
        """Called when a playFinished event comes from Snips."""
        self.log("__function__:  data %s" % data)
        self.jarvis.jarvis_action(
            {'siteId': self.site_id,
             'sessionId': self.sessionId,
             'text': '',
             'intentFilter': ''})
