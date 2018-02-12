import appdaemon.plugins.hass.hassapi as hass
import sys
import string
import json
from fuzzywuzzy import fuzz, process

#####################
# Jarvis Lights Skill
#####################

class jarvis_lights(hass.Hass):

    def initialize(self):
        if not self.args.get('enabled'):
            return
        self.jarvis = self.get_app('jarvis_core')

        self.lights = self.args.get('lights')

        self.jarvis.jarvis_register_intent('lightsTurnOnSet',
                                      self.jarvis_lights_on)
        self.jarvis.jarvis_register_intent('lightsTurnOff',
                                      self.jarvis_lights_off)
        self.jarvis.jarvis_register_intent('lightsTurnUp',
                                      self.jarvis_lights_up)
        self.jarvis.jarvis_register_intent('lightsTurnDown',
                                      self.jarvis_lights_down)

    def jarvis_lights_on(self, data):
        self.log("__function__: {}".format(data), 'DEBUG')
        self.jarvis_lights_state(data, state='on')

    def jarvis_lights_off(self, data):
        self.log("__function__: {}".format(data), 'DEBUG')
        self.jarvis_lights_state(data, state='off')

    def jarvis_lights_up(self, data):
        self.log("__function__: {}".format(data), 'DEBUG')
        self.jarvis_lights_state(data, state='up')

    def jarvis_lights_down(self, data):
        self.log("__function__: {}".format(data), 'DEBUG')
        self.jarvis_lights_state(data, state='down')

    def jarvis_lights_state(self, data, state):
        self.log("__function__: {}".format(data), 'INFO')
        if data.get('payload'):
            data = json.loads(data.get('payload'))

        self.log("__function__: slots: {}".format(data['slots']), 'DEBUG')

        for slot in data.get('slots'):
            zone = (slot['value'].get('value', '')
                    if 'zone' in slot['slotName'] else None)
            unit = (slot['value'].get('value')
                    if 'unit' in slot['slotName'] else None)
            number = (slot['value'].get('value')
                      if 'number' in slot['slotName'] else None)

        if not zone:
            self.jarvis.jarvis_end_session(
                {'sessionId': data.get('sessionId', ''),
                 'text': self.jarvis.jarvis_get_speech(
                             'unknown_entity').format('light')})

        if self.lights.get(zone):
            self.log("__function__: entity: {}: {}".format(
                    self.lights.get(zone), state), 'INFO')
            if self.get_state(entity=self.lights.get(zone)) == state:
                self.jarvis.jarvis_end_session(
                    {'sessionId': data.get('sessionId', ''),
                     'text': self.jarvis.jarvis_get_speech(
                                 'already_state').format(
                                 zone.replace('_', ' '), 'light', state)})
                return

            response = self.call_service("switch/turn_" + state,
                              entity_id = self.lights.get(zone))
            self.jarvis.jarvis_end_session(
                {'sessionId': data.get('sessionId', ''),
                 'text': self.jarvis.jarvis_get_speech(
                             'turn_on_or_off').format(
                             zone.replace('_', ' '), 'light', state)})
        else:
            self.jarvis.jarvis_end_session(
                {'sessionId': data.get('sessionId', ''),
                 'text': self.jarvis.jarvis_get_speech(
                    'not_found').format(zone.replace('_', ' '),
                                               'light')})
