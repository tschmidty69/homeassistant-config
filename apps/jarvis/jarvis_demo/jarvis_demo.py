import appdaemon.plugins.hass.hassapi as hass
import ast
import sys
import string
import json
import requests
import os, re, time
import urllib


##########################
# Jarvis Demo Skill
##########################

class jarvis_demo(hass.Hass):

    def initialize(self):
        if not self.args.get('enabled'):
            return
        self.jarvis = self.get_app('jarvis_core')
        self.jarvis.jarvis_register_intent('demo_intent',
                                      self.demo_intent)

    def jarvis_demo(self, data):
        self.log("__function__: demo_intent: %s" % data)
