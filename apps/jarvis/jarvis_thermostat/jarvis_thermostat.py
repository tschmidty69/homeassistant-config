import appdaemon.plugins.hass.hassapi as hass
import ast
import sys
import random
import string
import json
import yaml
import requests
from pathlib import Path
import os, re, time
from fuzzywuzzy import fuzz, process

#########################
# Jarvis thermostat Skill
#########################

class jarvis_thermostat(hass.Hass):

    def initialize(self):
        if not self.args.get('enabled'):
            return
        self.jarvis = self.get_app('jarvis_core')
        self.thermostat = self.args.get('thermostat')
        self.jarvis.jarvis_register_intent('setThermostat',
                                      self.jarvis_set_thermostat)

    def jarvis_set_thermostat(self, data, *args, **kwargs):
        self.log("__function__: {}".format(data), "INFO")
        if data.get('payload'):
            data = json.loads(data.get('payload', data))
        #self.log("jarvis_thermostat: intent {}".format(data['intent']), "INFO")
        #self.log("jarvis_thermostat: slots {}".format(data['slots']), "INFO")
        if not self.thermostat:
            self.log("__function__: No thermostats configured!", "INFO")

        if not data.get('slots'):
            self.log("jarvis_thermostat: no slot information")
            return

        slots = {}
        for slot in data['slots']:
            slots[slot['slotName']] = slot['value']['value']

        self.log("jarvis_thermostat: {}".format(slots), "INFO")
        if slots.get('zone') == 'upstairs':
            thermostat = 'upstairs'
        else:
            thermostat = 'downstairs'

        if not slots.get('temperature') and not slots.get('direction'):
            self.jarvis.jarvis_notify(None, {'siteId': data.get(
                'siteId', 'default'),
                'text': self.jarvis.jarvis_get_speech(
                'not_understood')})
            return
        if slots.get('direction'):
            if slots.get('temperature'):
                if not 1 <= int(slots['temperature']) < 10:
                    self.jarvis.jarvis_notify(
                        {'siteId': data.get('siteId', 'default'),
                         'text': self.jarvis.jarvis_get_speech('sorry') + ', '
                         + self.jarvis.jarvis_get_speech(
                         'too_much_change').format(slots['temperature'])})
                    return
                else:
                    temperature = int(slots['temperature'])
            elif slots.get('direction') == 'up':
                temperature = 2
            else:
                temperature = -2
            cur_temp = self.get_state(
                entity='climate.'+self.thermostat['heat'][thermostat],
                attribute='temperature')
            target_temp = int(cur_temp) + int(temperature)
        elif slots.get('temperature'):
            if not 60 <= int(slots['temperature']) < 91:
                self.jarvis.jarvis_notify({'siteId':
                    data.get('siteId', 'default'),
                    'text': self.jarvis.jarvis_get_speech('sorry') + ', '
                    + self.jarvis.jarvis_get_speech(
                    'cant_set_temperature').format(slots['temperature'])})
                return
            else:
                target_temp = int(slots['temperature'])
        if target_temp:
            self.log("jarvis_thermostat: target_temp {}".format(target_temp),
                     "INFO")
            if slots.get('mode') == 'cool':
                mode = 'cool'
            else:
                mode = 'heat'
            self.call_service('climate/set_temperature',
                              entity_id='climate.'
                                        + self.thermostat[mode][thermostat],
                              temperature=target_temp)
            self.jarvis.jarvis_notify({'siteId':
                  data.get('siteId', 'default'),
                  'text': self.jarvis.jarvis_get_speech('ok') + ', '
                  + self.jarvis.jarvis_get_speech('set_temperature').format(
                    thermostat, mode, target_temp)})
        else:
            self.jarvis.jarvis_notify({'siteId':
                data.get('siteId', 'default'),
                + 'text': self.jarvis.jarvis_get_speech('not_understood')})
