import time
from pixels import Pixels, pixels
#from alexa_led_pattern import AlexaLedPattern
from google_home_led_pattern import GoogleHomeLedPattern

import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish

pixels.pattern = GoogleHomeLedPattern(show=pixels.show)

host = "192.168.1.19"
port = 1883

def pixels_wakeup(client, userdata, msg):
#  print("pixels_wakeup")
  pixels.wakeup()
  time.sleep(3)

def pixels_think(client, userdata, msg):
#    print("pixels_think")
    pixels.think()
    time.sleep(3)

def pixels_speak(client, userdata, msg):
#    print("pixels_speak")
    pixels.speak()
    time.sleep(6)

def pixels_off(client, userdata, msg):
#    print("pixels_off")
    pixels.off()
    time.sleep(3)

def log(msg):
  logging.info(msg)
  print(msg);

def on_connect(client, userdata, flags, rc):
  print("Connected with result code "+str(rc))

  # Subscribing in on_connect() means that if we lose the connection and
  # reconnect then subscriptions will be renewed.
  client.subscribe("hermes/hotword/toggleOff")
  client.subscribe("hermes/hermes/asr/stopListening")
  client.subscribe("hermes/audioServer/default/playBytes")

  client.subscribe("hermes/hotword/toggleOn")
  client.subscribe("hermes/audioServer/default/playFinished")
  client.subscribe("hermes/dialogueManager/endSession")


client = mqtt.Client()
client.on_connect = on_connect

client.message_callback_add("hermes/hotword/toggleOff", pixels_wakeup)
client.message_callback_add("hermes/asr/stopListening", pixels_think)
client.message_callback_add("hermes/audioServer/default/playBytes", pixels_speak)

client.message_callback_add("hermes/dialogueManage/endSession", pixels_off)
client.message_callback_add("hermes/audioServer/default/playFinished", pixels_off)
client.message_callback_add("hermes/hotword/toggleOn", pixels_off)

client.connect(host, port, 60)

client.loop_forever()

