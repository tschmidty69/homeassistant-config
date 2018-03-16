#!/usr/bin/env python3
import os
import time

from splinter import Browser


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

browser = Browser('firefox', profile_preferences=prof, headless=True)
url = "https://console.snips.ai/login"

browser.visit(url)
print('Loading: {}'.format(browser.url))
browser.fill('email', 'tschmidty@yahoo.com')
browser.fill('password', 'gordo1999')
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
    ext(1)

retrain=browser.find_by_text('Retrain')
if retrain:
    print('Retraining assistant')
    retrain[0].click()

print('Trying to download assistant...')
browser.driver.set_page_load_timeout(600)
url='https://console.snips.ai/api/assistants/proj_8EW074Zxr81/download'
browser.visit(url)
print('Loading: {}'.format(browser.url))
