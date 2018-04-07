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

# The callback for when a PUBLISH message is received from the server.
def handle_intent(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload.decode()))
    data = json.loads(msg.payload.decode())
    print("data.sessionId"+data['sessionId'])
    print("data.intent"+str(data['intent']))
    print("data.slots"+str(data['slots']))

    #
    # Here is where we would handle our intent and send a response
    #
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


client = mqtt.Client()
client.on_connect = on_connect

# This function responds to all intents
client.message_callback_add("hermes/intent/#", handle_intent)

# This responds specifically to the setTimer intent
# client.message_callback_add("hermes/intent/setTimer", setTimer)


client.connect(mqtt_host, mqtt_port, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()
