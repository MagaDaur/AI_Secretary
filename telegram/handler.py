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

import logging
logging.basicConfig(level=logging.INFO)

load_dotenv()

API_KEY = os.getenv('API_KEY')

bot = telegram.Bot(API_KEY)

credentials = pika.PlainCredentials('user', 'password')
connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq-server', credentials=credentials))
#connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))

channel = connection.channel()

channel.queue_declare(queue='asr_to_handler')
channel.queue_declare(queue='llm_to_handler')

asr_caption = '''
Так как вы выбрали ручной режим, вы получаете предварительный отчет диаризации.
Внимательно ознакомьтесь с текстом и когда будете готовы определить имена спикеров нажмите на подсказку "Продолжить".
'''

def asr_callback(ch, method, properties, body):
    data = json.loads(body)

    with open(f'./temp/{data['chat_id']}/speakers.srt', 'wb') as srt_file:
        srt_file.write(base64.b64decode(data['srt_file']))

        pdf_file_path = srt_preview.create_pdf(data['chat_id'])

        asyncio.run(bot.send_document(data['chat_id'], pdf_file_path, caption=asr_caption, reply_markup=ReplyKeyboardMarkup([['Продолжить']], one_time_keyboard=True, resize_keyboard=True)))

def llm_callback(ch, method, properties, body):
    data = json.loads(body)
    

channel.basic_consume(queue='asr_to_handler', auto_ack=True, on_message_callback=asr_callback)
channel.start_consuming()