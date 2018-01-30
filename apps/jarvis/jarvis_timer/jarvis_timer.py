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

####################
# Jarvis timer Skill
####################

class jarvis_timer(hass.Hass):

    def initialize(self):
        if not self.args.get('enabled'):
            return
        self.jarvis = self.get_app('jarvis_core')
        self.jarvis.jarvis_register_intent('setTimer',
                                      self.jarvis_set_timer)
        self.jarvis.jarvis_register_intent('stopTimer',
                                      self.jarvis_set_timer)

    def jarvis_set_timer(self, data, *args, **kwargs):
        self.log("jarvis_set_timer: {}".format(data), "INFO")
        duration = int(data['hours'])*360
        duration += int(data['minutes'])*60
        duration += int(data['seconds'])

        #self.log("duration: {}".format(duration), "INFO")
        self.handle = self.run_in(
            self.jarvis_timer_done,
            duration,
            timer_name=data['name']
        )
        text = self.jarvis_speech('ok') + ", setting a timer of "

        if int(data['hours']) > 0:
            if int(data['hours']) > 1:
                text += data['hours']+" hours "
            else:
                text += " 1 hour "
            if int(data['minutes']) > 0:
                text += " and "
        if int(data['minutes']) > 0:
            if int(data['minutes']) > 1:
                text += data['minutes']+" minutes "
            else:
                text += " 1 minute "
            if int(data['seconds']) > 0:
                text += " and "
        if int(data['seconds']) > 0:
            if int(data['seconds']) > 1:
                text += data['seconds']+" seconds "
            else:
                text += " 1 second "
        text += 'for '
        text += data['name']
        #self.log("jarvis_set_timer: text: {}".format(text), "INFO")

        self.jarvis_notify('NONE', {'text': text})

    def jarvis_cancel_timer(self, data, kwargs):
        self.log("jarvis_cancel_timer: {}".format(data), "INFO")
        try:
          self.cancel_timer(self.handle)
          speech={"text": self.jarvis_speech('ok') + ", canceling your timer"}
          self.jarvis_notify('NONE', speech)
        except:
          speech={"text": self.jarvis_speech('sorry')
                  + ", I couldn't find that timer"}
          self.jarvis_notify('NONE', speech)
