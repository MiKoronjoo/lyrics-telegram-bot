import time
import requests
import os

import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineQueryResultArticle, InputTextMessageContent, ChosenInlineResult, Update, \
    InlineKeyboardMarkup, InlineKeyboardButton

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


def on_chat_message(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    linked_str = '[%s](tg://user?id=%d)' % (msg['from']['first_name'], msg['from']['id'])
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
                message = template % (artist, music, lyrics_text)
                if len(message) > 4096:
                    file_name = music + '_LyrixRobot.txt'
                    file = open(file_name, 'w')
                    file.write(lyrics_text)
                    file.close()
                    bot.sendDocument(chat_id, open(file_name), caption_template % (artist, music), 'Markdown')
                    os.system('rm "%s"' % file_name)

                else:
                    bot.sendMessage(chat_id, message, 'Markdown')

            except AssertionError:
                bot.sendMessage(chat_id, 'Music not found!')

            except Exception as ex:
                bot.sendMessage(chat_id, 'Music not found!')
                if log_id:
                    bot.sendMessage(log_id, '```%s```' % str(ex), 'Markdown')

            if log_id:
                bot.sendMessage(log_id, log_template % (linked_str, msg['text'], artist, music), 'Markdown')


def on_inline_query(msg):
    query_id, from_id, query_string = telepot.glance(msg, flavor='inline_query')
    if not query_string:
        return

    artist, music = '', 'Music not found!'
    page_link = ''
    try:
        page_link = search(query_string)
        artist, music = get_info(page_link)
        result = '*%s*\n*%s*' % (artist, music)

    except AssertionError:
        result = 'Music not found!'

    except Exception as ex:
        result = 'Music not found!'
        if log_id:
            bot.sendMessage(log_id, '```%s```' % str(ex), 'Markdown')

    articles = [
        InlineQueryResultArticle(
            id='R1',
            title=music,
            input_message_content=InputTextMessageContent(
                message_text=result,
                parse_mode='Markdown'
            ),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text='Show lyrics', callback_data=page_link)]]
            ),
            description=artist
        )
    ]
    bot.answerInlineQuery(query_id, articles)


def on_callback_query(msg):
    query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
    if query_data:
        lyrics_text = scrap_lyrics(query_data)
        # message = template % ('artist', 'music', lyrics_text)
        # if len(message) > 4096:
        #     file_name = 'music' + '_LyrixRobot.txt'
        #     file = open(file_name, 'w')
        #     file.write(lyrics_text)
        #     file.close()
        #     bot.sendDocument(chat_id, open(file_name), caption_template % (artist, music), 'Markdown')
        #     os.system('rm "%s"' % file_name)
        #
        # else:
        #     bot.sendMessage(chat_id, message, 'Markdown')
        #
        bot.editMessageText(msg['inline_message_id'], lyrics_text[:4096])


def on_chosen_inline_result(msg):
    result_id, from_id, query_string = telepot.glance(msg, flavor='chosen_inline_result')
    print('Chosen Inline Result:', result_id, from_id, query_string)


if __name__ == '__main__':
    bot = telepot.Bot(TOKEN)
    MessageLoop(bot, {'chat': on_chat_message,
                      'inline_query': on_inline_query,
                      'callback_query': on_callback_query,
                      'chosen_inline_result': on_chosen_inline_result}).run_as_thread()

    while True:
        time.sleep(30)
