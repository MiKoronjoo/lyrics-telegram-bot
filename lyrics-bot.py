import time
import requests
import os

import telepot
from telepot.loop import MessageLoop

from config import *
from consts import *


def search(music_name):
    music_name = music_name.replace(' ', '+')
    link = 'https://www.google.com/search?q=site:%s+%s' % (base_link, music_name)
    print(link)
    source = requests.get(link).text
    first_index = source.find(href) + len(href)
    assert first_index != len(href) - 1
    last_index = source.find('&', first_index)
    page_link = source[first_index:last_index]
    return page_link


def scrap_lyrics(page_link):
    os.system('wget --output-document=lyrics_bot ' + page_link)
    source = open('lyrics_bot').read()
    first_index = source.find(left_pivot) + len(left_pivot)
    last_index = source.find(right_pivot, first_index)
    lyrics_text = source[first_index:last_index].replace('\\n', '\n').replace('\\"', '"')
    return lyrics_text


def get_info(page_link):
    # a = page_link[::-1].find('/')
    # a = page_link[::-1].find('/', a + 1)
    # sp = len(page_link) - a
    if 'https://www.musixmatch.com/de/songtext/' in page_link:
        sp = len('https://www.musixmatch.com/de/songtext/')

    else:
        sp = len('https://www.musixmatch.com/lyrics/')

    artist, music = page_link[sp:].replace('-', ' ').split('/')[:2]
    return artist, music


def handler(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    linked_str = '[%s](tg://user?id=%d)' % (msg['first_name'], msg['from']['id'])
    if content_type == 'text' and chat_type == u'private':
        if msg['text'] == '/start':
            bot.sendMessage(chat_id, 'Welcome')
            if log_id:
                bot.sendMessage(log_id, 'New user: ' + linked_str, 'Markdown')

        else:
            artist, music = None, None
            try:
                page_link = search(msg['text'])
                artist, music = get_info(page_link)
                lyrics_text = scrap_lyrics(page_link)

                bot.sendMessage(chat_id, template % (artist, music, lyrics_text), 'Markdown')

            except AssertionError:
                bot.sendMessage(chat_id, 'Music not found!')

            except Exception as ex:
                bot.sendMessage(chat_id, 'Music not found!')
                if log_id:
                    bot.sendMessage(log_id, '```%s```' % str(ex), 'Markdown')

            if log_id:
                bot.sendMessage(log_id, log_template % (linked_str, msg['text'], artist, music), 'Markdown')


if __name__ == '__main__':
    bot = telepot.Bot(TOKEN)
    MessageLoop(bot, handler).run_as_thread()

    while True:
        time.sleep(30)
