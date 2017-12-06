#!//srv/homeassistant/bin//python
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import subprocess
import json

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
  print("Connected with result code "+str(rc))

  # Subscribing in on_connect() means that if we lose the connection and
  # reconnect then subscriptions will be renewed.
  client.subscribe("hermes/tts/say")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
  print(msg.topic+" "+str(msg.payload.decode()))
  data = json.loads(msg.payload.decode())
  print(data['text'])
  subprocess.run(['/home/homeassistant/.homeassistant/shell_command/jarvis_says.sh', data['text']], stdout=subprocess.PIPE)
  publish.single('hermes/tts/sayFinished', payload='{"siteId": "'+data['siteId']+'", "sessionId": "'+data['sessionId']+'", "id": "'+data['id']+'"}', qos=0, retain=False, hostname="192.168.1.19",
    port=1883, client_id="", keepalive=60, will=None, auth=None, tls=None,
    protocol=mqtt.MQTTv311)

#  subprocess.run([HA_BASE+'/shell_commnads/jarvis_says.sh, 'how long'])

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("192.168.1.19", 1883, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()
