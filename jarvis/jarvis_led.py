import time
from pixels import Pixels, pixels
from google_home_led_pattern import GoogleHomeLedPattern

import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish

pixels.pattern = GoogleHomeLedPattern(show=pixels.show)

host = "192.168.1.19"
port = 1883

def pixels_wakeup(client, userdata, msg):
  pixels.wakeup()
  time.sleep(3)

def pixels_think(client, userdata, msg):
    pixels.think()
    time.sleep(3)

def pixels_speak(client, userdata, msg):
    pixels.speak()
    time.sleep(6)

def pixels_off(client, userdata, msg):
    pixels.off()
    time.sleep(3)

def log(msg):
  logging.info(msg)
  print(msg);

def on_connect(client, userdata, flags, rc):
  print("Connected with result code "+str(rc))

  client.subscribe("hermes/hotword/toggleOff")
  client.subscribe("hermes/hotword/toggleOn")

client = mqtt.Client()
client.on_connect = on_connect

client.message_callback_add("hermes/hotword/toggleOff", pixels_wakeup)
client.message_callback_add("hermes/hotword/toggleOn", pixels_off)

client.connect(host, port, 60)

client.loop_forever()
