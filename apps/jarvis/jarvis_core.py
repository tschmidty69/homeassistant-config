import appdaemon.plugins.hass.hassapi as hass
import ast
import sys
import subprocess
from subprocess import Popen, PIPE, STDOUT
import random
import string
import uuid
import json
import yaml
import requests
import tempfile
from pathlib import Path
import os, re, time
import paho.mqtt.publish as publish

######################
# Jarvis Core
######################

class jarvis_core(hass.Hass):

    def initialize(self):
        self.snips_mqtt_host = self.args.get('snips_mqtt_host')
        self.snips_mqtt_port = self.args.get('snips_mqtt_port', 1883)
        self.log("__function__: snips %s %s" %
            (self.snips_mqtt_host, self.snips_mqtt_port), 'DEBUG')

        self.sessionId = ''
        self.siteId = 'default'
        self.intents_enabled = True

        self.global_vars['intents'] = {}
        self.global_vars['dialogue_callback'] = {}
        self.global_vars['dialogue_listener_callback'] = {}
        self.global_vars['dialogue_http_audio_callback'] = {}
        self.global_vars['dialogue_enabled'] = {}

        self.speech_file = (os.path.join(os.path.dirname(__file__)) + '/'
                               + self.args.get('speech_file',
                                               '/data/speech_en.yml'))

        self.acceptable_probability = self.args.get('acceptable_probability',
                                                    .5)
        self.players = self.args.get('media_player')
        self.volume = {}
        for room, player in self.players.items():
            self.log("__function__ (player): %s %s" % (room, player), 'DEBUG')
            self.volume[player] = self.get_state(entity=player,
                                                 attribute='volume_level')
        self.listen_event(self.event_listener, 'JARVIS_MQTT')
        self.listen_event(self.jarvis_notify, 'JARVIS_NOTIFY')
        self.listen_event(self.jarvis_action, 'JARVIS_ACTION')

        self.listen_event(self.jarvis_intent_not_recognized,
                          'JARVIS_INTENT_NOT_RECOGNIZED')
        self.jarvis_register_intent('YesNoResponse',
                                    self.jarvis_yes_no_response)

    def jarvis_register_intent(self, intent, callback):
        self.log("__function__: %s" % intent, 'INFO')
        self.global_vars['intents'][intent] = callback

    def register_dialogue_callback(self, site_id, callback):
        self.log("__function__: %s" % site_id, 'INFO')
        self.global_vars['dialogue_callback'][site_id] = callback

    def register_dialogue_listener_callback(self, site_id, callback):
        self.log("__function__: %s" % site_id, 'INFO')
        self.global_vars['dialogue_listener_callback'][site_id] = callback

    def enable_intents(self, state=True):
        self.log("__function__: %s" % state, 'INFO')
        self.intents_enabled = state

    def event_listener(self, event_name, data, *args, **kwargs):
        self.log("__function__: %s" % data, 'INFO')
        payload = json.loads(data['payload']) if data.get('payload') else {}

        site_id = payload.get('siteId', self.siteId)

        # If dialogue is enabled, we are waiting for tts to finish here
        if self.global_vars['dialogue_enabled'].get(site_id):
            self.log("__function__: dialogue_enabled for site %s" % site_id, 'INFO')
            self.log("__function__: topic %s" % data.get('topic'), 'INFO')
            # audio done playing, now call to set up listening
            if 'hermes/audioServer/'+site_id+'/playFinished' in data.get('topic'):
                self.log("__function__: callback: %s" %
                    self.global_vars['dialogue_listener_callback'].get(site_id), 'INFO')

                if self.global_vars['dialogue_listener_callback'].get(site_id):
                    self.log("__function__: dialogue_listener_callback %s" % payload, 'INFO')
                    self.global_vars['dialogue_listener_callback'][site_id](payload)

            # got our answer, send it to callback
            if 'hermes/asr/textCaptured' in data.get('topic', ''):
                self.log("__function__: dialogue_callback %s" % site_id, 'INFO')
                if self.global_vars['dialogue_callback'].get(site_id):
                    self.log("__function__: dialogue_callback %s" % payload, 'INFO')
                    self.global_vars['dialogue_callback'][site_id](payload)

        if 'hermes/hotword/' in data.get('topic', ''):
            hotword_data = {'toggle': data['topic'].split('toggle')[-1],
                            'payload': data.get('payload')}
            self.listening(hotword_data)

        if not self.intents_enabled:
            self.log("__function__: not listening for intents")
            return

        if 'hermes/intent/' in data.get('topic', ''):
            if data.get('payload'):
                data = json.loads(data['payload'])
            if data['intent']['intentName'].startswith('user_'):
                intent = data['intent']['intentName'].split('__')[-1]
            else:
                intent = data['intent']['intentName'].split(':')[-1]
            self.log("__function__ intent received: %s" % intent, 'INFO')
            if data['intent'].get('probability', 0) < self.acceptable_probability:
                self.log("__function__ intent probability "
                         "too low, should drop: %s" %
                         data['intent'].get('probability', 0), 'INFO')
            if self.global_vars['intents'].get(intent):
                self.global_vars['intents'][intent](data)
            else:
                self.log("__function__: UnknownIntent %s" %data, 'INFO')

    def jarvis_intent_not_recognized(self, data, *args, **kwargs):
        self.log("__function__: %s" %data, 'INFO')
        self.jarvis_notify('NONE', {'text':
                           self.jarvis_get_speech('intent_not_recognized')})

    def jarvis_notify(self, data, *args, **kwargs):
        self.log("__function__: %s" % data, 'INFO')
        payload={'siteId': data.get('siteId', self.siteId),
                 'init': {'type': 'notification',
                          'text': data.get('text', '')}}
        publish.single('hermes/dialogueManager/startSession',
                       payload=json.dumps(payload),
                       hostname=self.snips_mqtt_host,
                       port=self.snips_mqtt_port)

    def jarvis_play_http_audio(self, data, callback, *args, **kwargs):
        self.log("__function__: %s" % data, 'INFO')
        request_id = uuid.uuid4()
        payload={'siteId': data.get('siteId', self.siteId),
                 'init': {'type': 'notification',
                          'session_id': data.get('session_id', '')}}

        response = requests.get(data.get('url'), stream=True)
        mp3_file = tempfile.NamedTemporaryFile()
        wav_file = tempfile.NamedTemporaryFile()
        mp3_file.write(response.content)
        subprocess.run(['/usr/bin/mpg123','-q','-w', wav_file.name, mp3_file.name])
        audio = wav_file.read()
        byte_id = uuid.uuid4()
        publish.single('hermes/audioServer/{}/playBytes/{}'.format(
            data.get('siteId', self.siteId), byte_id),
                       payload=audio,
                       hostname=self.snips_mqtt_host,
                       port=self.snips_mqtt_port)
        wav_file.close()
        mp3_file.close()
        if callback:
            self.global_vars['http_audio_callback'] = callback
            self.register_dialogue_listener_callback(data.get('siteId', self.siteId),
                self.jarvis_http_audio_callback)

    def jarvis_http_audio_callback(self, data, *args, **kwargs):
        self.log("__function__: %s" % data, 'INFO')
        if self.global_vars['http_audio_callback']:
            self.global_vars['http_audio_callback'](data)
        self.global_vars['http_audio_callback'] = None

    def jarvis_hotword_on(self, data, *args, **kwargs):
        self.log("__function__: %s" % data, 'INFO')
        payload={'siteId': data.get('siteId', self.siteId)}
        #TODO: configurable hotward
        publish.single('hermes/hotword/jarvis/ToggleOn',
                       payload=json.dumps(payload),
                       hostname=self.snips_mqtt_host)

    def jarvis_hotword_off(self, data, *args, **kwargs):
        self.log("__function__: %s" % data, 'INFO')
        payload={'siteId': data.get('siteId', self.siteId)}
        #TODO: configurable hotward
        publish.single('hermes/hotword/jarvis/ToggleOff',
                       payload=json.dumps(payload),
                       hostname=self.snips_mqtt_host)

    def jarvis_end_session(self, data, *args, **kwargs):
        self.log("__function__: %s" % data, 'INFO')
        payload={'siteId': data.get('siteId', self.siteId)}
        if data.get('text'):
             payload['init'].update({'text': data.get('text')})
        publish.single('hermes/dialogueManager/endSession',
                       payload=json.dumps(payload),
                       hostname=self.snips_mqtt_host,
                       port=self.snips_mqtt_port)

    def jarvis_continue_session(self, data, *args, **kwargs):
        self.log("__function__: %s" % data, 'INFO')
        payload={'siteId': data.get('siteId', self.siteId)}
        if data.get('custom_data'):
            payload.update({'customData': data.get('custom_data')})
        if data.get('text'):
             payload['init'].update({'text': data.get('text')})
        if data.get('intentFilter'):
            payload['init'].update({'intentFilter': [data.get('intentFilter')]})
        publish.single('hermes/dialogueManager/continueSession',
                       payload=json.dumps(payload),
                       hostname=self.snips_mqtt_host,
                       port=self.snips_mqtt_port)

    def jarvis_action(self, data, *args, **kwargs):
        self.log("__function__: %s" % data, 'INFO')
        payload={'siteId': data.get('siteId', self.siteId),
                 'init': {'type': 'action',
                 'canBeEnqueued': True}}
        if data.get('custom_data'):
            payload.update({'customData': data.get('custom_data')})
        if data.get('text'):
             payload['init'].update({'text': data.get('text')})
        if data.get('intentFilter'):
            payload['init'].update({'intentFilter': [data.get('intentFilter')]})
        publish.single('hermes/dialogueManager/startSession',
                       payload=json.dumps(payload),
                       hostname=self.snips_mqtt_host,
                       port=self.snips_mqtt_port )

    def jarvis_yes_no_response(self, data, *args, **kwargs):
        """Custom handler for specific Yes/No Intent.
           This pulls information from the customData
           To fire an intent."""
        self.log("__function__: %s" % data, "INFO")
        if data.get('payload'):
            data = json.loads(data.get('payload', data))

        intent = ''
        slots = []
        if data['slots'][0]['value']['value'] == 'yes':
            intent_data = ast.literal_eval(data.get('customData', ''))
            payload={'siteId': data.get('siteId', self.siteId),
                     'sessionId': data.get('sessionId'),
                     'input': data.get('customData'),
                     'intent': {'intentName': intent_data.get('intent', '')},
                     'slots': intent_data.get('slots', [])}
            publish.single('hermes/intent/'+intent_data.get('intent', ''),
                           payload=json.dumps(payload),
                           hostname=self.snips_mqtt_host,
                           port=self.snips_mqtt_port
            )
        else:
            self.jarvis_notify('NONE', {"text": self.jarvis_speech('ok')})

    def jarvis_get_speech(self, speech):
        # hack for now so we get any speech changes without reloading
        with open(self.speech_file, "r") as f:
          self.speech = yaml.load(f)
        return random.choice(self.speech.get(speech))

    def snips_start_session(self, payload):
        publish.single('hermes/dialogueManager/startSession',
          payload=json.dumps(payload),
          hostname=self.snips_mqtt_host,
          port=self.snips_mqtt_port
        )

    def listening(self, data, *args, **kwargs):
        self.log("__function__: %s" % data, 'DEBUG')
        if not self.args.get('ramp_volume_on_hotword'):
            self.log("__function__: ramp_volume_on_hotword disabled", 'INFO')
            return
        for room, player in self.players.items():
            if room in data['payload']:
                if data.get('toggle') == 'Off':
                    self.log("__function__ lowering volume in room: %s"
                             % room, 'INFO')
                    if not self.get_state(entity=player,
                                          attribute="is_volume_muted"):
                        self.volume[player] = self.get_state(
                            entity=player, attribute='volume_level')
                        self.ramp_volume(player,
                            self.volume[player], 0.2)
                if data.get('toggle') == 'On':
                    if not self.get_state(entity=player,
                                          attribute="is_volume_muted"):
                        self.ramp_volume(player, 0.2,
                                                self.volume[player])

    def ramp_volume(self, player, volume, dst_vol, *args, **kwargs):
        self.log("__function__: %s %s %s" % (player, volume, dst_vol),
            'DEBUG')
        if self.get_state(player) == 'off':
            return
        time_time = time.time
        start = time_time()
        period = .1
        count = 0
        steps = 7
        step = (volume - dst_vol) / steps
        while True:
          if count == steps: break
          if (time_time() - start) > period:
            count += 1
            start += period
            self.call_service("media_player/volume_set",
              entity_id = player,
              volume_level = str(volume - step * count))

    def not_implemented(self, data, *args, **kwargs):
        self.log("__function__: %s" %data, 'INFO')
        if self.args.get('speech_on_not_implemented'):
            self.jarvis_notify('NONE', {'text':
                self.jarvis_get_speech('sorry') + ', '
                + self.jarvis_get_speech('cant_do_yet')})
