import pika
import telegram
from telegram import (
    ReplyKeyboardMarkup,
)

from lib import (
    get_chat_metadata,
    set_chat_metadata,
)

import json
import os

import asyncio
import base64

import srt_preview
import neofic

API_KEY = os.getenv('API_KEY')
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')

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

        with telegram.Bot(API_KEY, local_mode=True) as bot:
            loop.run_until_complete(bot.send_document(data['chat_id'], pdf_file_path, caption=asr_caption, reply_markup=ReplyKeyboardMarkup([['Продолжить']], one_time_keyboard=True, resize_keyboard=True)),)
        

def llm_callback(ch, method, properties, body):
    data = json.loads(body)

    pdf_filepath = neofic.create_pdf(data)
    with telegram.Bot(API_KEY, local_mode=True) as bot:
        loop.run_until_complete(bot.send_document(data['chat_id'], pdf_filepath, caption='Держи!'))

    

if __name__ == '__main__':
    credentials = pika.PlainCredentials('user', 'password')
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials))
    channel = connection.channel()

    channel.queue_declare(queue='asr_to_handler')
    channel.queue_declare(queue='telegram_text_upload')

    channel.basic_consume(queue='telegram_text_upload', auto_ack=True, on_message_callback=llm_callback)
    channel.basic_consume(queue='asr_to_handler', auto_ack=True, on_message_callback=asr_callback)
    channel.start_consuming()