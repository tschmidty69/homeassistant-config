#!/usr/bin/python

import sys
import argparse
import subprocess
#import random
#from requests import post
import logging
#from subprocess import Popen, PIPE, STDOUT
import string

parser = argparse.ArgumentParser()

group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-t", "--text", help="text to send to snips")

parser.add_argument("-v", "--verbose", help="verbose output, can be specified multiple times", action="count")

args = parser.parse_args()

MOSQUITTO_PUB_BINARY="/usr/bin/mosquitto_pub"
HA_BASE="/home/homeassistant/.homeassistant/"

SNIPS_MQTT=subprocess.check_output(["grep", "snips_mqtt", HA_BASE+"secrets.yaml"]).rsplit()[1]

logging.basicConfig(level=logging.DEBUG, filename=HA_BASE+"snips_query.log", filemode="a+",
                        format="%(asctime)-15s %(levelname)-8s %(message)s")

def log(*msg):
  logging.info(' '.join(msg))
  print ' '.join(msg);  

log( "text:", args.text)

input_text="{\"input\": \"" + args.text + "\", \"id\": \"123456\"}"

if args.verbose:
  log( "MOSQUITTO_PUB_BINARY", MOSQUITTO_PUB_BINARY)
  log( "SNIPS_MQTT:", SNIPS_MQTT)
  log( "input_text:", input_text)
  log(MOSQUITTO_PUB_BINARY, "-h", SNIPS_MQTT, "-t", "hermes/nlu/query", "-m", input_text)

subprocess.check_output([MOSQUITTO_PUB_BINARY, "-h", SNIPS_MQTT, "-t", "hermes/nlu/query", "-m", input_text])

#log( "output:", output)
