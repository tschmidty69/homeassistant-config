import appdaemon.plugins.hass.hassapi as hass
import ast
import sys
import string
import json
import requests
import os, re, time
from fuzzywuzzy import fuzz, process
import paho.mqtt.publish as publish


###########################
# Jarvis Good Morning Skill
###########################

class jarvis_good_morning(hass.Hass):

    def initialize(self):
        if not self.args.get('enabled'):
            return
        self.jarvis = self.get_app('jarvis_core')
        self.jarvis.jarvis_register_intent('goodMorning', self.jarvis_good_morning)

    def jarvis_good_morning(self, data):
        self.log("__function__: %s" % data)
        """Custom handler for morning greeting."""
        self.log("__function__: %s" % data, "INFO")
        if data.get('payload'):
            data = json.loads(data.get('payload', data))

        payload = {'siteId': data.get('siteId', 'default'),
                   'sessionId': data.get('sessionId', 'default'),
                   'input': 'Good Morning',
                   'intent': {'intentName': 'searchWeatherForecast',
                              'probability': 1},
                   'slots': []}
        publish.single('hermes/intent/searchWeatherForecast',
                       payload=json.dumps(payload),
                       hostname=self.jarvis.snips_mqtt_host,
                       port=self.jarvis.snips_mqtt_port,
        )
