#!/bin/bash
/usr/bin/mosquitto_pub -h 192.168.1.19 -t hermes/feedback/sound/$1 -m '{"siteId": "default"}'
