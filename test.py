import json
data = json.loads('{"text":"For how long?","lang":"en","id":"3e42cc64-df90-4d81-b652-8a3420dd484d","siteId":"default","sessionId":"ada34a58-272f-401f-a4dc-ad865093ed4a"}')
print(data['text'])
