#!/srv/homeassistant/bin/python
import json
request = json.loads('{"id":"123456","input":"set a timer of 5 minutes for the turkey","intent":{"intentName":"user_rZEKlr8M7M3__SetTimer","probability":0.80519766},"slots":[{"rawValue":"5 minutes","value":{"kind":"Duration","years":0,"quarters":0,"months":0,"weeks":0,"days":0,"hours":0,"minutes":5,"seconds":0,"precision":"Exact"},"range":{"start":15,"end":24},"entity":"snips/duration","slotName":"timer_duration"},{"rawValue":"turkey","value":{"kind":"Custom","value":"turkey"},"range":{"start":33,"end":39},"entity":"string","slotName":"timer_name"}],"sessionId":null}')
#print(request)
intent_type = request['intent']['intentName'].split('__')[-1]
slots = {}

for slot in request.get('slots', []):
  if 'value' in slot['value']:
    slots[slot['slotName']] = { 'value': slot['value']['value'] }
  elif slot['entity'] == 'snips/duration':
    duration = "{0:02}:{1:02}:{2:02}".format( slot['value']['hours'], slot['value']['minutes'], slot['value']['seconds'] )
    slots[slot['slotName']] = { 'value': duration, 'rawValue': slot['rawValue']  }

print( slots )
