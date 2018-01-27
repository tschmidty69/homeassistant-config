import appdaemon.plugins.hass.hassapi as hass
import sys
import string
import json
from fuzzywuzzy import fuzz, process

######################
# Jarvis Weather Skill
######################

class jarvis_lights(hass.Hass):

    def initialize(self):
        jarvis = self.get_app("jarvis_core")

        self.lights = []
        for light in self.args.get('lights'):
            self.lights.append(light)

        jarvis.jarvis_register_intent('turnLightOnSet',
                                    self.jarvis_lights)
        jarvis.jarvis_register_intent('turnLightOff',
                                    self.jarvis_lights)

    def jarvis_lights(self, data, *args, **kwargs):
        self.log("__function__: {}".format(data), "INFO")
        if data.get('payload'):
            data = json.loads(data.get('payload'))

        on_off = on

        self.log("__function__: {}".format(data['slots']), "INFO")
        try:
            zone = data['slots'][0]['value'].get('value', '')
        except:
            zone = "unknown"

        try:
            self.call_service("switch/turn_"+on_off,
                              entity_id = self.lights[zone])
            jarvis_core.jarvis_end_session(
                {'sessionId': data.get('sessionId', ''),
                 'text': jarvis_core.jarvis_get_speech('lights').format(
                    zone.sub('_', ' '), on_off)})
        except:
            jarvis_core.jarvis_end_session(
                {'sessionId': data.get('sessionId', ''),
                 'text': jarvis_core.jarvis_get_speech(
                    'not_found_lights').format(zone.sub('_', ' '))})
