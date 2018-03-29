#!/usr/bin/python3
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import json

# Edit these
mqtt_host="192.168.1.19"
mqtt_port=1883

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("hermes/intent/#")
    client.subscribe("hermes/nlu/#")
    client.subscribe("hermes/asr/#")
    client.subscribe("hermes/dialogueManager/#")

def asr(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload.decode()))
    data = json.loads(msg.payload.decode())
    print(data)

def dialogueManager(client, userdata, msg):
    data = json.loads(msg.payload.decode())
    print(data)
    print(msg.topic+" "+str(msg.payload.decode()))

# The callback for when a PUBLISH message is received from the server.
def handle_intent(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload.decode()))
    data = json.loads(msg.payload.decode())
    print("data.sessionId"+data['sessionId'])
    print("data.intent"+str(data['intent']))
    print("data.slots"+str(data['slots']))

    if data['intent']['intentName'] == 'searchWeather':
        payload = {'sessionId': data.get('sessionId', ''),
                    'text': "It might be sunny outside?"
                   }
             }
        publish.single('hermes/dialogueManager/endSession',
                       payload=json.dumps(payload),
                       hostname=mqtt_host,
                       port=mqtt_port)

    # We didn't recognize that intent.
    else:
        payload = {sessionId': data.get('sessionId', ''),
                   'text': "I am not sure what to do",
                   }
        publish.single('hermes/dialogueManager/endSession',
                       payload=json.dumps(payload),
                       hostname=mqtt_host,
                       port=mqtt_port)

def intentNotParsed(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload.decode()))
    data = json.loads(msg.payload.decode())
    print(data)

    # I am actually not sure what message is sent for partial queries
    if 'sessionId' in data:
        payload = {'text': 'I am not listening to you anymore',
                   'sessionId': data.get('sessionId', '')
                   }
        publish.single('hermes/dialogueManager/endSession',
                       payload=json.dumps(payload),
                       hostname=mqtt_host,
                       port=mqtt_port)

def intentNotRecognized(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload.decode()))
    data = json.loads(msg.payload.decode())
    print(data)

    # Intent isn't recognized so session will already have ended
    # so we send a notification instead.
    if 'sessionId' in data:
        payload = {'siteId': data.get('siteId', ''),
                   'init': {'type': 'notification',
                            'text': "I didn't understand you"
                           }
                   }
        publish.single('hermes/dialogueManager/endSession',
                       payload=json.dumps(payload),
                       hostname=mqtt_host,
                       port=mqtt_port)

def nlu(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload.decode()))
    data = json.loads(msg.payload.decode())
    print(data)

# setTimer intent, doesn't actually do anything as you can see
def setTimer(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload.decode()))
    data = json.loads(msg.payload.decode())
    print("data.sessionId"+data['sessionId'])
    print("data.intent"+data['intent'])
    print("data.slots"+data['slots'])


client = mqtt.Client()
client.on_connect = on_connect

# These are here just to print random info for you
client.message_callback_add("hermes/asr/#", asr)
client.message_callback_add("hermes/dialogueManager/#", dialogueManager)
client.message_callback_add("hermes/nlu/#", nlu)
client.message_callback_add("hermes/nlu/intentNotParsed", intentNotParsed)
client.message_callback_add("hermes/nlu/intentNotRecognized",
                            intentNotRecognized)


# This function respondes to all intents
client.message_callback_add("hermes/intent/#", handle_intent)

# This responds specifically to the setTimer intent
client.message_callback_add("hermes/intent/setTimer", setTimer)


client.connect(mqtt_host, mqtt_port, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()
