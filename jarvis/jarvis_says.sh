#!/bin/bash
# Shell script to replace TTS in snips with AWS polly
#
# https://github.com/tschmidty69
# adapted from
# https://github.com/jvandewiel/
#
# Install and configure aws cli as per
# https://docs.aws.amazon.com/polly/latest/dg/getting-started-cli.html
# Installed in /home/<user>/.aws, configure with aws configure
# and provide key, secret, etc. Best practice is to create an IAM
# user and give tehm permission to just polly
#
# Edit the aws line below with your configure profile name and voice-ide prefered
#
# in /etc/snips.toml, change TTS config to contain following 3 lines
# [snips-tts]
# provider = "customtts"
# customtts = { command = ["/usr/local/jarvis_says.sh", "-w", "%%OUTPUT_FILE%%", "-l", "%%LANG%%", "%%TEXT%%"] }
#
# install mpg123 (apt-get install mpg123) for the mp3->wav conversion
#
# This will run e.g. '"/usr/local/jarvis_says.sh" "-w" "/tmp/.tmpbQHj3W.wav" "-l" "en" "For how long?"'
#
output_file="$2"
textstr="$5"
# get interm filename
interm_file="/tmp/sounds/$textstr.mp3"
# debugging
#echo 'Calling polly for output file:' $output_file >> /tmp/jarvis_says.log
#echo 'and intermediate file:' $interm_file>> /tmp/jarvis_says.log
#echo 'Input text:' $textstr >> /tmp/jarvis_says.log
# execute polly to get mp3 - check paths, voice set to Salli
mkdir -pv /tmp/sounds/
if [ ! -f "$interm_file.wav" ]; then
  aws --profile jarvis polly synthesize-speech --output-format mp3 --voice-id Geraint  --sample-rate 16000 --text "$textstr" "$interm_file"
  # execute conversion to wav
  #avconv -y -i "$interm_file" "$interm_file.wav"
  mpg123 -w "$interm_file.wav" "$interm_file"
fi
#echo "$interm_file.wav --> $output_file" >> /tmp/jarvis_says.log
cp -v "$interm_file.wav" "$output_file"
