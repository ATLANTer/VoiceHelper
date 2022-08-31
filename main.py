#!-*- coding: utf-8 -*-

import COVID19Py
import telebot
import uuid
import os
import requests
from bs4 import BeautifulSoup
import speech_recognition as sr
from config import *
TEMP = ".\\temp"
bot = telebot.TeleBot(TOKEN)
SR = sr.Recognizer()
start_flag = False
language = "ru_RU"
users_data = dict()
country = "Россия"
countries = {'Китай': 'CN', 'Россия': 'RU',
             'США': 'US', 'Германия': 'DE',
             'Франция': 'FR', 'Англия': 'EN',
             'Беларусь': 'BY', 'Казахстан': 'KZ',
             'Украина': 'UA', 'Армения': 'AM'}


def data_pars(text):
    headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.85 Safari/537.36"}
    url = f"https://www.google.com/search?q={text.replace(' ', '+')}"
    get_resp = requests.get(url=url, headers=headers)
    if get_resp.status_code == 200:
        soup = BeautifulSoup(get_resp.text, "lxml")
        need_divs = soup.find_all('div', class_='yuRUbf')
        hrefs = list()
        for div in need_divs:
            hrefs.append(div.find('a').get('href'))
        return hrefs

    else:
        return []


def text_handler(text, chid):
    if 'Коронавир' in text or 'коронавир' in text:
        covid19 = COVID19Py.COVID19()
        country_id = countries.get(users_data[chid][1], False)
        if country_id:
            location = covid19.getLocationByCountryCode(country_id)
            date = location[0]['last_updated'].split("T")
            time = date[1].split(".")
            final_message = f"<u>Данные по стране:</u>\nНаселение: {location[0]['country_population']:,}\n" \
                            f"Последнее обновление: {date[0]} {time[0]}\nПоследние данные:\n<b>" \
                            f"Заболевших: </b>{location[0]['latest']['confirmed']:,}\n<b>Сметрей: </b>" \
                            f"{location[0]['latest']['deaths']:,}"
            bot.send_message(chid, final_message, parse_mode='html')
        else:
            cnts = ' '.join(countries.keys())
            bot.send_message(chid, f"Укажите корректную страну.\nСписок поддерживаемых стран:\n{cnts}")
    else:
        refs = data_pars(text)
        refs_txt = '\n'.join(refs)
        bot.send_message(chid, f"По вашему запросу найдены следующие результаты: {refs_txt}")


@bot.message_handler(commands=["start"])
def bot_start(message):
    global users_data
    global start_flag
    start_flag = True
    username = message.from_user.username
    chat_id = message.from_user.id
    users_data[chat_id] = [username, country]
    bot.send_message(chat_id, f"Привет {username}! Меня зовут Дыня, я твой бот-помощник. Как я могу тебе помочь?\n\
Чтобы узнать обо мне получше набери /help")


@bot.message_handler(commands=["help"])
def bot_help(message):
    if users_data.get(message.from_user.id, False):
        bot.send_message(message.from_user.id, "Данный бот может многое:\n"
                                               "-Распознавание речи пользователя\n"
                                               "-Подбор поисковых запросов на вопросы пользователя "
                                               "(в том числе курс валюты, погода в каком то регионе и т.д.)\n"
                                               "-Предоставление данных о коронавирусе в регионе по голосовому запросу\n"
                                               "-Запоминание имени пользователя с его местоположением "
                                               "и возможность поменять эти данные\n\n"
                                               "Команды используемые ботом:\n"
                                               "/info вывод информации о пользователе\n"
                                               "/name изменить имя\n"
                                               "/country изменить регион")
    else:
        bot.send_message(message.from_user.id, "Введите /start")


@bot.message_handler(commands=["info"])
def user_info(message):
    if users_data.get(message.from_user.id, False):
        chid = message.from_user.id
        nickname = users_data[chid][0]
        countr = users_data[chid][1]
        bot.send_message(message.from_user.id, f"Имя пользователя: {nickname}\nСтрана пользователя: {countr}")
    else:
        bot.send_message(message.from_user.id, "Введите /start")


@bot.message_handler(commands=["name"])
def name_change(message):
    global users_data
    if users_data.get(message.from_user.id, False):
        chid = message.from_user.id
        data = message.text.split()
        if len(data) > 1:
            new_name = data[1]
            users_data[message.from_user.id][0] = new_name
            bot.send_message(chid, "Имя успешно изменено")
        else:
            bot.send_message(chid, "Используйте конструкцию [ /name ваше_новое_имя ]")
    else:
        bot.send_message(message.from_user.id, "Введите /start")


@bot.message_handler(commands=["country"])
def country_change(message):
    global users_data
    if users_data.get(message.from_user.id, False):
        chid = message.from_user.id
        data = message.text.split()
        if len(data) > 1:
            new_country = data[1]
            users_data[message.from_user.id][1] = new_country
            bot.send_message(chid, "Регион успешно изменён")
        else:
            bot.send_message(chid, "Используйте конструкцию [ /country ваше_новый регион ]")
    else:
        bot.send_message(message.from_user.id, "Введите /start")


@bot.message_handler(content_types=['voice'])
def receive_voice(message):
    if users_data.get(message.from_user.id, False):
        fname = str(uuid.uuid4())
        fpath_ogg = os.path.join(TEMP, fname) + ".ogg"
        fpath_wav = os.path.join(TEMP, fname) + ".wav"
        print(fpath_wav)
        download_file = bot.download_file(bot.get_file(message.voice.file_id).file_path)
        with open(fpath_ogg, 'wb') as fout:
            fout.write(download_file)
        os.system("ffmpeg\\bin\\ffmpeg.exe -i " + fpath_ogg + "  " + fpath_wav)
        r_text = recognize(fpath_wav)

        # print(download_file)
        if r_text:
            # bot.send_voice(message.from_user.id, download_file)
            bot.reply_to(message, r_text)
            text_handler(r_text, message.from_user.id)
        else:
            bot.send_message(message.from_user.id, "Извините, я вас не понял")

        clean(fpath_wav, fpath_ogg)
    else:
        bot.send_message(message.from_user.id, "Введите /start")


@bot.message_handler(content_types=["text"])
def receive_text(message):
    if users_data.get(message.from_user.id, False):
        text_handler(message.text, message.from_user.id)
    else:
        bot.send_message(message.from_user.id, "Введите /start")


@bot.message_handler(content_types=["sticker", "pinned_message", "photo", "audio"])
def poslat(message):
    if users_data.get(message.from_user.id, False):
        bot.send_message(message.from_user.id, "Я вас не понимаю. Пожалуйста,\
                                                используйте текстовые или голосовые сообщения")
    else:
        bot.send_message(message.from_user.id, "Введите /start")


def clean(*files):
    for fpath in files:
        os.remove(fpath)


def recognize(fpath):
    with sr.AudioFile(fpath) as src:
        try:
            audio_text = SR.listen(src)
            text = SR.recognize_google(audio_text, language=language)
            return text
        except Exception as ex:
            print(ex)
            return ""


def main():
    if not os.path.exists(TEMP):
        os.mkdir(TEMP)

    bot.polling(timeout=5)


if __name__ == "__main__":
    main()
