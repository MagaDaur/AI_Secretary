import pika
import telegram
from telegram import (
    ReplyKeyboardMarkup,
)

from local_lib import (
    get_chat_metadata,
    set_chat_metadata,
)

import json
import os

import asyncio
import base64

import srt_preview
import neofic
import neofic_word
import ofic
import db

from shutil import (
    rmtree as RemoveDirectory
)

import logging
logging.basicConfig(level=logging.INFO)

API_KEY = os.getenv('API_KEY')
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')
TELEGRAM_HOST = os.getenv('TELEGRAM_HOST')

bot = telegram.Bot(API_KEY, base_url=f'http://{TELEGRAM_HOST}:8081/bot', local_mode=True)

asr_caption = '''
Так как вы выбрали ручной режим, вы получаете предварительный отчет диаризации.
Внимательно ознакомьтесь с текстом и когда будете готовы определить имена спикеров нажмите на подсказку "Продолжить".
'''

loop = asyncio.get_event_loop()

def asr_callback(ch, method, properties, body):
    data = json.loads(body)
    
    srt_filepath = f"./temp/{data['chat_id']}/speakers.srt"

    with open(srt_filepath, 'wb') as srt_file:
        srt_file.write(base64.b64decode(data['srt_file']))

    pdf_file_path = srt_preview.create_pdf(srt_filepath)
    with open(pdf_file_path, 'rb') as pdf_file:
        loop.run_until_complete(bot.send_document(data['chat_id'], pdf_file, caption=asr_caption, reply_markup=ReplyKeyboardMarkup([['Продолжить']], is_persistent=True, one_time_keyboard=True, resize_keyboard=True)),)
        
    db.add_record_with_files(data['chat_id'], audio_transcription_path=pdf_file_path)

    metadata = get_chat_metadata(data['chat_id'])
    metadata['num_speakers'] = data['unique_speakers']
    metadata['cur_speaker'] = 0
    set_chat_metadata(data['chat_id'], metadata)

def llm_callback(ch, method, properties, body):
    data = json.loads(body)
    metadata = get_chat_metadata(data['chat_id'])

    logging.info(data)

    neofic_pdf_filepath = neofic.create_pdf(data)
    neofic_docx_filepath = neofic_word.create_docx(data)

    # ofic_pdf_filepath = ofic.generate_protocol(data)
    
    with open(neofic_pdf_filepath, 'rb') as pdf_file:
        loop.run_until_complete(bot.send_document(data['chat_id'], pdf_file, caption='Неофицальный PDF отчет.'))
        db.update_record_by_id(metadata['db_uid'], 'informal_protocol', neofic_pdf_filepath)

    with open(neofic_docx_filepath, 'rb') as docx_file:
        loop.run_until_complete(bot.send_document(data['chat_id'], docx_file, caption='Неофицальный DOCX отчет.'))

    # with open(ofic_pdf_filepath, 'rb') as pdf_file:
    #     loop.run_until_complete(bot.send_document(data['chat_id'], pdf_file, caption='Офицальный PDF отчет.'))
    #     db.update_record_by_id(metadata['db_uid'], 'formal_protocol', ofic_pdf_filepath)

    loop.run_until_complete(bot.send_message(data['chat_id'], 'Спасибо что воспльзовались нашим ботом!', reply_markup=ReplyKeyboardMarkup([['Start']], is_persistent=True, resize_keyboard=True, one_time_keyboard=True)))

    RemoveDirectory(f'./temp/{data['chat_id']}/', ignore_errors=True)

if __name__ == '__main__':
    credentials = pika.PlainCredentials('user', 'password')
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials))
    channel = connection.channel()

    channel.queue_declare(queue='asr_to_handler')
    channel.queue_declare(queue='telegram_text_upload')

    channel.basic_consume(queue='telegram_text_upload', auto_ack=True, on_message_callback=llm_callback)
    channel.basic_consume(queue='asr_to_handler', auto_ack=True, on_message_callback=asr_callback)
    channel.start_consuming()