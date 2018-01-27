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

######################
# Jarvis Weather Skill
######################

class jarvis_weather(hass.Hass):

    def initialize(self):
        jarvis = self.get_app("jarvis_core")
        jarvis.jarvis_register_intent('searchWeatherForecast',
                                    self.jarvis_weather)

    def jarvis_weather(self, data):
        self.log("__function__: Here is your weather: %s" % data)
