import aio_pika
import telegram
from telegram import (
    ReplyKeyboardMarkup,
)

from local_lib import (
    get_chat_metadata,
    set_chat_metadata,
    fix_llm_respond
)

import json
import os

import asyncio
import base64

# import srt_preview
import neofic
import ofic

from shutil import (
    rmtree as RemoveDirectory
)

import logging
logging.basicConfig(level=logging.INFO)

API_KEY = os.getenv('API_KEY')
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')
RABBITMQ_LOGIN = os.getenv('RABBITMQ_DEFAULT_USER')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_DEFAULT_PASS')
TELEGRAM_HOST = os.getenv('TELEGRAM_HOST')

bot = telegram.Bot(API_KEY, base_url=f'http://{TELEGRAM_HOST}:8081/bot', local_mode=True)

asr_caption = '''
Так как вы выбрали ручной режим, вам нужно заполнить имена спикеров на основе фрагментов их голосов.
'''

async def asr_callback(message):
    async with message.process():
        data = json.loads(message.body)

        with open(f'./temp/{data['chat_id']}/speakers.srt', 'wb') as srt_file:
            srt_file.write(base64.b64decode(data['srt_file']))

        await bot.send_message(data['chat_id'], text=asr_caption, reply_markup=ReplyKeyboardMarkup([['Продолжить']], one_time_keyboard=True, resize_keyboard=True))
            
        metadata = get_chat_metadata(data['chat_id'])
        metadata['num_speakers'] = data['unique_speakers']
        metadata['cur_speaker'] = 0
        set_chat_metadata(data['chat_id'], metadata)

async def llm_callback(message):
    async with message.process():
        data = json.loads(message.body)
        metadata = get_chat_metadata(data['chat_id'])

        llm_response = fix_llm_respond(data['transcribed_text'])
        
        ofic_path = f'./temp/{data["chat_id"]}/ofic.pdf'
        ofic.create_pdf(llm_response, ofic_path, metadata.get('password'))
        with open(ofic_path, 'rb') as ofic_pdf:
            await bot.send_document(data['chat_id'], ofic_pdf, caption='Официальный PDF Отчет', filename='Протокол.pdf')

        neofic_path = f'./temp/{data["chat_id"]}/neofic.pdf'
        neofic.create_pdf(llm_response, neofic_path, metadata.get('password'))
        with open(neofic_path, 'rb') as neofic_pdf:
            await bot.send_document(data['chat_id'], neofic_pdf, caption='Неофициальный PDF Отчет', filename='Протокол.pdf')

        await bot.send_message(data['chat_id'], 'Спасибо что воспльзовались нашим ботом!', reply_markup=ReplyKeyboardMarkup([['Start']], resize_keyboard=True, one_time_keyboard=True))

        RemoveDirectory(f'./temp/{data['chat_id']}/', ignore_errors=True)

async def main():
    connection = await aio_pika.connect(host=RABBITMQ_HOST, login=RABBITMQ_LOGIN, password=RABBITMQ_PASSWORD, heartbeat=5000)
    channel = await connection.channel()

    await channel.set_qos(10)

    asr_to_handler = await channel.declare_queue('asr_to_handler')
    telegram_text_upload = await channel.declare_queue('telegram_text_upload')

    await telegram_text_upload.consume(llm_callback)
    await asr_to_handler.consume(asr_callback)
    
    await asyncio.Future()

if __name__ == '__main__':
    asyncio.run(main())