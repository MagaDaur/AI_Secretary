import pika
import telegram
import json
import os
from dotenv import load_dotenv
import asyncio

import logging
logging.basicConfig(level=logging.INFO)

load_dotenv()

API_KEY = os.getenv('API_KEY')

bot = telegram.Bot(API_KEY)

credentials = pika.PlainCredentials('user', 'password')
connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq-server', credentials=credentials))

channel = connection.channel()

channel.queue_declare(queue='telegram_text_upload')

def llm_callback(channel, method, properties, body):
    global bot
    logging.info("LLM Callback worked!")

    data = json.loads(body)
    
    # Сомнительно, но окэй
    asyncio.run(bot.send_message(data['chat_id'], '\n'.join(data['transcribed_text'])))

channel.basic_consume(queue='telegram_text_upload', auto_ack=True, on_message_callback=llm_callback)
channel.start_consuming()