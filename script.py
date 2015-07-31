#!/usr/local/bin/python3.4
# coding: utf-8

import os
import re
from urllib import request
from urllib.parse import urlencode
from json import loads
from collections import namedtuple
import contextlib
from dateutil import parser

limit = 300
my_phone_number = '972541111111' #your phone number with 972 prefix 
Neighborhoods = "רחביה,בית הכרם,רסקו,נחלאות,גבעת רם".split(',') #Words to look for in posts
nexmo_api_secret = "" #You can get both the key and secret from nexmo.com
nexmo_api_key = ""
facebook_access_token = '' #You can get you facebook access token from: https://developers.facebook.com/tools/explorer/
facebook_group_id = '172544843294' #Dirot Mipe Leozen Jerusalem
max_single_room_price, min_apt_price, max_apt_price = 1800, 3000, 5300 #price < 1800 or 3000 < price < 5300

known_posts_file = "known_posts.txt"
try :
    with open(known_posts_file,"r") as f:
        known_hosts = f.read()
        first_run = False
except :
    with open(known_posts_file,"w") as f:
        known_hosts = ""
        first_run= True

def add_post_to_known_posts(post):
    with open(known_posts_file,"a") as f:
        f.write(post.id +'\n')


url = "https://graph.facebook.com/v2.0/{}/feed/?access_token={}&limit={}"
res = loads(request.urlopen(url.format(facebook_group_id, facebook_access_token, limit)).read().decode('utf8'))
data = res['data']

"""
ENTER PHONE NUMBER HERE:
"""

def hebrew_to_english(text):
    translate = {chr(ord('א')+heb):eng for heb,eng in zip(range(27),"abgdhwzhtycclmmnnseppzzkrrst")} 
    translate[' '] = '-'
    translate[','] = ','
    return "".join(translate[i] for i in text if i in translate)


def send_text(text,number):
    nexmo_url = "https://rest.nexmo.com/sms/json?api_key={key}&api_secret={secret}&from=NEXMO&to={number}&text={text}"
    request.urlopen(nexmo_url.format(key= nexmo_api_key, secret = nexmo_api_secret,
                     number = number,text = request.quote(text.encode('utf8'))))
def text_post(post):
    text = "{link} at {neighborhood} for {prices}".format(link = post.get_link(),
                                                         neighborhood = hebrew_to_english(str(post.neighborhood)),
                                                          prices = str(post.prices))
    send_text(text,yotam_phone_number)


fields = 'id,message,link,updated_time,prices,neighborhood'.split(',')#,comments,likes'

class Post:
    def __init__(self,dictionary):
        for field in fields:
            setattr(self,field,dictionary.get(field,''))
        self.prices = [float(num) for num in re.findall(r'(\d{3,4})',self.message)]
        self.neighborhood = [neighborhood for neighborhood in Neighborhoods if neighborhood in self.message]
    def get_link(self):
        return 'https://www.facebook.com/groups/{}/?view=permalink&id={}'.format(*self.id.split('_'))

    def __iter__(self):
        return (getattr(self,field) for field in fields)

posts = [Post(d) for d in data]

def filter_posts(posts):
    for post in posts:
        if post.neighborhood:
            if any(price < max_single_room_price or min_apt_price  < price < max_apt_price for price in post.prices):
                yield post

relevant_posts =list(filter_posts(posts))

for post in relevant_posts:
    if post.id not in known_hosts:
        if not first_run:
            text_post(post)
        print("New Post {}".format(post.id))
        add_post_to_known_posts(post)
