#!/usr/bin/python3

import os
import json
import requests
from lxml import html
from html2text import html2text

base_url = 'https://kohlchan.net'
board_url   = base_url + '/%s/'
post_url    = base_url + '/post.php'
captcha_url = base_url + '/inc/lib/captcha/captcha.php'
captcha_solve_url = base_url + '/ip_bypass.php'


user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
cookie_file = '/tmp/kc.cookies'
captcha_file = '/tmp/kc.captcha.jpg'


session = requests.Session()
session.headers.update({'User-Agent': user_agent})
session.cookies.update({'cookieConsent': 'true'})

def loadCookies(storage_file):
    with open(storage_file, 'r') as fh:
        session.cookies.update(json.load(fh))

def storeCookies(storage_file):
    with open(storage_file, 'w') as fh:
        json.dump(dict(session.cookies), fh)

def getTree(url):
    result = session.get(url)
    return html.fromstring(result.content)

def getBoard(board):
    return getTree(board_url % board)

def post(tree, subject='', text='', files=None, password=None):
    form = tree.xpath('//form[@name = "post"]')[0]

    data = {}
    inputs = form.xpath('.//input')
    for inp in inputs:
        try:
            data[inp.name] = inp.attrib['value']
        except Exception as e:
            pass #print(e, inp.attrib)

    files_data = {}
    if files:
        for f, fkey in zip(files, ['file', 'file2', 'file3', 'file4']):
            files_data[fkey] = open(f, 'rb')

    data['json_response'] = 1
    data['subject'] = subject
    data['body']    = text
    if password:
        data['password'] = password

    #print(data)
    #print(data.keys())
    #print(files_data)

    result = session.post(post_url, data=data, files=files_data)
    #print(result)
    #print(result.text)

    try:
        json_result = json.loads(result.text)
        if 'ip_bypass' in json_result['error']:
            print('must solve a captcha ')
            if not solveCaptcha():
                print('nope!')
                return False
        elif 'redirect' in json_result:
            return json_result['redirect']
    except:
        pass

    result = session.post(post_url, data=data, files=files_data)
    print(result)
    print(result.text)


def solveCaptcha(max_tries=3):
    result = session.get(captcha_url)
    with open(captcha_file, 'wb') as fh:
        fh.write(result.content)
    os.system("feh '%s' &" % captcha_file)

    while True:
        code = input('Captcha: ')
        if code:
            break

    data = dict(captcha_code=code)
    result = session.post(captcha_solve_url, data=data)
    print(result)
    print(result.text)

    if 'Try again' in result.text:
        if max_tries > 1:
            return solveCaptcha(max_tries - 1)
        else:
            return False

    return True
