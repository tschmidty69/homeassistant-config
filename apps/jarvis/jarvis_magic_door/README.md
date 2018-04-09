# Welcome to The Magic Door on Snips!

A fun Alexa skill adapted to work with Snips with the gracious help of
the folks at [The Magic Door](https://www.themagicdoor.org)

### INSTALL

Assumes you are running this on a raspberry pi with a pi user and snips
installed on the same pi. Adapt install instructions if needed.
```
sudo apt-get -y install python3-pip python3-venv curl mpg321

sudo python3 -m venv /srv/jarvis
sudo chown -R pi.pi /srv/jarvis
source /srv/jarvis/bin/activate

pip3 install appdaemon
pip3 install paho-mqtt

cd /srv/jarvis
wget https://github.com/tschmidty69/jarvis-appdaemon/releases/download/0.1/jarvis_magic_door.tgz
tar zxvfp jarvis_magic_door.tgz
```

### Running

There will be lots of debug output. Ignore an error about players list. This
listens to an mqtt broker on 127.0.0.1. You can edit this and add user/pass
in appdaemon.yaml

```appdaemon -c /srv/jarvis```

You can also run it as a daemon although I like being able to restart with
ctrl-c and all the endless debug messages.

```appdaemon -d -c /srv/jarvis```

### Uninstall

```rm -rf /srv/jarvis```

## Playing

Add the 'The Magic Door' bundle to your Snips assistant and follow the normal
steps to update your Snips install.

If you want to keep persistent game sessions, set a unique username in the
apps/jarvis_magic_door/jarvis_magic_door.yaml file and restart appdaemon.

Start the game with 'Launch The Magic Door'

If using a site id of default, the game will start a new session when the audio
is done playing so you can continue without saying the hotword. If you take
too long to speak, just say the hotword and whatever else. You can edit the
siteid that is listened for in appdaemon.yaml.

You can say 'Repeat Scene' or 'Can you say that again' to replay the
descriptions.

You might be able to say 'Start Over' to start over, but my Assistant is stuck
with a response that conflicts with yes and no, but give it a try.

I also would love to be able to say the hotword to cancel the audio (hint, hint!)

Have Fun!
