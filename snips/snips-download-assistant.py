#!/usr/bin/env python3
import requests
import zipfile

# Edit here, assistant is shwon in the url of the snips console.
assistant = 'proj_YOUR_PROJECT'
payload = {'email': 'your_email',
           'password': 'your_password'}

assistant_directory = '/usr/share/snips/'

login_url = 'https://console.snips.ai/api/login'
download_url = 'https://console.snips.ai/api/assistants/{}/download'.format(assistant)

with requests.Session() as session:
    post = session.post(login_url, data=payload)
    r = session.get(download_url, stream=True)
    with open('./assistant.zip', 'wb') as f:
        size = 0
        for chunk in r.iter_content(chunk_size=1024):
            size += 1
            if chunk: # filter out keep-alive new chunks
                print('{} KB'.format(size), end='\r')
                f.write(chunk)
        print('')

zip = zipfile.ZipFile('./assistant.zip', 'r')
zip.extractall(assistant_directory)
zip.close()
