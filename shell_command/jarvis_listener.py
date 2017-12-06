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

parser = argparse.ArgumentParser()

parser.add_argument("-m", "--host", help="host to connect to", default='127.0.0.1')
parser.add_argument("-p", "--port", help="port to connect to", default=1883)
parser.add_argument("-v", "--verbose", help="verbose output, can be specified multiple times", action="count", default = 0)

args = parser.parse_args()

HA_BASE="/home/homeassistant/.homeassistant/"
HA_SENSOR="sensor.jarvis_listener"
LOG_FILE=os.path.basename(sys.argv[0]).replace('.py','')+".log"

logging.basicConfig(level=logging.DEBUG, filename=HA_BASE+LOG_FILE, filemode="a+",
                        format="%(asctime)-15s %(levelname)-8s %(message)s")

def log(msg):
  logging.info(msg)
  print(msg);

def on_connect(client, userdata, flags, rc):
  print("Connected with result code "+str(rc))

  # Subscribing in on_connect() means that if we lose the connection and
  # reconnect then subscriptions will be renewed.
  client.subscribe("hermes/tts/say")
  client.subscribe("hermes/audioServer/default/playFinished")

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

def playFinished(client, userdata, msg):
  log(msg.topic+" "+str(msg.payload.decode()))

if args.verbose > 0:
  log(args)

client = mqtt.Client()
client.on_connect = on_connect

client.message_callback_add("hermes/tts/say", tts_say)
client.message_callback_add("hermes/audioServer/default/playFinished", playFinished)

client.connect(args.host, args.port, 60)

aws_client = boto3.setup_default_session(profile_name='jarvis')
aws_client = boto3.client('polly')

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()


