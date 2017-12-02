#!/usr/bin/python

import sys
import argparse
import subprocess
import random
from requests import post
import logging

parser = argparse.ArgumentParser()

parser.add_argument("-p", "--playlist", help="playlist to search for", required="yes") 
parser.add_argument("-r", "--random", help="choose random playlist if more than one", action="store_true")
parser.add_argument("-v", "--verbose", help="verbose output, can be specified multiple times", action="count")

args = parser.parse_args()

if args.verbose:
  print "Searching for playlist:", args.playlist

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
  logging.info(msg)
  print msg;  

if args.verbose > 1:
  log( "REST_URL:", REST_URL )
  log( "REST_PASSWORD:", REST_PASSWORD )


PLAYLISTS=subprocess.check_output([MPC_BINARY, "-h", MPC_HOST, "lsplaylists"])

if args.verbose > 1:
  log( "PLAYLISTS:", PLAYLISTS.split("\n") )

matching = [s for s in PLAYLISTS.split("\n") if args.playlist.lower() in s.lower()]

if matching:

  if args.verbose:
    log( "Found these playlists:", matching )

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

url = 'https://'+REST_URL+'/api/states/' + HA_SENSOR
headers = {'x-ha-access': REST_PASSWORD,
           'content-type': 'application/json'}
data = '{"state": "'+playlist+'"}'

if args.verbose > 1:
  log( "Url:", url )
  log( "headers:", headers )
  log( "data:", data )

response = post(url, headers=headers, data=data)

log(response.text)
