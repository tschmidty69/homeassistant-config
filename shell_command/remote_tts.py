#!/srv/homeassistant/bin//python

import string
import json
import random
import subprocess

import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish

my_siteId = 'wohnzimmer'
host = '192.168.1.220'

def on_connect(client, userdata, flags, rc):
  print("Connected with result code "+str(rc))

  # Subscribing in on_connect() means that if we lose the connection and
  # reconnect then subscriptions will be renewed.
  client.subscribe("hermes/tts/say")
  client.subscribe("hermes/audioServer/default/playFinished")
  client.subscribe("jarvis/timer_duration")

def tts_say(client, userdata, msg):
  print(msg.topic+" "+str(msg.payload.decode()))
  data = json.loads(msg.payload.decode())
  print('text: {}'.format(data['text']))
  print('siteId: {}'.format(data['siteId']))
  if not data.get('siteId') == my_siteId:
      print('not for site {}'.format(my_siteId))
      return

  # Add some translations here
  text = data['text'].replace('Turned on', 'Eingeschaltet')
  text = text.replace('Turned off', 'Ausgeschaltet')


  # Generating audio
  sessionId=''.join(random.choices(string.ascii_uppercase + string.digits, k=16))

  subprocess.run(['/usr/bin/pico2wave','-w','/tmp/'+sessionId+'.wav', text])
  wav_file = open('/tmp/'+sessionId+'.wav', "rb")
  audio_wav = wav_file.read()
  wav_file.close()

  publish.single('hermes/audioServer/'+data['siteId']+'/playBytes/'+sessionId+'/',
    payload=audio_wav, qos=0, retain=False, hostname=args.host, port=args.port,
    client_id="", keepalive=60, will=None, auth=None, tls=None, protocol=mqtt.MQTTv311)

client = mqtt.Client()
client.on_connect = on_connect

client.message_callback_add("hermes/tts/say", tts_say)

client.connect(host, 1883, 60)
client.loop_forever()
