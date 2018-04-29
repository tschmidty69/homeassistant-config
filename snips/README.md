These are a couple of scripts that I have running on my Snips RaspberryPI 3


### jarvis_says ###

Copy this script somewhere it can be executed by snips
```
cd /usr/local/bin
sudo wget https://raw.githubusercontent.com/tschmidty69/homeassistant-config/master/snips/jarvis_says.sh
sudo chmod +x jarvis_says.sh
sudo apt-get install mpg123
```
Install and configure aws cli as per
https://docs.aws.amazon.com/polly/latest/dg/getting-started-cli.html

Edit the jarvis_says.sh file and add your keys and which voice you would like to use
and path to your aws binary if needed.

Edit /etc/snips.toml, change TTS config to contain following 3 lines
```
[snips-tts]
provider = "customtts"
customtts = { command = ["/usr/local/bin/jarvis_says.sh", "-w", "%%OUTPUT_FILE%%", "-l", "%%LANG%%", "%%TEXT%%"] }
```
Stop the snips services
```
systemctl stop "snips-*"
```
Edit the snips-tts startup file
```
/lib/systemd/system/snips-tts.service
```
Add ' -vvv' to the end of the ExecStart line
```
ExecStart=/usr/bin/snips-tts -vvv
```
Restart snips-tts
```
systemctl daemon-reload
systemctl restart "snips-*"
```
# Testing

First test that the snips user can run the script
```
sudo su -s /bin/bash - _snips
/usr/local/bin/jarvis_says.sh -w /tmp/test.wav -l en "OK, here I am"
```
This should create mp3 files within /tmp/cache and a file /tmp/test.wav.

You can play the wav file using aplay.

If you don't have anything set to talk to snips yet you can test using mosquitto_pub. Snips by default runs mqtt on
127.0.0.1, port 9898
```
apt-get install mosquitto-clients
mosquitto_pub -h YOUR_SNIPS_IP -P YOUR_SNIPS_PORT -t hermes/tts/say -m '{"siteId":"default","text":"for how long?"}'
```

### jarvis-led ###

This is for the Seeed Studio Respeaker 4 mic for Rasp Pi

This will give pretty lights when jarvis detects a hotword and turn them off when done
You can edit it to use whatever lights you want of course.

jarvis_led.py is istalled using these commands. You probably already have the respeaker
since you need it to get the mic working so you can skip those steps
```
git clone https://github.com/respeaker/seeed-voicecard
cd seeed-voicecard
sudo ./install.sh 4mic
cd ..
git clone https://github.com/respeaker/4mics_hat.git
cd 4mics_hat
wget https://raw.githubusercontent.com/tschmidty69/homeassistant-config/master/snips/jarvis_led.py
sudo pip install spidev gpiodev numpy paho-mqtt
# edit jarvis_led to point to your snips mqtt broker
```
Test it
```
python jarvis_led.py
```
If it works you can grab this shell script and Ubuntu startup script to have it run at boot
```
cd /usr/local/bin
sudo wget https://raw.githubusercontent.com/tschmidty69/homeassistant-config/master/jarvis/jarvis-led.sh
sudo chmod +x jarvis-led.sh
cd /etc/systemd/system/
sudo wget https://raw.githubusercontent.com/tschmidty69/homeassistant-config/master/jarvis/jarvis-led.service
systemctl daemon-reload
systemctl enable jarvis-led
systemctl start jarvis-led
```
