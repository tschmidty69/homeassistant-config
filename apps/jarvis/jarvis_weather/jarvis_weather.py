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
        if not self.args.get('enabled'):
            return
        jarvis = self.get_app('jarvis_core')
        jarvis.jarvis_register_intent('searchWeatherForecast',
                                      self.jarvis_weather)
        jarvis.jarvis_register_intent('searchWeatherForecastCondition',
                                      self.jarvis_weather_condition)
        jarvis.jarvis_register_intent('searchWeatherItem',
                                      self.jarvis_weather_item)
        jarvis.jarvis_register_intent('searchWeatherForecastTemperature',
                                      self.jarvis_weather_temperature)

    def jarvis_weather(self, data):
        self.log("__function__: Here is your weather: %s" % data)

    def jarvis_weather_condition(self, data):
        self.log("__function__: Here is your weather: %s" % data)

    def jarvis_weather_item(self, data):
        self.log("__function__: Here is your weather: %s" % data)

    def jarvis_weather_temperature(self, data):
        self.log("__function__: Here is your weather: %s" % data)
