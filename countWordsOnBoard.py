#!/usr/bin/python3

import re
import json
import requests
from html2text import html2text

base_url = 'https://kohlchan.net'
board_url = base_url + '/%s/%d.json'
thread_url = base_url + '/%s/res/%d.json'
catalog_url = base_url + '/%s/catalog.json'

def rEscape(s):
    return re.sub('([\\[\\]\\(\\)])', '\\\\\\1', s)

def sortDictByValue(d):
    return sorted(d.items(), key=lambda i: (i[1], i[0]))

def getWords(text, min_length=3):
    words = re.split('[\\.\\?!/:;,#\*\'\" \n\\(\\)\\[\\]<>]', text)
    return list(filter(lambda x: len(x) >= min_length and not x.isnumeric(), words))

def countWordsInTextFast(words):
    unique_words = set(words)
    words = list(map(lambda s: s.lower(), words))

    word_counts = {}
    seen = []
    for word in unique_words:
        word_lower = word.lower()
        if word_lower in seen:
            continue
        else:
            seen.append(word_lower)
            word_counts[word] = words.count(word_lower)

    return word_counts

def countWordsInTextFast22(words):
    words = list(map(lambda s: s.title(), words))
    unique_words = set(words)

    word_counts = {}
    for word in unique_words:
        word_counts[word] = words.count(word)

    return word_counts

def countWordsInText(words, text):
    word_counts = {}
    word_counts_seen = []
    for word in words:
        if word.lower() in word_counts_seen:
            continue
        else:
            word_counts_seen.append(word.lower())

        try:
            found = re.findall("\\b%s\\b" % rEscape(word), text, re.I)
            word_counts[word] = len(found)
        except Exception as e:
            print(e, word)

    return word_counts

def groupByTenners(word_counts):
    def getK(n):
        return "%d0-%d9" % ( int(n / 10), int(n / 10)  )

    words2 = {}
    for word, count in word_counts:
        k = getK(count)

        if k not in words2:
            words2[k] = []

        words2[k].append(word)
    return words2

def printMappingTenners(words2):
    for count, words in words2.items():
        print("%9s x" % count, ', '.join(words))

def analyze(s):
    #s = removeBrackets(s)
    words = getWords(s)
    words_total = len(words)

    #unique_words = set(words)
    #word_counts = countWordsInText(unique_words, s)
    word_counts = countWordsInTextFast22(words)
    word_counts = sortDictByValue(word_counts)
    return word_counts

    words2 = {}
    for word, count in word_counts:
        if count not in words2:
            words2[count] = []

        words2[count].append(word)

    for count, words in words2.items():
        print("%2s x" % count, ', '.join(words))

    print('Total:', words_total)

def getJson(url):
    result = requests.get(url)
    return json.loads(result.text)

def getBoard(board):
    return getJson(board_url % board)

def getThread(board, thread):
    return getJson(thread_url % (board, thread))

def getCatalog(board):
    return getJson(catalog_url % board)

def getAllThreadsOfBoard(board):
    catalog = getCatalog(board)
    for cata in catalog:
        for thread in cata['threads']:
            try:
                yield getThread('b', thread['no'])
            except Exception as e:
                print(e)

def getAllTheText(listOfThreads):
    allTheText = ''

    for thread in listOfThreads:
        for post in thread['posts']:
            try:
                allTheText += html2text(post['com'])
            except Exception as e:
                print(e, post)

    return allTheText

def analyzeThreadList(listOfThreads):
    allTheText = ''

    for thread in listOfThreads:
        for post in thread['posts']:
            try:
                allTheText += html2text(post['com'])
            except Exception as e:
                print(e, post)

    analyze(allTheText)


#print(getJson(board_url % ('b', 1)))
