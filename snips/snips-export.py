#!/usr/bin/env python3
import os
import json
import yaml
import argparse
import pprint

from config import *

from splinter import Browser

parser = argparse.ArgumentParser()

#group = parser.add_mutually_exclusive_group(required=True)

parser.add_argument("-d", "--debug", help="don't actually download html use cached files", action="count")
parser.add_argument("-v", "--verbose", help="verbose output, can be specified multiple times", action="count")
parser.add_argument("-a", "--assistant", help="update just this assistant")

args = parser.parse_args()

config = {}

console = 'https://console.snips.ai'

prof = {}
prof['browser.download.manager.showWhenStarting'] = 'false'
prof['browser.helperApps.alwaysAsk.force'] = 'false'
prof['browser.download.dir'] = os.getcwd()
prof['browser.download.folderList'] = 2
prof['browser.helperApps.neverAsk.saveToDisk'] = 'text/csv, application/csv, text/html,application/xhtml+xml,application/xml, application/octet-stream, application/pdf, application/x-msexcel,application/excel,application/x-excel,application/excel,application/x-excel,application/excel, application/vnd.ms- excel,application/x-excel,application/x-msexcel,image/png,image/jpeg,text/html,text/plain,application/msword,application/xml,application/excel,text/x-c'
prof['browser.download.manager.useWindow'] = 'false'
prof['browser.helperApps.useWindow'] = 'false'
prof['browser.helperApps.showAlertonComplete'] = 'false'
prof['browser.helperApps.alertOnEXEOpen'] = 'false'
prof['browser.download.manager.focusWhenStarting']= 'false'

if args.debug:
    print('Using cached html files')

if not args.debug:
    print('Starting browser')
    browser = Browser('firefox', profile_preferences=prof, headless=True)
else:
    browser = {'html': ''}

def get_html(url):
    if args.debug:
        url = url.replace('https://', '')
        url = url.replace('/', '_')
        print('Trying to read file {}'.format(url))
        file = open(url, 'r')
        return file.read()
    else:
        print('Loading {}'.format(url))
        browser.visit(url)
        save_url(url)
        return browser.html

def save_url(url):
    url = url.replace('https://', '')
    url = url.replace('/', '_')
    #print('Saving: {}'.format(url))
    file = open(url, 'w')
    file.write(browser.html)
    file.close()

url = '{}/login'.format(console)
if args.debug:
    get_html(url)
else:
    browser.visit(url)
    print('Loading: {}'.format(browser.url))
    browser.fill('email', email)
    browser.fill('password', password)
    button=browser.find_by_text('Log in')
    #for b in button:
    #    print('button: {}'.format(b._element.get_attribute('name')))
    if button:
        print('Logging in')
        button[1].click()

    # Print the current url
    print('Loading: {}'.format(browser.url))

    if 'assistants' in browser.url:
        print('Found Assistant Page')
    else:
        print('ERROR: Could not get to assistants page')
        exit(1)
    save_url(url)

assistants = []

# Gather a list of all intent IDs
for line in get_html(url).split('\n'):
    #print('line: {}'.format(line))
    if  'window.__APOLLO_STATE__=' in line:
        #print('Found  window.__APOLLO_STATE__=')
        states = json.loads(line.replace('window.__APOLLO_STATE__=', ''))
        #print(json.dumps(states, indent=4))
        for asst in states['ROOT_QUERY']['assistants']:
            assistants.append(asst['id'])
        #print(assistants)

sidebar = open('{}/_Sidebar.md'.format(wiki), 'w')
for assistant in assistants:
    bundles = []
    intents = []

    if args.assistant and not args.assistant == assistant:
        continue

    url = '{}/assistants/{}'.format(console, assistant.replace('Assistant:', ''))
    print('Trying to refresh bundles')
    print('url: {}'.format(browser.url))
    lines = get_html(url).split('\n')
    bundle_button = browser.find_by_xpath('HomeAssistant')
    bundle_button.click()
    intent_button = browser.find_by_text('HassTurnOn')
    intent_button.click()
    print('url: {}'.format(browser.url))
    lines = get_html(url).split('\n')
    print('url: {}'.format(browser.url))
    browser.back()
    for line in lines:
        #print('line: {}'.format(line))

        if  'window.__APOLLO_STATE__=' in line:
            #print('Found  window.__APOLLO_STATE__=')
            states = json.loads(line.replace('window.__APOLLO_STATE__=', ''))
            #print(json.dumps(states, indent=4))
            asst_name = states[assistant].get('title', 'UNKNOWN')
            print("Assistant: {}".format(asst_name))

            for bundle in states[assistant].get('bundles', ''):
                bundles.append(bundle.get('id'))
            print('Bundles: {}'.format(bundles))
            for bundle in bundles:
                print("Bundle: {}".format(states[bundle]))
                print("Bundle: {}".format(states[bundle].get('name')))
                #if states[bundle].get('name') in my_bundles:
                for intent in states[bundle].get('intents', []):
                    #print(intent['id'])
                    intents.append(intent['id'].replace('PartialIntent:', ''))
            #print('Intents: {}'.format(intents))

            # if args.debug:
            #     intents = ['intent_0Q3zGE19g88']

            if intents:
                url = '{}/intent-editor/{}'.format(console, intents[0])
                #html = get_html(url).split('\n')
            else:
                print('ERROR: No intents found')
                continue

            config_slots = {}
            config = {}
            for intent in intents:
                url = '{}/intent-editor/{}'.format(console, intent)
                html = get_html(url).split('\n')
                for line in html:
                    #print('line: {}'.format(line))
                    if  'window.__APOLLO_STATE__=' in line:
                        #print('Found  window.__APOLLO_STATE__=')
                        states = json.loads(line.replace('window.__APOLLO_STATE__=', ''))
                        #print(json.dumps(states, indent=4))
                        slots = []

                        # Get Slot Entity Names
                        for key, value in states.items():

                            if key == '$Intent:{}.config'.format(intent):
                                config[intent]= {}
                                config[intent]['name'] = value.get('name', '')
                                #print('Intent: {}'.format(config[intent]['name']))
                                #print(key, value)
                                slots = [slot['id'] for slot in value.get('slots', [])]
                                for slot in slots:
                                    for slot_key, slot_value in states.items():
                                        if slot in slot_key:
                                            if slot_value['entity'].startswith('snips/'):
                                                continue
                                            config_slots[slot_value['entityId']] = {
                                                'name': slot_value['entity'],
                                                'values': []
                                            }
                                #print(config_slots)
                                for slot_name, slot_id in config_slots.items():
                                    for slot_key, slot_value in states.items():
                                        if 'IntentEntity:{}.data'.format(slot_name) in slot_key:
                                            #print('slot: {}'.format(slot_value.get('value', '')))
                                            config_slots[slot_name]['values'].append(slot_value.get('value', ''))

                                # Build utterances
                                config[intent]['training_examples'] = []
                                for tx_key, tx_value in states.items():
                                    if tx_key == '$Intent:{}.customIntentData'.format(intent):
                                        # Build list of utterance keys
                                        #print(tx_value.get('utterances'))
                                        #print(utterances)

                                        for utterance in [ value['id'] for value in tx_value.get('utterances') ]:
                                            #print(utterance)
                                            tx_example = ''
                                            for ut_key, ut_value in states.items():
                                                #print(ut_key,ut_value)
                                                if ut_key == utterance:
                                                    for data in ut_value.get('data', []):
                                                        # build list of data bits
                                                        #print('data: {}'.format(data))
                                                        for ud_key, ud_value in states.items():
                                                            if ud_key == data.get('id'):
                                                                if ud_value.get('slot_name'):
                                                                    tx_example += '[{}]({})'.format(ud_value['text'], ud_value['slot_name'])
                                                                else:
                                                                    tx_example += ud_value.get('text', '')

                                            #print('utterance: {}'.format(tx_example))
                                            config[intent]['training_examples'].append(tx_example)

                print('Config loaded for {}'.format(config[intent].get('name', '')))

            #pprint.pprint(config)
            #pprint.pprint(config_slots)
            print('Saving config files for {}'.format(asst_name))
            wiki_dir = '{}/{}'.format(wiki,asst_name)
            print("Creating dir: {}".format(wiki_dir))
            os.makedirs(wiki_dir, exist_ok=True)
            sidebar.write("### {}\n".format(asst_name))

            for intent_id, intent_data in config.items():
                print(intent_data['name'])
                sidebar.write("* [{1}](https://github.com/tschmidty69/hass-snips-bundle-intents/wiki/{0}-{1})\n".format(
                              asst_name, intent_data['name']))

                with open('{}-{}.md'.format(wiki_dir, intent_data['name']), 'w') as outfile:
                    outfile.write('```yaml\n')
                    yaml.dump({intent_id: intent_data}, outfile, default_flow_style=False)
                    outfile.write('```\n')
                    outfile.close()
            for slot_id, slot_data in config_slots.items():
                print(slot_data['name'])
                sidebar.write("* [{1}](https://github.com/tschmidty69/hass-snips-bundle-intents/wiki/{0}-{2})\n".format(
                              asst_name, slot_data['name'], slot_data['name'].replace(' ', '-')))
            with open('{}-{}.md'.format(wiki_dir, slot_data['name'].replace(' ', '-')), 'w') as outfile:
                    outfile.write('```yaml\n')
                    yaml.dump({slot_id: slot_data}, outfile, default_flow_style=False)
                    outfile.write('```\n')
                    outfile.close()

sidebar.close()
if not args.debug:
    browser.quit()
exit()
    # # Export Slots
    # button = browser.find_by_xpath('//*[@id="BkTs83jFFf_tooltip-menu"]/button')
    # if button:
    #     print('Found slots ...')
    #     button.click()
    #
    # button = browser.find_by_xpath('//*[@id="SJggj8niKFM_tooltip-menu"]/button/svg')
    # if button:
    #     print('Found slots ...')
    #     button.click()


if not args.debug:
    browser.quit()

# browser.driver.set_page_load_timeout(600)
# retrain=browser.find_by_text('Retrain')
# if retrain:
#     print('Retraining assistant')
#     retrain[0].click()

# print('Trying to download assistant...')
# url='https://console.snips.ai/api/assistants/proj_8EW074Zxr81/download'
# browser.visit(url)
# print('Loading: {}'.format(browser.url))
# print('Downloaded assistant')
