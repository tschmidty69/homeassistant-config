import appdaemon.plugins.hass.hassapi as hass
import ast
import sys
import random
import string
import json
import yaml
from pathlib import Path
import os, re, time
from fuzzywuzzy import fuzz, process

#################
# Jarvis TV Skill
#################

class jarvis_tv(hass.Hass):

    def initialize(self):
        if not self.args.get('enabled'):
            return
        self.jarvis = self.get_app("jarvis_core")
        self.tv = self.args.get('tv')
        self.tv_file = os.path.join(os.path.dirname(__file__)
                                        + self.args.get('tv_file'))
        with open(self.tv_file, "r") as f:
            self.shows = yaml.load(f)

        self.jarvis.jarvis_register_intent('playTv',
                                      self.jarvis_play_tv)
        self.jarvis.jarvis_register_intent('pressPauseTv',
                                      self.jarvis_pause_tv)
        self.jarvis.jarvis_register_intent('pressPlayTv',
                                      self.jarvis_press_play_tv)
        self.jarvis.jarvis_register_intent('playSelectTv',
                                      self.jarvis_press_select_tv)
        self.jarvis.jarvis_register_intent('turnTVOn',
                                      self.jarvis_turn_on_tv)
        self.jarvis.jarvis_register_intent('turnTVOff',
                                      self.jarvis_turn_off_tv)

    def jarvis_play_tv(self, data, *args, **kwargs):
        self.log("__function__: {}".format(data), "INFO")
        if not self.tv:
            #TODO
            return
        if data.get('payload'):
            data = json.loads(data.get('payload', data))
        zone = data.get('zone', 'living_room')
        channel = '12' # Netflix
        if data.get('channel'):
            if data['channel'] == 'amazon':
                channel = '13'

        if data.get('slots'):
            #self.log("jarvis_tv: {}".format(data.get('slots')), "INFO")
            for slot in data['slots']:
                #self.log("jarvis_tv: {}".format(slot), "INFO")
                if slot.get('slotName') == 'show':
                    #self.log("jarvis_tv: {}".format(self.netflix.keys()),
                    #         "INFO")
                    show = process.extractBests(slot['value']['value'],
                        list(self.tv.keys()), score_cutoff=60)
                    self.log("jarvis_tv: shows {}".format(show), "INFO")
                    self.log("jarvis_tv: best_match {}".format(
                        self.shows[show[0][0]]), "INFO")

                    url = ("http://"
                          + str(self.tv[zone]['roku'])
                          + ":8060/launch/"
                          + str(self.shows[show[0][0]]['channel'])
                          + "?ContentID="
                          + str(self.shows[show[0][0]]['seasons'][1])
                          + "&MediaType=series")
                    self.log("jarvis_tv: url {}".format(url), "INFO")

                    response = requests.post(url)
                    self.log("jarvis_tv: response {}".format(response), "INFO")
                    if str(self.shows[show[0][0]]['channel']) == '13':
                        time.sleep(3)
                        url = ("http://"
                               + str(self.roku[zone])
                               + ":8060/keypress/Select")
                        response = requests.post(url)
                        self.log("jarvis_tv: response {}".format(response), "INFO")
                        self.jarvis_notify(None, {'siteId':
                            data.get('siteId', 'default'),
                            'text': self.jarvis_speech('ok')
                            + ", I put " + self.shows[show[0][0]]['long_title']
                            + " on for you"})

    def jarvis_pause_tv(self, data, *args, **kwargs):
        self.log("__function__: {}".format(data), "INFO")
        self.jarvis.not_implemented()

    def jarvis_press_play_tv(self, data, *args, **kwargs):
        self.log("__function__: {}".format(data), "INFO")
        self.jarvis.not_implemented()

    def jarvis_press_select_tv(self, data, *args, **kwargs):
        self.log("__function__: {}".format(data), "INFO")
        self.jarvis.not_implemented()

    def jarvis_turn_on_tv(self, data, *args, **kwargs):
        jarvis_tv_power(data, 'on')

    def jarvis_turn_of_tv(self, data, *args, **kwargs):
        jarvis_tv_power(data, 'off')

    def jarvis_tv_power(self, data, state, *args, **kwargs):
        self.log("__function__: {} {}".format(state, data), "INFO")
        if data.get('payload'):
            data = json.loads(data.get('payload', data))
        zone = data.get('zone', self.args.get('default_tv'))
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
                          entity_id = self.tv[zone]['power_switch'])
        self.jarvis.jarvis_end_session(
            {'sessionId': data.get('sessionId', ''),
             'text': self.jarvis.jarvis_get_speech(
                         'turn_on_or_off').format(
                         zone.replace('_', ' '), 'tv', state)})
