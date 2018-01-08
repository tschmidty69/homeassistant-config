These are a couple of scripts that I have running on my Snips RaspberryPI 3

This us for the Seeed Studio Respeaker 4 mic for Rasp Pi

This will give pretty lights when jarvis detects a hotword and turn them off when done
You can edit it to use whatever lights you want of course.

### jarvis-led ###
jarvis_led.py is istalled using these commands. You probably already have the respeaker
since you need it to get the mic working so you can skip those steps
```
git clone https://github.com/respeaker/seeed-voicecard
cd seeed-voicecard
sudo ./install.sh 4mic
cd /srv/respeaker
git clone https://github.com/respeaker/4mics_hat.git
source /srv/respeaker/bin/activate
wget https://raw.githubusercontent.com/tschmidty69/homeassistant/master/jarvis/jarvis_led.py
# edit jarvis_led to point to your snips mqtt broker
```
Test it
```
source /srv/respeaker/bin/activate
python jarvis_led.py
```
If it works you can grab this shell script and Ubuntu startup script to have it run at install
```
cd /usr/local/bin
sudo wget https://raw.githubusercontent.com/tschmidty69/homeassistant/master/jarvis/jarvis-led.sh
sudo chmod +x jarvis-led.sh
cd /etc/systemd/system/
sudo wget https://raw.githubusercontent.com/tschmidty69/homeassistant/master/jarvis/jarvis-led.service
systemctl daemon-reload
systemctl enable jarvis-led
systemctl start jarvis-led
```
### jarvis_says ###

Copy this script somewhere it can be executed bu snips
```
cd /usr/local/bin
sudo wget https://raw.githubusercontent.com/tschmidty69/homeassistant/cmaster/jarvis/jarvis_says.sh
sudo chmod +x jarvis_says.sh
sudo mkdir /tmp/sounds
sudo chown _snips /tmp/sounds
sudo apt-get install mpg123
```
Install and configure aws cli as per
https://docs.aws.amazon.com/polly/latest/dg/getting-started-cli.html
Installed in /home/<user>/.local/bin, configure with aws configure
and provide key, secret, etc.

Edit /etc/snips.toml, change TTS config to contain following 3 lines
```
[snips-tts]
provider = "customtts"
customtts = { command = ["/usr/local/jarvis_says.sh", "-w", "%%OUTPUT_FILE%%", "-l", "%%LANG%%", "%%TEXT%%"] }
```
Edit the snips-tts startup file
```
/lib/systemd/system/snips-tts.service
```
Add ' -vvv' the end of the ExecStart line
```
ExecStart=/usr/bin/snips-tts -vvv
```
Restart snips-tts
```
systemctl restart snips-tts
```
If you don't have anything set to talk to snips yet you can test using mosquitto_pub. Snips by default runs mqtt on
127.0.0.1, port 8989
```
apt-get install mosquitto-clients
mosquitto_pub -h YOUR_SNIPS_IP -P YOUR_SNIPS_PORT -t hermes/tts/say -m'{"siteId":"default","text":"for how long?"}'
```
