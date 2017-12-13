#!/usr/bin/python

import sys
import argparse
import subprocess
from requests import post
import logging
import string


parser = argparse.ArgumentParser()

group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-t", "--text", help="text")

parser.add_argument("-v", "--verbose", help="verbose output, can be specified multiple times", action="count")

args = parser.parse_args()

HA_BASE="/home/homeassistant/.homeassistant/"
LOG_FILE=HA_BASE+os.path.basename(sys.argv[0]).replace('.py','')+".log"
HA_SENSOR="sensor."+os.path.basename(sys.argv[0]).replace('.py','')

REST_URL=subprocess.check_output(["grep", "http_base_url", HA_BASE+"secrets.yaml"]).rsplit()[1]
REST_PASSWORD=subprocess.check_output(["grep", "http_password", HA_BASE+"secrets.yaml"]).rsplit()[1]

logging.basicConfig(level=logging.DEBUG, filename=LOG_FILE, filemode="a+",
                        format="%(asctime)-15s %(levelname)-8s %(message)s")

def log(*msg):
  logging.info(" ".join(msg))
  print " ".join(msg);  

if args:
  url = 'https://'+REST_URL+'/api/states/' + HA_SENSOR
  headers = {'x-ha-access': REST_PASSWORD,
             'content-type': 'application/json'}

  # set a default value so we dont get unknown
  data = '{"state": "00:00"}'

  if args.verbose > 1:
    log( "Url: "+url )
    log( "headers: "+headers )
    log( "data: "+data )

  response = post(url, headers=headers, data=data)
  log(response.text)

  
