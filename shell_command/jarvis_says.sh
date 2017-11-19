aws --profile jarvis polly synthesize-speech --output-format mp3 --voice-id Geraint --text "$1" /tmp/temp.mp3
cat /tmp/temp.mp3 | netcat -q 1 192.168.1.202 1234
#rm /tmp/temp.mp3

