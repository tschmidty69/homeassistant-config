import appdaemon.plugins.mqtt.mqttapi as mqtt
import ast
import sys
import string
import json
import requests
import os, re, time
from fuzzywuzzy import fuzz, process


class mqtt_demo(mqtt.Mqtt):

    def initialize(self):
        self.log("__function__: I'm alive")
        self.listen_event(self.mqtt_message,
                          'MQTT_MESSAGE')

    def mqtt_message(self, data):
        self.log("__function__: %s" % data)
