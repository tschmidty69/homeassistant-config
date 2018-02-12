import appdaemon.plugins.hass.hassapi as hass
import ast
import sys
import string
import json
import requests
import os, re, time
from fuzzywuzzy import fuzz, process
import wolframalpha
import urllib


##########################
# Jarvis Google Skill
##########################

class jarvis_google(hass.Hass):

    def initialize(self):
        if not self.args.get('enabled'):
            return
        self.jarvis = self.get_app('jarvis_core')
        self.jarvis.jarvis_register_intent('ask_wolfram',
                                      self.jarvis_ask_wolfram)
        self.api_key = 'AIzaSyBkNTpqUQ8RN61I-YFF2ZvC82XELLnwAuI'

    def jarvis_ask_wolfram(self, data):
        self.log("__function__: Here is your ask_wolfram: %s" % data)
        query = data.get('input')
        service_url = 'https://kgsearch.googleapis.com/v1/entities:search'
        params = {
            'query': query,
            'limit': 10,
            'indent': True,
            'key': self.api_key,
        }
        url = service_url + '?' + urllib.parse.urlencode(params)
        response = json.loads(urllib.request.urlopen(url).read())
        self.log(response)
        for element in response['itemListElement']:
            self.log(element['result']['name'] + ' (' + str(element['resultScore']) + ')')
