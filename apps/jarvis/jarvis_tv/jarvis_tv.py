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

        self.jarvis.jarvis_register_intent('playTV',
                                      self.jarvis_play_tv)
        self.jarvis.jarvis_register_intent('pressPauseTV',
                                      self.jarvis_pause_tv)
        self.jarvis.jarvis_register_intent('pressPlayTV',
                                      self.jarvis_press_play_tv)
        self.jarvis.jarvis_register_intent('playSelectTV',
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

        if not data.get('slots'):
            self.jarvis.jarvis_end_session(
                {'sessionId': data.get('sessionId', ''),
                 'text': self.jarvis.jarvis_get_speech(
                             'not_understood').format('light')})
        else:
            #self.log("jarvis_tv: {}".format(data.get('slots')), "INFO")
            for slot in data['slots']:
                #self.log("jarvis_tv: {}".format(slot), "INFO")
                if slot.get('slotName') == 'show':
                    #self.log("jarvis_tv: {}".format(self.netflix.keys()),
                    #         "INFO")
                    show = process.extractBests(slot['value']['value'],
                        list(self.shows.keys()), score_cutoff=60)
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
                    if self.tv.get(zone):
                        tv_state = self.get_state(entity=self.tv[zone]['power_switch'])
                        self.log("__function__: entity: {}: {}".format(
                                self.tv[zone]['power_switch'], tv_state), 'INFO')
                        if tv_state == 'off':
                            self.call_service("switch/turn_on",
                                entity_id = self.tv[zone]['power_switch'])

                    response = requests.post(url)
                    self.log("jarvis_tv: response {}".format(response), "INFO")
                    self.jarvis.jarvis_end_session({'sessionId':
                        data.get('sessionId', ''),
                        'text': self.jarvis.jarvis_get_speech('ok')
                        + ", I put " + self.shows[show[0][0]]['long_title']
                        + " on for you"})

    def jarvis_pause_tv(self, data, *args, **kwargs):
        self.log("__function__: {}".format(data), "INFO")
        self.jarvis.not_implemented(data)

    def jarvis_press_play_tv(self, data, *args, **kwargs):
        self.log("__function__: {}".format(data), "INFO")
        url = ("http://"
               + str(self.tv[zone]['roku'])
               + ":8060/keypress/Play")
        response = requests.post(url)
        self.log("__function__: response {}".format(response), "INFO")

    def jarvis_press_select_tv(self, data, *args, **kwargs):
        self.log("__function__: {}".format(data), "INFO")
        url = ("http://"
               + str(self.tv[zone]['roku'])
               + ":8060/keypress/Select")
        response = requests.post(url)
        self.log("__function__: response {}".format(response), "INFO")

    def jarvis_turn_on_tv(self, data, *args, **kwargs):
        self.jarvis_tv_power(data, 'on')

    def jarvis_turn_off_tv(self, data, *args, **kwargs):
        self.jarvis_tv_power(data, 'off')

    def jarvis_tv_power(self, data, state, *args, **kwargs):
        self.log("__function__: {} {}".format(state, data), "INFO")
        if data.get('payload'):
            data = json.loads(data.get('payload', data))
        zone = data.get('zone', self.args.get('default_tv'))
        if not zone:
            self.jarvis.jarvis_end_session(
                {'sessionId': data.get('sessionId', ''),
                 'text': self.jarvis.jarvis_get_speech(
                             'unknown_entity').format('tv')})

        if self.tv.get(zone):
            tv_state = self.get_state(entity=self.tv[zone]['power_switch'])
            self.log("__function__: entity: {}: {}".format(
                    self.tv[zone]['power_switch'], tv_state), 'INFO')
            if tv_state == state:
                self.jarvis.jarvis_end_session(
                    {'sessionId': data.get('sessionId', ''),
                     'text': self.jarvis.jarvis_get_speech(
                                 'already_state').format(
                                 zone.replace('_', ' '), 'tv', state)})
                return

        response = self.call_service("switch/turn_" + state,
                          entity_id = self.tv[zone]['power_switch'])
        self.jarvis.jarvis_end_session(
            {'sessionId': data.get('sessionId', ''),
             'text': self.jarvis.jarvis_get_speech(
                         'turn_on_or_off').format(
                         zone.replace('_', ' '), 'tv', state)})
