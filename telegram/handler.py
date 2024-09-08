import pika
import telegram
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters
)

import json
import os
from dotenv import load_dotenv
import asyncio
import base64

import srt_preview
import neofic

import logging
logging.basicConfig(level=logging.INFO)

load_dotenv()

def get_metadata(file_path: str):
    with open(file_path, 'r') as file:
        return json.load(file)


def set_metadata(file_path: str, value: dict):
    with open(file_path, 'w') as file:
        json.dump(value, file)


def get_chat_metadata(chat_id):
    return get_metadata(f'./temp/{chat_id}/metadata.json')



def set_chat_metadata(chat_id, value):
    set_metadata(f'./temp/{chat_id}/metadata.json', value)

API_KEY = os.getenv('API_KEY')

bot = telegram.Bot(API_KEY)

credentials = pika.PlainCredentials('user', 'password')
connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq-server', credentials=credentials))
#connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))

channel = connection.channel()

channel.queue_declare(queue='asr_to_handler')
channel.queue_declare(queue='telegram_text_upload')

asr_caption = '''
Так как вы выбрали ручной режим, вы получаете предварительный отчет диаризации.
Внимательно ознакомьтесь с текстом и когда будете готовы определить имена спикеров нажмите на подсказку "Продолжить".
'''

loop = asyncio.get_event_loop()

def asr_callback(ch, method, properties, body):
    data = json.loads(body)

    metadata = get_chat_metadata(data['chat_id'])
    metadata['num_speakers'] = data['unique_speakers']
    metadata['cur_speaker'] = 0
    set_chat_metadata(data['chat_id'], metadata)

    with open(f"./temp/{data['chat_id']}/speakers.srt", 'wb') as srt_file:
        srt_file.write(base64.b64decode(data['srt_file']))

        pdf_file_path = srt_preview.create_pdf(f"./temp/{data['chat_id']}/speakers.srt")
        loop.run_until_complete(bot.send_document(data['chat_id'], pdf_file_path, caption=asr_caption, reply_markup=ReplyKeyboardMarkup([['Продолжить']], one_time_keyboard=True, resize_keyboard=True)),)
        

def llm_callback(ch, method, properties, body):
    data = json.loads(body)

    pdf_filepath = neofic.create_pdf(data)
    loop.run_until_complete(bot.send_document(data['chat_id'], pdf_filepath, caption='Держи!'))

channel.basic_consume(queue='telegram_text_upload', auto_ack=True, on_message_callback=llm_callback)
channel.basic_consume(queue='asr_to_handler', auto_ack=True, on_message_callback=asr_callback)
channel.start_consuming()