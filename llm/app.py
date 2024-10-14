from os import getenv

import time
import json
import requests

import asyncio
import aio_pika
from aio_pika import Message
from dotenv import load_dotenv

from prompts import PROMPTS, Prompt

import logging

logging.basicConfig(level=logging.INFO)

load_dotenv()

IAM_TOKEN = getenv('IAM_TOKEN')
RABBITMQ_HOST = getenv('RABBITMQ_HOST')
RABBITMQ_LOGIN = getenv('RABBITMQ_DEFAULT_USER')
RABBITMQ_PASSWORD = getenv('RABBITMQ_DEFAULT_PASS')

url = 'https://llm.api.cloud.yandex.net/foundationModels/v1/completion'
headers = {
    'Authorization': f'Bearer {IAM_TOKEN}',
    'Content-Type': 'application/json'
}

def request_chunking(request_str, chunk_size=4_000):
    return [request_str[i:i + chunk_size] for i in range(0, len(request_str), chunk_size)]


async def callback(message):
    async with message.process():
        logging.info("GPT GENERATION")
        data = json.loads(message.body)
        answers = []

        for prompt_components in PROMPTS:
            chunks = data['transcribed_text']
            chunck_response_list = []

            for chunk in chunks:
                request_data = {
                    "modelUri": "gpt://b1glrfrec5q420bjhi7n/yandexgpt/latest",
                    "completionOptions": {
                        "stream": False,
                        "temperature": 0.1,
                        "maxTokens": 20000
                    },
                    "messages": [
                        {
                            "role": "system",
                            "text": f"{prompt_components['llm_instructions']}"
                        },
                        {
                            "role": "user",
                            "text": f"{prompt_components['question'] + ' ' + chunk}"
                        }
                    ]
                }

                response = requests.post(url, headers=headers, json=request_data)

                if response.status_code == 200:
                    response_text = response.json()['result']['alternatives'][0]['message']['text']
                    logging.info(response_text)

                    try:
                        json_list = json.loads(response_text)
                    except json.decoder.JSONDecodeError as e:
                        logging.info(f"json.decoder.JSONDecodeError: \n{response_text}")
                        json_list = []
                    chunck_response_list += json_list
                else:
                    logging.info(response.status_code)
                    logging.info(response.json())

            answers.append(chunck_response_list)

        body = {
            'chat_id': data['chat_id'],
            'file_name': data['file_name'],
            'transcribed_text': answers
        }
        logging.info(answers)
        logging.info("END OF GPT GENERATION")
        await channel.default_exchange.publish(Message(json.dumps(body).encode()), 'telegram_text_upload')

async def main():
    global channel

    connection = await aio_pika.connect(host=RABBITMQ_HOST, login=RABBITMQ_LOGIN, password=RABBITMQ_PASSWORD, heartbeat=5000)
    async with connection:
        channel = await connection.channel()

        await channel.set_qos(10)

        telegram_text_upload = await channel.declare_queue('telegram_text_upload')
        transcribed_text_upload = await channel.declare_queue('transcribed_text_upload')

        await transcribed_text_upload.consume(callback)

        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())