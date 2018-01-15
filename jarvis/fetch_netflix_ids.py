#!/usr/bin/python3

import os
import sys
import argparse
import re
import subprocess
from requests import post,get
import logging
import string
import html
#import yaml


parser = argparse.ArgumentParser()

#group = parser.add_mutually_exclusive_group(required=True)

parser.add_argument("-r", "--refresh", help="refresh lists", action='count')
parser.add_argument("-p", "--process", help="process raw.txt", action='count')

parser.add_argument("-v", "--verbose", help="verbose output, can be specified multiple times", action="count")

args = parser.parse_args()

LOG_FILE='./netflix.log'
logging.basicConfig(level=logging.DEBUG, filename=LOG_FILE, filemode="a+",
                        format="%(asctime)-15s %(levelname)-8s %(message)s")

def log(*msg):
    #logging.info(" ".join(msg))
    print (msg);

def clean_title(title):
    title = re.sub(" Season [0-9]+",'', title)
    title = title.replace('.','_')
    title = title.replace('+','and')
    title = title.replace(',','_')
    title = title.replace(' ','_')
    title = title.replace('!','')
    title = title.replace('?','')
    title = title.replace(':','_')
    title = title.replace("'",'')
    title = title.replace("&",'and')
    title = title.replace("*",'_')
    title = title.replace("(",'_')
    title = title.replace(")",'_')
    title = re.sub("_$",'', title)
    return title

def clean_long_title(title):
    title = re.sub(" Season [0-9]+",'', title)
    title = title.replace('&','and')
    title = title.replace('+','and')
    title = title.replace(':','and')
    return title

if args.refresh:
    with open('../apps/jarvis/tv_netflix_raw.txt', 'w') as outfile:
        outfile.seek(0)
        for page in range(1, 21):
            url = ("http://instantwatcher.com/search?page={}"
            "genres=83&page_title=TV+Series&sort=queue_count+desc&"
            "view=text&average_rating=32-max&content_type%5B%5D=3&"
            "maturity_rating_level%5B%5D=6&maturity_rating_level%5B%5D=8&"
            "maturity_rating_level%5B%5D=10&language_audio=18".format(page))
            print(url)
            response = get(url)
            outfile.write(str(response.content))
        outfile.truncate()
        outfile.close()
    with open('../apps/jarvis/tv_amazon_raw.txt', 'w') as outfile:
        outfile.seek(0)
        for page in range(1, 29):
            url = ("http://instantwatcher.com/a/search?page={}"
            "page_title=Prime+TV&sort=ratings_count+desc&view=text&"
            "&year=1950-max&amzn_rating=6-max&prime%5B%5D=2&"
            "content_type%5B%5D=2&quality%5B%5D=1&quality%5B%5D=2&"
            "maturity_rating_level%5B%5D=2&maturity_rating_level%5B%5D=5&"
            "maturity_rating_level%5B%5D=6&maturity_rating_level%5B%5D=8&"
            "maturity_rating_level%5B%5D=9&"
            "maturity_rating_level%5B%5D=10".format(page))
            print(url)
            response = get(url)
            outfile.write(str(response.content))
        outfile.truncate()
        outfile.close()

shows = {}

if args.process:
    with open('../apps/jarvis/tv_netflix_raw.txt', 'r') as infile:
        infile.seek(0)
        for line in infile:
            match = re.findall(
                "data-title-id=\"[0-9]+\">[a-zA-Z0-9 \:\`\'\&\*\#\;\.\,\?]+",
                line)
            for title in match:
                #print(title)
                contentid_match = re.search('[0-9]+', title)
                title_match = re.search('>(.*)', title)
                content_id = contentid_match.group(0)
                title = str(html.unescape(title_match.group(1)))
                long_title = title
                season = '1'
                title = clean_title(title)
                long_title = clean_long_title(long_title)
                title = re.sub(" Season [0-9]+",'', title)

                shows[title]={'title': title,
                    'long_title': long_title,
                    'channel': '12',
                    'seasons': {
                        season: content_id
                        }
                    }
    with open('../apps/jarvis/tv_amazon_raw.txt', 'r') as infile:
        infile.seek(0)
        for line in infile:
            matches = re.findall(
                "data-title-id=\"[0-9]+\">[a-zA-Z0-9 \:\`\'\&\*\#\;\.,]+.*?"
                "ref=atv_feed_catalog",
                line)
            for match in matches:
                title_match = re.search('>(.*?)<', match)
                title = str(html.unescape(title_match.group(1)))
                print(title)
                contentid_match = re.search('product\/([A-Z0-9]+)\/ref', match)
                content_id = contentid_match.group(1)
                season_match = re.search('Season ([0-9]+)', match)
                season = season_match.group(1) if season_match else '1'
                season = str(int(season))
                #print(content_id)
                long_title = title
                long_title = clean_long_title(long_title)
                title = clean_title(title)

                if not shows.get(title):
                    shows[title] = {}
                shows[title].update({'title': title,
                    'long_title': long_title,
                    'channel': '13',
                    })
                if not shows[title].get('seasons'):
                    shows[title]['seasons'] = {}

                #print(shows[title])
                #print(shows[title]['seasons'])
                #print(season, content_id)
                shows[title]['seasons'].update({
                        season: content_id
                        })
                #print(shows[title]['seasons'])
                #print(shows[title])




    outfile1 = open('../apps/jarvis/tv.yaml', 'w')
    outfile2 = open('../apps/jarvis/tv.txt', 'w')
    outfile1.seek(0)
    outfile2.seek(0)

    infile1 = open('../apps/jarvis/tv_extra.yaml', 'r')
    infile2 = open('../apps/jarvis/tv_extra.txt', 'r')
    for line in infile1:
        outfile1.write(line)
    for line in infile2:
        outfile2.write(line)

#    print(shows)
    for show, value in shows.items():
        #print(show)
        print("%s:" % show)
        print("  channel: %s" % value['channel'] )
        print("  seasons:")

        outfile1.write('%s:\n' % show )
        outfile1.write('  long_title: "%s"\n' % value['long_title'])
        outfile1.write('  channel: %s\n' % value['channel'])
        outfile1.write('  seasons: \n')
        for season, content_id in value['seasons'].items():
            print("    %s: %s" % (season, content_id))
            outfile1.write("    %s: %s\n" % (season, content_id))

        outfile2.write('%s\n' % value['long_title'])


    outfile1.truncate()
    outfile1.close()
    outfile2.truncate()
    outfile2.close()
