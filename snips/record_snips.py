import sys
import wave
import paho.mqtt.client as mqtt
import struct
#from io import io.StringIO
import json
import time
import collections
import os.path

mqtt_client = mqtt.Client()

SENSITIVITY = 0.5
HOTWORD_ID = 'default'
MQTT_ADDRESS = '192.168.1.19'  #default just incase its not enabld in the toml file
MQTT_PORT = '1883'

count = 0


#class to store audio after the hotword is spoken
class AudioBuffer(object):
    def __init__(self, size = 4096):
        self._buf = collections.deque(maxlen=size)

    def extend(self, data):
        self._buf.extend(data)

    def get(self):
        tmp = bytes(bytearray(self._buf))
        self._buf.clear()
        return tmp


def on_connect(client, userdata, flags, rc):
    print('connected: {}'.format(rc))
    mqtt_client.subscribe('hermes/audioServer/default/audioFrame')

buffer = AudioBuffer(512*16000*20)

def on_message(client, userdata, msg):
    global count
    print('message: {} len:{}'.format(userdata, len(msg.payload[44:])))
    print(' '.join([str(a) for a in msg.payload[44:]]))
    siteId = msg.topic.split('/')[2]
    #i want to capture what is said after the hotword as a wave
    buffer.extend(msg.payload[44:struct.unpack('<L', msg.payload[4:8])[0]])
    #client_buffer[siteId].extend(data)
    #data = client_buffer[siteId].get()
    #save wave file
    count += 1
    if count == 512:
        waveFile = wave.open(siteId + '.wav', 'wb')
        waveFile.setnchannels(1)
        waveFile.setsampwidth(2)
        waveFile.setframerate(16000)
        waveFile.writeframes(buffer.get())
        waveFile.close()
        exit(0)



if __name__ == '__main__':
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_ADDRESS, int(MQTT_PORT))
    mqtt_client.loop_forever()
