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
# Jarvis Dialogue Skill
##########################

class jarvis_dialogue(hass.Hass):

    def initialize(self):
        if not self.args.get('enabled'):
            return
        self.jarvis = self.get_app('jarvis_core')
        self.jarvis.jarvis_register_intent('start_dialogue',
                                           self.start_dialogue)
        self.session_id = {}
        #TODO Change this to a dict for multiple dialogues
        self.site_id = 'default'
        self.dialogue_callback = None
        self.dialogue_listener_callback = None
        self.jarvis.enable_intents(state=True)
        self.global_vars['dialogue_enabled'][self.site_id] = False
        self.cancel_dialogue = []

    def dialogue_say(self, data):
        payload = {'siteId': data.get('siteId', 'default')}
        publish.single('hermes/asr/toggleOff',
                       payload=json.dumps(payload),
                       hostname=self.jarvis.snips_mqtt_host,
                       port=self.jarvis.snips_mqtt_port)
        payload = {'siteId': data.get('siteId', 'default'),
                   'sessionId': self.session_id[self.site_id]}
        publish.single('hermes/asr/stopListening',
                       payload=json.dumps(payload),
                       hostname=self.jarvis.snips_mqtt_host,
                       port=self.jarvis.snips_mqtt_port)
        publish.single('hermes/tts/say',
                       payload=json.dumps(data),
                       hostname=self.jarvis.snips_mqtt_host,
                       port=self.jarvis.snips_mqtt_port)

    def start_dialogue(self, data=None, start_text=None, *args, **kwargs):
        self.log("__function__: %s" % data)

        if self.global_vars['dialogue_enabled'].get('self.site_id') == True:
            self.log("__function__: Already running a dialogue!")

        self.jarvis.enable_intents(state=False)
        self.site_id = data.get('siteId', 'default')
        self.session_id[self.site_id] = str(uuid.uuid1())

        self.dialogue_callback = (kwargs.get('dialogue_callback')
                if kwargs.get('dialogue_callback')
                else self.dialogue_cb)
        self.jarvis.register_dialogue_callback(
                            self.site_id, self.dialogue_callback)
        # This should usually not need to be redefined but wth
        self.dialogue_listener_callback = (kwargs.get('dialogue_listener_callback')
                if kwargs.get('dialogue_listener_callback')
                else self.dialogue_listener_cb)
        self.jarvis.register_dialogue_listener_callback(
                            self.site_id, self.dialogue_listener_callback)

        payload = {'siteId': data.get('siteId', 'default')}
        self.global_vars['dialogue_enabled'][self.site_id] = True
        publish.single('hermes/dialogueManager/stop',
                       payload=json.dumps(payload),
                       hostname=self.jarvis.snips_mqtt_host,
                       port=self.jarvis.snips_mqtt_port)

        text = start_text if start_text else 'I am listening'
        self.dialogue_say({'siteId': self.site_id,
                           'text': text})
        self.jarvis.jarvis_end_session(
            {'sessionId': data.get('sessionId', '')})

    def dialogue_listener_reset(self, **kwargs):
        self.log("__function__: %s" % data)

        payload = {'siteId': data.get('siteId', 'default')}
        publish.single('hermes/asr/toggleOff',
                       payload=json.dumps(payload),
                       hostname=self.jarvis.snips_mqtt_host,
                       port=self.jarvis.snips_mqtt_port)
        payload = {'siteId': data.get('siteId', 'default'),
                   'sessionId': self.session_id[self.site_id]}
        publish.single('hermes/asr/stopListening',
                       payload=json.dumps(payload),
                       hostname=self.jarvis.snips_mqtt_host,
                       port=self.jarvis.snips_mqtt_port)


    def dialogue_listener_cb(self, data, *args, **kwargs):
        self.log("__function__: %s" % data)

        payload = {'siteId': data.get('siteId', 'default')}
        publish.single('hermes/hotword/toggleOff',
                       payload=json.dumps(payload),
                       hostname=self.jarvis.snips_mqtt_host,
                       port=self.jarvis.snips_mqtt_port)
        publish.single('hermes/asr/toggleOn',
                       payload=json.dumps(payload),
                       hostname=self.jarvis.snips_mqtt_host,
                       port=self.jarvis.snips_mqtt_port)
        payload = {'siteId': data.get('siteId', 'default'),
                   'sessionId': self.session_id[self.site_id]}
        publish.single('hermes/asr/startListening',
                       payload=json.dumps(payload),
                       hostname=self.jarvis.snips_mqtt_host,
                       port=self.jarvis.snips_mqtt_port)


    def dialogue_cb(self, data, *args, **kwargs):
        self.log("__function__:  data %s" % data)
        self.cancel_listen_event(self.cancel_dialogue)
        if 'bye' in data.get('text'):
            self.end_dialogue('EVENT', data)
            return
        self.dialogue_say({'siteId': self.site_id,
                           'text': '{}, Interesting'.format(data.get('text', ''))})

    def end_dialogue(self, data, *args, **kwargs):
        self.log("__function__: %s" % data)
        self.jarvis.enable_intents(state=True)
        self.global_vars['dialogue_enabled'][self.site_id] = False
        self.cancel_listen_event(self.cancel_dialogue)
        if data.get('data'):
            data = json.loads(data.get('data'))
        self.site_id = data.get('siteId', 'default')
        self.session_id[self.site_id] = uuid.uuid1()
        payload = {'siteId': data.get('siteId', 'default')}
        publish.single('hermes/dialogueManager/start',
                       payload=json.dumps(payload),
                       hostname=self.jarvis.snips_mqtt_host,
                       port=self.jarvis.snips_mqtt_port)
        publish.single('hermes/asr/stopListening',
                       payload=json.dumps(payload),
                       hostname=self.jarvis.snips_mqtt_host,
                       port=self.jarvis.snips_mqtt_port)
        publish.single('hermes/asr/toggleOff',
                       payload=json.dumps(payload),
                       hostname=self.jarvis.snips_mqtt_host,
                       port=self.jarvis.snips_mqtt_port)
        publish.single('hermes/hotword/toggleOn',
                       payload=json.dumps(payload),
                       hostname=self.jarvis.snips_mqtt_host,
                       port=self.jarvis.snips_mqtt_port)
        payload = {'siteId': data.get('siteId', 'default'),
                   'sessionId': self.session_id[self.site_id]}
        #TODO add end text
        self.dialogue_say({'siteId': self.site_id,
                           'text': 'Goodbye'})
        self.global_vars['dialogue_enabled'][self.site_id] = False
        self.jarvis.register_dialogue_callback(self.site_id, None)
        self.jarvis.register_dialogue_listener_callback(self.site_id, None)
