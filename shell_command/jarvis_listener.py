#!/srv/homeassistant/bin//python

import sys
import argparse
import subprocess
import random
from requests import post
import logging
import string
#from fuzzywuzzy import fuzz
#from fuzzywuzzy import process
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import json
import boto3
from pathlib import Path
import os
import re

parser = argparse.ArgumentParser()

parser.add_argument("-m", "--host", help="host to connect to", default='127.0.0.1')
parser.add_argument("-p", "--port", help="port to connect to", default=1883)
parser.add_argument("-v", "--verbose", help="verbose output, can be specified multiple times", action="count", default = 0)

args = parser.parse_args()

HA_BASE="/home/homeassistant/.homeassistant/"
LOG_FILE=HA_BASE+os.path.basename(sys.argv[0]).replace('.py','')+".log"
# default sensor
HA_SENSOR="sensor."+os.path.basename(sys.argv[0]).replace('.py','')

REST_URL=str(subprocess.check_output(["grep", "http_base_url", HA_BASE+"secrets.yaml"]).rsplit()[1].decode())
REST_PASSWORD=str(subprocess.check_output(["grep", "http_password", HA_BASE+"secrets.yaml"]).rsplit()[1].decode())

logging.basicConfig(level=logging.DEBUG, filename=LOG_FILE, filemode="a+",
                        format="%(asctime)-15s %(levelname)-8s %(message)s")

NAMES = [('hour', 'hours'),
         ('minute', 'minutes'),
         ('second', 'seconds')]

def log(msg):
  logging.info(msg)
  print(msg);

def on_connect(client, userdata, flags, rc):
  print("Connected with result code "+str(rc))

  # Subscribing in on_connect() means that if we lose the connection and
  # reconnect then subscriptions will be renewed.
  client.subscribe("hermes/tts/say")
  client.subscribe("hermes/audioServer/default/playFinished")
  client.subscribe("jarvis/timer_duration")

def sensor_state(sensor, data):
  url = REST_URL+"/api/states/"+sensor
  headers = {"x-ha-access": REST_PASSWORD,
             "content-type": "application/json"}

  if args.verbose > 1:
    log("Url: "+url )
    log("headers: "+str(headers) )
    log("data: "+data )

  response = post(url, headers=headers, data=data)
  log(response.text)


Small = {
    'zero': 0,
    'one': 1,
    'two': 2,
    'three': 3,
    'four': 4,
    'five': 5,
    'six': 6,
    'seven': 7,
    'eight': 8,
    'nine': 9,
    'ten': 10,
    'eleven': 11,
    'twelve': 12,
    'thirteen': 13,
    'fourteen': 14,
    'fifteen': 15,
    'sixteen': 16,
    'seventeen': 17,
    'eighteen': 18,
    'nineteen': 19,
    'twenty': 20,
    'thirty': 30,
    'forty': 40,
    'fifty': 50,
    'sixty': 60,
    'seventy': 70,
    'eighty': 80,
    'ninety': 90
}

Magnitude = {
    'thousand':     1000,
    'million':      1000000,
    'billion':      1000000000,
    'trillion':     1000000000000,
    'quadrillion':  1000000000000000,
    'quintillion':  1000000000000000000,
    'sextillion':   1000000000000000000000,
    'septillion':   1000000000000000000000000,
    'octillion':    1000000000000000000000000000,
    'nonillion':    1000000000000000000000000000000,
    'decillion':    1000000000000000000000000000000000,
}

class NumberException(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)

def text2num(s):
    a = re.split(r"[\s-]+", s)
    n = 0
    g = 0
    for w in a:
        x = Small.get(w, None)
        if x is not None:
            g += x
        elif w == "hundred" and g != 0:
            g *= 100
        else:
            x = Magnitude.get(w, None)
            if x is not None:
                n += g * x
                g = 0
            else:
                raise NumberException("Unknown number: "+w)
    return n + g


############################
# my callbacks

# The callback for when a PUBLISH message is received from the server.
def tts_say(client, userdata, msg):
  log(msg.topic+" "+str(msg.payload.decode()))
  data = json.loads(msg.payload.decode())
  #log(data['text'])

  # Generating audio
  sessionId=''.join(random.choices(string.ascii_uppercase + string.digits, k=16))

  Path("/tmp/sounds/").mkdir(parents=True, exist_ok=True)

  tmp_file = Path("/tmp/sounds/"+data['text']+".wav")
  response = {}
  if not tmp_file.is_file():
    response=aws_client.synthesize_speech( OutputFormat='mp3', Text=data['text'], VoiceId='Geraint' )
    if args.verbose > 0:
      log(response['ContentType']+'\n'+response['RequestCharacters'])
    mp3_file = open("/tmp/sounds/"+data['text']+".mp3", "wb")
    mp3_file.write(response['AudioStream'].read())
    mp3_file.close()
    subprocess.run(['/usr/bin/mpg123','-q','-w','/tmp/sounds/'+data['text']+'.wav', '/tmp/sounds/'+data['text']+'.mp3'])
  wav_file = open("/tmp/sounds/"+data['text']+".wav", "rb")
  audio_wav = wav_file.read()
  wav_file.close()

  publish.single('hermes/audioServer/default/playBytes/'+sessionId+'/',
    payload=audio_wav, qos=0, retain=False, hostname=args.host, port=args.port,
    client_id="", keepalive=60, will=None, auth=None, tls=None, protocol=mqtt.MQTTv311)
  #TODO: listen for callback

  # If we have a sessionId the request came from a snips dialogue so let it know we are done talking
  if 'sessionId' in data:
    publish.single('hermes/tts/sayFinished', payload='{"siteId": "'+data['siteId']+'", "sessionId": "'+data['sessionId']+'", "id": "'+data['id']+'"}',
      qos=0, retain=False, hostname=args.host, port=args.port, client_id="", keepalive=60, will=None, auth=None, tls=None, protocol=mqtt.MQTTv311)

def timer_duration(client, userdata, msg):
  log(msg.topic+" "+str(msg.payload.decode()))
  data = json.loads(msg.payload.decode())
  log("text: "+data['text'])

  # set a default value so we dont get unknown
  state = '{"state": "00:00"}'
  sensor_state("sensor.timer_duration", state)

  seconds=re.match(r'(\w+) second', data['text'])
  minutes=re.match(r'(\w+) minute', data['text'])
  hours=re.match(r'(\w+) hour', data['text'])
  secs=text2num(str(seconds.group(1) if seconds else "zero"))
  mins=text2num(str(minutes.group(1) if minutes else "zero"))
  hrs=text2num(str(hours.group(1) if hours else "zero"))
  duration = "%02d:%02d:%02d" % (hrs, mins, secs)

  log("duration: "+duration)
  sensor_state("sensor.timer_duration", "{\"state\": \""+duration+"\"}")


def playFinished(client, userdata, msg):
  log(msg.topic+" "+str(msg.payload.decode()))

###########
# Main loop

if args.verbose > 0:
  log(args)

client = mqtt.Client()
client.on_connect = on_connect

client.message_callback_add("hermes/tts/say", tts_say)
client.message_callback_add("hermes/audioServer/default/playFinished", playFinished)
client.message_callback_add("jarvis/timer_duration", timer_duration)

client.connect(args.host, args.port, 60)

aws_client = boto3.setup_default_session(profile_name='jarvis')
aws_client = boto3.client('polly')

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()
