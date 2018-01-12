import appdaemon.appapi as appapi
import sys
import subprocess
from subprocess import Popen, PIPE, STDOUT
import random
import string
import json
import boto3
import yaml
from pathlib import Path
import os, re, time, threading
#import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

######################
# Jarvis
######################

class jarvis(appapi.AppDaemon):

  def initialize(self):
    self.log("Jarvis is alive")
    self.aws_client = boto3.setup_default_session(profile_name='jarvis')
    self.aws_client = boto3.client('polly')
    self.snips_mqtt_host = '192.168.1.19'
    self.snips_mqtt_port = 1883
    self.mpc_host = '192.168.1.201'
    self.sessionId = ""
    self.siteId = "default"

    self.speech_file = os.path.join(os.path.dirname(__file__)
                                    + '/jarvis_speech/speech.yaml')
    with open(self.speech_file, "r") as f:
        self.speech = yaml.load(f)

    self.players = [
        "media_player.snapcast_client_6152618a83b04b70b879e3fa1f4664b2",
        "media_player.snapcast_client_4b8c047b8b04d3bb68c2b07e00000005"]
    self.volume = {'heat': {}, 'cool': {}}
    for player in self.players:
        self.volume[player] = self.get_state(player, "volume_level")
    self.thermostats = {'heat': {}, 'cool': {}}
    self.thermostats['heat']['downstairs'] =\
                        '2gig_technologies_ct101_thermostat_iris_heating_1'
    self.thermostats['heat']['upstairs'] =\
                        '2gig_technologies_ct101_thermostat_iris_heating_1_2'
    self.thermostats['cool']['downstairs'] =\
                        '2gig_technologies_ct101_thermostat_iris_heating_1'
    self.thermostats['cool']['downstairs'] =\
                        '2gig_technologies_ct101_thermostat_iris_heating_1_2'

    self.listen_event(self.jarvis_say, "JARVIS_SAY")
    self.listen_event(self.jarvis_notify, "JARVIS_NOTIFY")
    self.listen_event(self.jarvis_query, "JARVIS_QUERY")
    self.listen_event(self.jarvis_response, "JARVIS_RESPONSE")
    self.listen_event(self.jarvis_set_timer, "JARVIS_SET_TIMER")
    self.listen_event(self.jarvis_playlist, "JARVIS_PLAYLIST")
    self.listen_event(self.jarvis_artist, "JARVIS_ARTIST")
    self.listen_event(self.jarvis_song, "JARVIS_SONG")
    self.listen_event(self.jarvis_lights, "JARVIS_LIGHTS_ON")
    self.listen_event(self.jarvis_lights, "JARVIS_LIGHTS_OFF")
    self.listen_event(self.jarvis_listening, "JARVIS_LISTENING")
    self.listen_event(self.jarvis_listening, "JARVIS_NOT_LISTENING")
    self.listen_event(self.jarvis_weather, "JARVIS_WEATHER")
    self.listen_event(self.jarvis_thermostat, "JARVIS_THERMOSTAT")
    self.listen_event(self.jarvis_intent, "JARVIS_INTENT")
    self.listen_event(self.jarvis_intent_not_parsed,
                      "JARVIS_INTENT_NOT_PARSED")

  def snips_publish(self, payload):
    publish.single('hermes/dialogueManager/startSession',
      payload=json.dumps(payload),
      hostname=self.snips_mqtt_host,
      port=self.snips_mqtt_port,
      protocol=mqtt.MQTTv311
    )

  def jarvis_speech(self, speech):
    # hack for now so we get any speech changes without reloading
    with open(self.speech_file, "r") as f:
      self.speech = yaml.load(f)

    return random.choice(self.speech.get(speech))

  def jarvis_weather(self, event_name, data, *args, **kwargs):
    self.log("jarvis_weather: {}".format(data), "INFO")

  def jarvis_thermostat(self, event_name, data, *args, **kwargs):
    self.log("jarvis_thermostat: {}".format(data), "INFO")
    if data.get('payload'):
        data = json.loads(data.get('payload', data))
    #self.log("jarvis_thermostat: intent {}".format(data['intent']), "INFO")
    #self.log("jarvis_thermostat: slots {}".format(data['slots']), "INFO")

    if not data.get('slots'):
        self.log("jarvis_thermostat: no slot information")
        return

    slots = {}
    for slot in data['slots']:
        slots[slot['slotName']] = slot['value']['value']

    self.log("jarvis_thermostat: {}".format(slots), "INFO")
    if slots.get('zone') == 'upstairs':
        thermostat = 'upstairs'
    else:
        thermostat = 'downstairs'

    if not slots.get('temperature') and not slots.get('direction'):
        self.jarvis_notify(None, {'siteId': data.get('siteId', 'default'),
                             'text': self.jarvis_speech('sorry')
                             + ", I can only do heat or ac"})
        return
    if slots.get('direction'):
        if slots.get('temperature'):
            if not 1 <= int(slots['temperature']) < 10:
                self.jarvis_notify(None,
                            {'siteId': data.get('siteId', 'default'),
                             'text': self.jarvis_speech('sorry')
                             + str(slots['temperature'])
                             + ' degrees is too big of a change for me.'})
                return
            else:
                temperature = int(slots['temperature'])
        elif slots.get('direction') == 'up':
            temperature = 2
        else:
            temperature = -2
        cur_temp = self.get_state(
            'climate.'+self.thermostats['heat'][thermostat],
            'current_temperature')
        target_temp = int(cur_temp) + int(temperature)
    elif slots.get('temperature'):
        if not 60 <= int(slots['temperature']) < 91:
            self.jarvis_notify(None, {'siteId': data.get('siteId', 'default'),
                                 'text': self.jarvis_speech('sorry')
                                 + "I cant set the temperature"
                                 + 'to ' + slots['temperature']
                                 + ' degrees.'})
            return
        else:
            target_temp = int(slots['temperature'])
    if target_temp:
        self.log("jarvis_thermostat: target_temp {}".format(target_temp),
                 "INFO")
        if slots.get('mode') == 'cool':
            mode = 'cool'
        else:
            mode = 'heat'
        self.call_service('climate/set_temperature',
                          entity_id='climate.'
                                    + self.thermostats[mode][thermostat],
                          temperature=target_temp)
        self.jarvis_notify(None, {'siteId': data.get('siteId', 'default'),
                                  'text': self.jarvis_speech('ok')
                                  + ", setting the "
                                  + thermostat + ' '
                                  + mode + ' to ' + str(target_temp)
                                  + ' degrees'})
    else:
        self.jarvis_notify(None, {'siteId': data.get('siteId', 'default'),
                                  + 'text':"Sorry, I didnt understand"})

  def jarvis_intent(self, event_name, data, *args, **kwargs):
    self.log("jarvis_intent: {}".format(data), "INFO")

  def jarvis_intent_not_parsed(self, event_name, data, *args, **kwargs):
    self.log("jarvis_intent_not_parsed: {}".format(data), "INFO")
    self.jarvis_notify('NONE', {'text': self.jarvis_speech('sorry')
                    + " I didn't get that"})

  def jarvis_listening(self, event_name, data, *args, **kwargs):
    self.log("jarvis_listening: {}".format(data), "INFO")
    if event_name == "JARVIS_LISTENING":
        for player in self.players:
            self.volume[player] = self.get_state(player, "volume_level")
            self.jarvis_ramp_volume(player, self.volume[player], 0.2)
    if event_name == "JARVIS_NOT_LISTENING":
        for player in self.players:
            self.jarvis_ramp_volume(player, 0.2, self.volume[player])

  def jarvis_notify(self, event_name, data, *args, **kwargs):
    self.log("jarvis_notify: {}".format(data), "INFO")
    payload={'siteId': data.get('siteId', self.siteId),
             'init': {'type': 'notification',
                      'text': data['text']}}
    self.snips_publish(payload)

  def jarvis_query(self, event_name, data, *args, **kwargs):
    self.log("jarvis_query: {}".format(data), "INFO")
    payload={'siteId': data.get('siteId', self.siteId),
             'customData': data.get('topic', 'default'),
             'init': {'type': 'action',
             'text': data['text'],
             'canBeEnqueued': True}}
    self.snips_publish(payload)

  def jarvis_response(self, event_name, data, *args, **kwargs):
    self.log("jarvis_response: {}".format(data), "INFO")

  def jarvis_say(self, event_name, data, *args, **kwargs):
    self.log("jarvis_say: {}".format(data), "INFO")
    if data.get('type') == 'joke':
      self.jarvis_notify('NONE', {
                "text": self.jarvis_speech('ok')
                        + ", "
                        + self.jarvis_speech('joke')})
    else:
      self.jarvis_notify('NONE', {"text":
                         self.jarvis_speech(data.get('text', ''))})

  def jarvis_set_timer(self, event_name, data, *args, **kwargs):
    self.log("jarvis_set_timer: {}".format(data), "INFO")
    duration = int(data['hours'])*360
    duration += int(data['minutes'])*60
    duration += int(data['seconds'])

    #self.log("duration: {}".format(duration), "INFO")
    self.handle = self.run_in(
        self.jarvis_timer_done,
        duration,
        timer_name=data['name']
    )
    text = self.jarvis_speech('ok') + ", setting a timer of "

    if int(data['hours']) > 0:
        if int(data['hours']) > 1:
            text += data['hours']+" hours "
        else:
            text += " 1 hour "
        if int(data['minutes']) > 0:
            text += " and "
    if int(data['minutes']) > 0:
        if int(data['minutes']) > 1:
            text += data['minutes']+" minutes "
        else:
            text += " 1 minute "
        if int(data['seconds']) > 0:
            text += " and "
    if int(data['seconds']) > 0:
        if int(data['seconds']) > 1:
            text += data['seconds']+" seconds "
        else:
            text += " 1 second "
    text += 'for '
    text += data['name']
    #self.log("jarvis_set_timer: text: {}".format(text), "INFO")

    self.jarvis_notify('NONE', {'text': text})

  def jarvis_cancel_timer(self, event_name, data, kwargs):
    self.log("jarvis_cancel_timer: {}".format(data), "INFO")
    try:
      self.cancel_timer(self.handle)
      speech={"text": self.jarvis_speech('ok') + ", canceling your timer"}
      self.jarvis_notify('NONE', speech)
    except:
      speech={"text": self.jarvis_speech('sorry') + ", I couldn't find that timer"}
      self.jarvis_notify('NONE', speech)

  def jarvis_timer_done(self, kwargs):
    self.log("jarvis_timer_done: {}".format(kwargs))
    self.jarvis_notify('NONE', {'text': self.jarvis_speech('ok')
                       + ", your timer for "
                       + kwargs['timer_name']
                       + " is done"})
    #TODO: start a dialog and ask if reminder was heard

  def jarvis_playlist(self, event_name, data, *args, **kwargs):
    self.log("jarvis_playlist: {}".format(data), "INFO")
    self.call_service("media_player/shuffle_set",
                      entity_id = 'media_player.mopidy',
                      shuffle = 'true')
    subprocess.run(["/usr/bin/mpc", "repeat", "on"])
    source_list = self.get_state(
            "media_player.mopidy",
            "source_list")
    #self.log("jarvis_music: source_list {}".format(source_list), "INFO")
    if source_list is not None:
        matching = process.extractBests(data['playlist'],
            source_list,
            score_cutoff=60
        )
        playlists=[x[0] for x in matching]
        #self.log("jarvis_music matching playlists: {}".format(playlists),
        #         "INFO")
        playlist = random.choice(playlists)
        if not playlist:
            self.jarvis_notify('NONE', {'text': self.jarvis_speech('sorry')
                            + ", I couldn't find playlist matching "
                            + data['playlist']})
            return

        self.log("jarvis_music using playlist: %s" % format(playlist),
                 "INFO")
        self.call_service("media_player/turn_on",
                          entity_id = 'media_player.mopidy')
        self.call_service("media_player/clear_playlist",
                          entity_id = 'media_player.mopidy')
        self.call_service("media_player/play_media",
            entity_id = "media_player.mopidy",
            media_content_type = "playlist",
            media_content_id = playlist
        )
        self.call_service("media_player/media_next_track",
            entity_id = "media_player.mopidy"
        )
        clean_playlist = re.sub(' \(by .*\)', '', playlist)
        self.jarvis+notify('NONE', {'text': self.jarvis_speech('ok')
                           + "OK, playing playlist "
                           + clean_playlist})
    else:
        self.jarvis_notify('NONE', {'text': self.jarvis_speech('sorry')
                           + ", I couldn't get any playlist matching "
                           + data['playlist']})

  def jarvis_artist(self, event_name, data, *args, **kwargs):
    self.log("jarvis_artist: {}".format(data), "INFO")

    artist_search=subprocess.check_output(["/usr/bin/mpc", "-h", self.mpc_host,
                "search", "artist", data['artist']],
                universal_newlines=True)
    #self.log("jarvis_artist: {}".format(artist_search), "INFO")
    tracks = [str(s) for s in str(artist_search).split('\n') if "track" in s]
    #for t in tracks:
    #    self.log("jarvis_artist: track: %s" % t )
    if tracks:
        subprocess.run(["/usr/bin/mpc", "repeat", "off"])
        self.call_service("media_player/media_pause",
                          entity_id = 'media_player.mopidy')
        self.call_service("media_player/clear_playlist",
                          entity_id = 'media_player.mopidy')

        mpc_add=Popen(["/usr/bin/mpc", "-h", self.mpc_host, "add"],
                        stdin=PIPE, encoding='utf8')
        mpc_add.communicate("\n".join(tracks))

        self.call_service("media_player/turn_on",
                          entity_id = 'media_player.mopidy')
        self.call_service("media_player/media_play",
                          entity_id = 'media_player.mopidy')
        self.jarvis_notify('NONE', {'text': self.jarvis_speech('ok')
                           + ", playing music by "
                           + data['artist']})
    else:
        self.jarvis_notify('NONE', {'text': self.jarvis_speech('sorry')
                        + ", I couldn't find any music by "
                        + data['artist']})

  def jarvis_song(self, event_name, data, *args, **kwargs):
    self.log("jarvis_song: {}".format(data), "INFO")
    mpc_search=subprocess.check_output(["/usr/bin/mpc", "-h", self.mpc_host,
                "search", "artist", data['artist'], "title", data['title']],
                universal_newlines=True)
    #self.log("jarvis_artist: {}".format(artist_search), "INFO")
    tracks = [str(s) for s in str(mpc_search).split('\n') if "track" in s]
    #for t in tracks:
    #    self.log("jarvis_artist: track: %s" % t)
    if tracks:
        subprocess.run(["/usr/bin/mpc", "repeat", "off"])
        self.call_service("media_player/shuffle_set",
                          entity_id = 'media_player.mopidy',
                          shuffle = 'false')
        self.call_service("media_player/media_pause",
                          entity_id = 'media_player.mopidy')
        self.call_service("media_player/clear_playlist",
                          entity_id = 'media_player.mopidy')

        mpc_add=Popen(["/usr/bin/mpc", "-h", self.mpc_host, "add"],
                        stdin=PIPE, encoding='utf8')
        mpc_add.communicate("\n".join(tracks))

        self.call_service("media_player/turn_on",
                          entity_id = 'media_player.mopidy')
        self.call_service("media_player/media_play",
                          entity_id = 'media_player.mopidy')
        song = data['title'] if data['title'] else "music"
        self.jarvis_notify('NONE', {'text': self.jarvis_speech('ok')
                        + ", playing "+song+" by "+data['artist']})
    else:
        self.jarvis_notify('NONE', {'text': self.jarvis_speech('sorry')
                        + ", I couldn't find any music by "
                        + data['artist']})

  def jarvis_lights(self, event_name, data, *args, **kwargs):
    self.log("jarvis_lights: {}".format(data), "INFO")
    onOff = "on" if event_name == 'JARVIS_LIGHTS_ON' else "off"
    if data.get('payload'):
        data = json.loads(data.get('payload'))
    self.log("jarvis_lights: {}".format(data['slots']), "INFO")
    try:
        house_room = data['slots'][0]['value'].get('value', '')
    except:
        house_room = "unknown"
    text = ""
    if house_room == 'christmas':
        self.call_service("switch/turn_"+onOff,
          entity_id = 'switch.unknown_id0312_unknown_type0221_id251c_switch_3')
        text = "Ok"
    elif house_room == 'driveway':
        self.call_service("switch/turn_"+onOff,
          entity_id = 'switch.ge_unknown_type4952_id3037_switch')
        text = "Ok"
    elif house_room == 'living_room':
        self.call_service("switch/turn_"+onOff,
          entity_id = 'group.living_room_lights')
        text = "Ok"
    if text:
        self.jarvis_notify(None, {'siteId': data.get('siteId', 'default'),
                             'text': self.jarvis_speech('ok')
                             + ", turning the "+ house_room +
                             " lights " + onOff})
    else:
        self.jarvis_notify(None, {'siteId': data.get('siteId', 'default'),
                             'text': self.jarvis_speech('sorry')
                             + ", I can't control the "+
                             house_room+" lights"})

  def jarvis_ramp_volume(self, player, volume, dst_vol, *args, **kwargs):
    self.log("jarvis_ramp_volume: %s %s %s" % (player, volume, dst_vol),
        "INFO")
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
    #        self.log("jarvis_ramp_volume: %s" % (str(volume - step * count)),
    #            "INFO")
        start += period
        self.call_service("media_player/volume_set",
          entity_id = player,
          volume_level = str(volume - step * count))
