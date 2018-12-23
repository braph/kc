#!/usr/bin/python3

import re
import sys
import requests
import argparse
from queue import Queue
from lxml import html, etree
from threading import Thread
from html2text import html2text

domain    = ''.join([chr(ord(_) - 38) for _ in 'qunringtTtkz'])
base_url  = 'https://' + domain
board_url = lambda board: '%s/%s/' % (base_url, board)

# === Helper Functions
def err(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)

class SimpleThreadedFunc():
    def __init__(self, num_threads, func):
        self.results = Queue()
        self.threads = Queue(num_threads)

        def thread_func(*args, **kwargs):
            try:        self.results.put(func(*args, **kwargs))
            finally:    self.threads.get()

        def thread_func_start(*args, **kwargs):
            thr = Thread(target=thread_func, args=args, kwargs=kwargs)
            self.threads.put(thr)
            thr.start()

        self.threaded_func = thread_func_start

    def start(self, *args, **kwargs):
        self.threaded_func(*args, **kwargs)

    def yield_results(self, background_thread=None):
        if background_thread:
            background_thread_is_alive = lambda: background_thread.is_alive()
        else:
            background_thread_is_alive = lambda: False

        while True:
            try:   yield self.results.get(True, 1)
            except GeneratorExit: return
            except Exception:     pass

            if not background_thread_is_alive() and self.threads.qsize() == 0:
                break

        while True:
            try:   yield self.results.get_nowait()
            except GeneratorExit: return
            except Exception:     break

def get_tree(url):
    result = requests.get(url)
    return html.fromstring(result.content)

def grep_numbers(s):
    return re.findall('\d+', s)[0]

def get_threads_on_board(url):
    err(url)

    tree = get_tree(url)
    num_pages = get_max_page(tree)

    yield from parse_threads_on_page(tree)

    threadedFunc = SimpleThreadedFunc(30, get_threads_on_page)

    def bg_thread():
        for page in range(2, num_pages + 1):
            next_url = "%s/%d.html" % (url, page)
            threadedFunc.start(next_url)

    bg_thr = Thread(target=bg_thread)
    bg_thr.start()

    for r in threadedFunc.yield_results(bg_thr):
        yield from r

def get_max_page(tree):
    nums = []
    div_pages = tree.xpath('//div[@class = "pages"]')[0]
    for a in div_pages.xpath('.//a'):
        try:    nums.append(int(a.text_content().strip()))
        except: pass
    nums.sort()
    try:    return nums[-1]
    except: return 0

def get_threads_on_page(url):
    tree = get_tree(url)
    return parse_threads_on_page(tree)

def parse_threads_on_page(tree):
    ''' Parse threads on an lxml-Element '''

    def parse_fileinfos(fileinfo_divs):
        for fileinfo_div in fileinfo_divs:
            f = {}

            if fileinfo_div.xpath('.//img[contains(@class, "deleted")]'):
                continue
            
            try:
                f['src'] = fileinfo_div.xpath('.//a[@class = "filelink"]')[0].attrib['href']
            except Exception as e:
                err('src-error:', etree.tostring(fileinfo_div))

            a_postfilename = fileinfo_div.xpath('.//a[@class = "postfilename"]')[0]

            f['title'] = a_postfilename.text_content()
            f['title_truncated'] = f['title']

            try:
                f['title'] = a_postfilename.attrib['title']
            except:
                pass

            f['size'] = fileinfo_div.xpath('.//span[@class = "unimportant"]')[0].text_content()
            f['thumb'] = fileinfo_div.xpath('.//img[@class = "post-image"]')[0].attrib['src']

            yield f

    def xyz():
        pass

    def parse_post(div):
        p = {}
        p['name'] = div.xpath('.//span[@class = "name"]')[0].text_content()
        p['time'] = div.xpath('.//time')[0].attrib['datetime']
        #p['body'] = div.xpath('.//div[@class = "body"]')[0].text_content().decode('UTF-8')
        p['body_html'] = etree.tostring(div.xpath('.//div[@class = "body"]')[0]).decode('UTF-8')
        p['body'] = html2text(p['body_html'])
        p['id'] =   grep_numbers(div.attrib['id'])

        try:
            _ = div.xpath('.//span[@class = "sage"]')[0]
            p['sage'] = _.text_content()
        except:
            p['sage'] = ''

        try:
            _ = div.xpath('.//span[@class = "subject"]')[0]
            p['subject'] = _.text_content()
        except:
            p['subject'] = ''

        files_div = div.xpath('.//div[@class = "files"]')[0]
        fileinfo_divs = files_div.xpath('.//div[@class = "file"]')
        p['files'] = list(parse_fileinfos(fileinfo_divs))
        return p

    def parse_div(div):
        r = {}

        div_post_op = div.xpath('.//div[@class = "post op"]')[0]
        r['post_op'] = parse_post(div_post_op)

        r['replies'] = []
        reply_divs = div.xpath('.//div[@class = "post reply"]')
        for reply_div in reply_divs:
            r['replies'].append( parse_post(reply_div) )

        return r

    threads = tree.xpath('//div[@class = "thread"]')
    for thread in threads:
        yield parse_div(thread)
