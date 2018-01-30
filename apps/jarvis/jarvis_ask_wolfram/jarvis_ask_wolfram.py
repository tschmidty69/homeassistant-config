import appdaemon.plugins.hass.hassapi as hass
import ast
import sys
import string
import json
import requests
import os, re, time
from fuzzywuzzy import fuzz, process
import wolframalpha


##########################
# Jarvis ask_wolfram Skill
##########################

class jarvis_ask_wolfram(hass.Hass):

    def initialize(self):
        if not self.args.get('enabled'):
            return
        self.jarvis = self.get_app('jarvis_core')
        self.jarvis.jarvis_register_intent('ask_wolfram',
                                      self.jarvis_ask_wolfram)
        self.client = wolframalpha.Client(self.args.get('api_key'))

    def jarvis_ask_wolfram(self, data):
        self.log("__function__: Here is your ask_wolfram: %s" % data)
        res = self.client.query(data.get('input'))
        for pod in res.pods:
            self.log("__function__: pod: %s" % pod)
            if pod.subpods:
                self.log("__function__: subpod: %s" %
                         list(pod.subpods)[0].get('plaintext'))
                break
