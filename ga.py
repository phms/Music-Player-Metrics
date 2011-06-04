"""
Google Analytics Track Code for Phytom implementation of ga.php

Original Google Analytics Reference:
http://code.google.com/mobile/analytics/docs/web/

Adapted from:
http://github.com/b1tr0t/Google-Analytics-for-Mobile--python-/blob/master/ga.py
https://github.com/singhj/Google-Analytics-for-Mobile--Google-App-Engine/blob/Google-Analytics-for-Mobile--Google-App-Engine/ga.py
"""

import re
import struct
import time

from os import environ
from socket import gethostname
from hashlib import md5
from random import randint
from httplib2 import Http, HttpLib2Error
from urllib import quote
from Cookie import SimpleCookie, CookieError
from messaging import dbgMsg, setDebugging

# Conf

ACCOUNT = "MO-19693661-1"
DOMAIN = 'mp-metrics.phms.com.br'
setDebugging(0)

##

VERSION = "4.4sh"
COOKIE_NAME = "__utmmobile"
COOKIE_PATH = "/"
COOKIE_USER_PERSISTENCE = 63072000

ENVIRON = environ
ENVIRON['HTTP_USER_AGENT'] = "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.12) Gecko/20101027 Ubuntu/10.04 (lucid) Firefox/3.6.12"
ENVIRON['HTTP_ACCEPT_LANGUAGE'] = "pt-br,pt;q=0.8,en-us;q=0.5,en;q=0.3"

def get_ip():
    remote_address = ENVIRON.get("REMOTE_ADDR",'')

    if not remote_address:
        return ""

	dbgMsg("remote_address: %s" % str(remote_address))

    matches = re.match('^([^.]+\.[^.]+\.[^.]+\.).*', remote_address)
    if matches:
        return matches.groups()[0] + "0"
    else:
        return ""


def get_visitor_id():
    usrKey = str(gethostname() + ENVIRON.get('USER'))
    md5String = md5(usrKey).hexdigest()
    return "0x" + md5String[:16]


def get_random_number():
    return str(randint(0, 0x7fffffff))


def parse_cookie(cookie):
    if not cookie:
        return {}

    try:
        c = SimpleCookie()
        c.load(cookie)
    except CookieError:
        # Invalid cookie
        return {}

    cookiedict = {}
    for key in c.keys():
        cookiedict[key] = c.get(key).value
    return cookiedict


def get_utme(custom_var):
    # GA CustomVar
    if not custom_var:
        return ""

    utme_k = ""
    utme_v = ""
    aux = ""
    for k, v in custom_var.items():
        utme_k += aux + sanitize(k)
        utme_v += aux + sanitize(v)
        aux = "*"

    dbgMsg("custom_var: " + utme_k + " - " + utme_v)
    return ("8(" + utme_k + ")9(" + utme_v + ")")


def send_request_to_google_analytics(utm_url):
    # Make a tracking request to Google Analytics from this server.
    # Copies the headers from the original request to the new one.

    http = Http()
    try:
        http.request(utm_url, "GET", headers = {
            'User-Agent': ENVIRON.get('HTTP_USER_AGENT', 'Unknown'),
            'Accepts-Language:': ENVIRON.get('HTTP_ACCEPT_LANGUAGE','')
        })
        dbgMsg("success")

    except HttpLib2Error:
        raise Exception("Error opening: %s" % utm_url)

def sanitize(text):
  if text and isinstance(text, str):
    text = re.sub("[^\w\s\-]", "_", text)
    text = re.sub("_+", "_", text)
    return text

  return ""


def track_page_view(path, title, custom_var):
    # Track a page view and makes a server side request to Google Analytics and writes the transparent
    # gif byte data to the response.

    time_tup = time.localtime(time.time() + COOKIE_USER_PERSISTENCE)

    document_referer = "-"
    document_path = path
    account = ACCOUNT
    domain = DOMAIN

    visitor_id = get_visitor_id()

    # // Always try and add the cookie to the response.
    cookie = SimpleCookie()
    cookie[COOKIE_NAME] = visitor_id
    morsel = cookie[COOKIE_NAME]
    morsel['expires'] = time.strftime('%a, %d-%b-%Y %H:%M:%S %Z', time_tup)
    morsel['path'] = COOKIE_PATH

    utm_gif_location = "http://www.google-analytics.com/__utm.gif"

    utm_url = utm_gif_location + "?" + \
            "utmwv=" + VERSION + \
            "&utmn=" + get_random_number() + \
            "&utmhn=" + quote(domain) + \
            "&utme=" + get_utme(custom_var) + \
            "&utmdt=" + quote(title) + \
            "&utmr=" + quote(document_referer) + \
            "&utmp=" + quote(document_path) + \
            "&utmac=" + account + \
            "&utmcc=__utma%3D999.999.999.999.999.1%3B" + \
            "&utmvid=" + visitor_id + \
            "&utmip=" + get_ip()

    send_request_to_google_analytics(utm_url)
    dbgMsg("utm_url: " + utm_url)
