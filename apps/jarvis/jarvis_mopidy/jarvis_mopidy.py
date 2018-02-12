import appdaemon.plugins.hass.hassapi as hass
import string
import json
import subprocess
from subprocess import Popen, PIPE, STDOUT
from fuzzywuzzy import fuzz, process

#####################
# Jarvis Mopidy Skill
#####################

class jarvis_mopidy(hass.Hass):

    def initialize(self):
        if not self.args.get('enabled'):
            return
        self.jarvis = self.get_app('jarvis_core')
        self.mopidy_host = self.args.get('mopidy_host')
        self.jarvis.jarvis_register_intent('playAlbum',
                                      self.jarvis_mopidy_play_album)
        self.jarvis.jarvis_register_intent('playArtist',
                                      self.jarvis_mopidy_play_artist)
        self.jarvis.jarvis_register_intent('playPlaylist',
                                      self.jarvis_mopidy_play_playlist)
        self.jarvis.jarvis_register_intent('playSong',
                                      self.jarvis_mopidy_play_song)
        self.jarvis.jarvis_register_intent('volumeUp',
                                      self.jarvis_mopidy_volume_up)
        self.jarvis.jarvis_register_intent('volumeDown',
                                      self.jarvis_mopidy_volume_down)
        self.jarvis.jarvis_register_intent('addSong',
                                      self.jarvis_mopidy_add_song)
        self.jarvis.jarvis_register_intent('nextSong',
                                      self.jarvis_mopidy_next_song)
        self.jarvis.jarvis_register_intent('previousSong',
                                      self.jarvis_mopidy_previous_song)
        self.jarvis.jarvis_register_intent('playMusic',
                                      self.jarvis_mopidy_play_music)
        self.jarvis.jarvis_register_intent('pauseMusic',
                                      self.jarvis_mopidy_pause_music)


###############################################################
#
# MOPIDY SPECIFIC FUNCTIONS
#
###############################################################

    def jarvis_mopidy_play_album(self, data, *args, **kwargs):
        self.log("__function__: {}".format(data), "INFO")
        self.jarvis.not_implemented()

    def jarvis_mopidy_play_artist(self, data, *args, **kwargs):
        self.log("__function__: {}".format(data), "INFO")
        artist_search=subprocess.check_output(["/usr/bin/mpc", "-h", self.mopidy_host,
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

            mpc_add=Popen(["/usr/bin/mpc", "-h", self.mopidy_host, "add"],
                            stdin=PIPE, encoding='utf8')
            mpc_add.communicate("\n".join(tracks))

            self.call_service("media_player/turn_on",
                              entity_id = 'media_player.mopidy')
            self.call_service("media_player/media_play",
                              entity_id = 'media_player.mopidy')
            self.jarvis_notify({'text': self.jarvis_speech('ok')
                               + ", playing music by "
                               + data['artist']})
        else:
            self.jarvis_notify({'text': self.jarvis_speech('sorry')
                            + ", I couldn't find any music by "
                            + data['artist']})

    def jarvis_mopidy_play_playlist(self, data, *args, **kwargs):
        self.log("__function__: {}".format(data), "INFO")
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
                self.jarvis_notify({'text':
                    self.jarvis.jarvis_get_speech('sorry')
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
            self.jarvis+notify({'text':
                self.jarvis.jarvis_get_speech('ok')
                + " playing playlist "
                + clean_playlist})
        else:
            self.jarvis_notify({'text':
                self.jarvis.jarvis_get_speech('sorry')
                + ", I couldn't get any playlist matching "
                + data['playlist']})

    def jarvis_mopidy_play_song(self, data, *args, **kwargs):
        self.log("jarvis_song: {}".format(data), 'DEBUG')
        if not data.get('artist') and not data.get('title'):
            return
        mpc_search=subprocess.check_output(["/usr/bin/mpc", "-h", self.mopidy_host,
                    "search", "artist", data['artist'], "title", data['title']],
                    universal_newlines=True)
        self.log("jarvis_artist: {}".format(artist_search), 'DEBUG')
        tracks = [str(s) for s in str(mpc_search).split('\n') if "track" in s]
        #for t in tracks:
        #    self.log("jarvis_artist: track: %s" % t, 'DEBUG')
        if tracks:
            subprocess.run(["/usr/bin/mpc", "repeat", "off"])
            self.call_service("media_player/shuffle_set",
                              entity_id = 'media_player.mopidy',
                              shuffle = 'false')
            self.call_service("media_player/media_pause",
                              entity_id = 'media_player.mopidy')
            self.call_service("media_player/clear_playlist",
                              entity_id = 'media_player.mopidy')

            mpc_add=Popen(["/usr/bin/mpc", "-h", self.mopidy_host, "add"],
                            stdin=PIPE, encoding='utf8')
            mpc_add.communicate("\n".join(tracks))

            self.call_service("media_player/turn_on",
                              entity_id = 'media_player.mopidy')
            self.call_service("media_player/media_play",
                              entity_id = 'media_player.mopidy')
            song = data['title'] if data['title'] else "music"
            self.jarvis_notify({'text':
                self.jarvis.jarvis_get_speech('ok')
                + ", playing "+song+" by "+data['artist']})
        else:
            self.jarvis_notify({'text':
                self.jarvis.jarvis_get_speech('sorry')
                + ", I couldn't find any music by "
                + data['artist']})

    def jarvis_mopidy_volume_up(self, data, *args, **kwargs):
        self.log("__function__: {}".format(data), "INFO")
        self.jarvis.not_implemented()

    def jarvis_mopidy_volume_down(self, data, *args, **kwargs):
        self.log("__function__: {}".format(data), "INFO")
        self.jarvis.not_implemented()

    def jarvis_mopidy_add_song(self, data, *args, **kwargs):
        self.log("__function__: {}".format(data), "INFO")
        self.jarvis.not_implemented()

    def jarvis_mopidy_next_song(self, data, *args, **kwargs):
        self.log("__function__: {}".format(data), "INFO")
        self.call_service("media_player/media_next_track",
                          entity_id = 'media_player.mopidy')
        self.jarvis.jarvis_end_session(
            {'sessionId': data.get('sessionId', ''),
             'text': self.jarvis.jarvis_get_speech('ok')})

    def jarvis_mopidy_previous_song(self, data, *args, **kwargs):
        self.log("__function__: {}".format(data), "INFO")
        self.jarvis.not_implemented()
        self.call_service("media_player/media_previous_track",
                          entity_id = 'media_player.mopidy')
        self.jarvis.jarvis_end_session(
            {'sessionId': data.get('sessionId', ''),
             'text': self.jarvis.jarvis_get_speech('ok')})

    def jarvis_mopidy_play_music(self, data, *args, **kwargs):
        self.log("__function__: {}".format(data), "INFO")
        self.call_service("media_player/media_play",
                          entity_id = 'media_player.mopidy')
        self.jarvis.jarvis_end_session(
            {'sessionId': data.get('sessionId', ''),
             'text': self.jarvis.jarvis_get_speech('ok')})

    def jarvis_mopidy_pause_music(self, data, *args, **kwargs):
        self.log("__function__: {}".format(data), "INFO")
        self.call_service("media_player/media_pause",
                          entity_id = 'media_player.mopidy')
        self.jarvis.jarvis_end_session(
            {'sessionId': data.get('sessionId', ''),
             'text': self.jarvis.jarvis_get_speech('ok')})
