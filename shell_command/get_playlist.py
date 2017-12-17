#!/usr/bin/python

import sys
import argparse
import subprocess
import random
from requests import post
import logging
from subprocess import Popen, PIPE, STDOUT
import string
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

parser = argparse.ArgumentParser()

group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-a", "--artist", help="artist to search for")
group.add_argument("-p", "--playlist", help="playlist to search for")

parser.add_argument("-r", "--random", help="choose random playlist if more than one", action="store_true")
parser.add_argument("-v", "--verbose", help="verbose output, can be specified multiple times", action="count")

args = parser.parse_args()

HA_BASE="/home/homeassistant/.homeassistant/"
HA_SENSOR="sensor.mopidy_playlist"

SPOTIFY_USER=subprocess.check_output(["grep", "http_base_url", HA_BASE+"secrets.yaml"]).rsplit()[1]
SPOTIFY_PASSWORD=subprocess.check_output(["grep", "http_base_url", HA_BASE+"secrets.yaml"]).rsplit()[1]

MPC_BINARY="/usr/bin/mpc"
MPC_HOST=subprocess.check_output(["grep", "mopidy_host", HA_BASE+"secrets.yaml"]).rsplit()[1]

# You can hard code these as well
REST_URL=subprocess.check_output(["grep", "http_base_url", HA_BASE+"secrets.yaml"]).rsplit()[1]
REST_PASSWORD=subprocess.check_output(["grep", "http_password", HA_BASE+"secrets.yaml"]).rsplit()[1]

logging.basicConfig(level=logging.DEBUG, filename=HA_BASE+"get_playlist.log", filemode="a+",
                        format="%(asctime)-15s %(levelname)-8s %(message)s")

def log(*msg):
  logging.info(' '.join(msg))
  print ' '.join(msg);

if args.verbose > 1:
  log( "REST_URL:", REST_URL )
  log( "REST_PASSWORD:", REST_PASSWORD )

if args.playlist:
  playlists=[]
  PLAYLISTS=subprocess.check_output([MPC_BINARY, "-h", MPC_HOST, "lsplaylists"])

  if args.verbose > 1:
    log( "playlist:", args.playlist)
    log( "PLAYLISTS:", PLAYLISTS )

#  matching = [s for s in PLAYLISTS.split("\n") if args.playlist.lower() in s.lower()]
  playlists = process.extractBests(args.playlist, PLAYLISTS.split("\n"), score_cutoff=60)
  if args.verbose >1:
    print "tuple:  %s" % (playlists,)
  matching=[x[0] for x in playlists]


  if matching:

    if args.verbose:
      log( "Found these playlists:", '\n'.join(matching) )

    if args.random:
      playlist = random.choice(matching)
    else:
      playlist = matching[0]

    if args.verbose:
      log( "Using", playlist )
  else:
      if args.verbose:
        log( "Mo matching playlist found" )
      playlist="no match"

  log( "playlist:", playlist )

  url = REST_URL+'/api/states/' + HA_SENSOR
  headers = {'x-ha-access': REST_PASSWORD,
             'content-type': 'application/json'}
  data = '{"state": "'+playlist+'"}'

  if args.verbose > 1:
    log( "Url:", url )
    log( "data:", data )

  response = post(url, headers=headers, data=data)
elif args.artist:
  if args.verbose > 1:
    log( "ARTIST:", args.artist )

  ARTIST=subprocess.check_output([MPC_BINARY, "-h", MPC_HOST, "search", "artist", args.artist])
  tracks = [s for s in ARTIST.split("\n") if "track" in s]
  if args.verbose:
    for i in tracks:
      log( "track:", i )

  subprocess.check_output([MPC_BINARY, "-h", MPC_HOST, "clear"])
  mpc_add=Popen([MPC_BINARY, "-h", MPC_HOST, "add"], stdin=PIPE)
  mpc_add.communicate("\n".join(tracks))
  subprocess.check_output([MPC_BINARY, "-h", MPC_HOST, "play"])

  url = REST_URL+'/api/states/' + HA_SENSOR
  headers = {'x-ha-access': REST_PASSWORD,
             'content-type': 'application/json'}
  data = '{"state": "'+string.replace(args.artist,'"','')+'"}'

  if args.verbose > 1:
    log( "Url:", url )
    log( "data:", data )

  response = post(url, headers=headers, data=data)

log(response.text)
