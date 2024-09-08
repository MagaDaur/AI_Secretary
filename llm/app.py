from os import getenv

import json
import requests

import pika
from dotenv import load_dotenv
from pika.adapters.blocking_connection import BlockingChannel

from prompts import PROMPTS, Prompt

import logging

logging.basicConfig(level=logging.INFO)

load_dotenv()

IAM_TOKEN = getenv('IAM_TOKEN')

url = 'https://llm.api.cloud.yandex.net/foundationModels/v1/completion'
headers = {
    'Authorization': f'Bearer {IAM_TOKEN}',
    'Content-Type': 'application/json'
}

credentials = pika.PlainCredentials('user', 'password')
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='rabbitmq-server', credentials=credentials, heartbeat=1800))
channel = connection.channel()

channel.queue_declare(queue='transcribed_text_upload')


def request_chunking(request_str, chunk_size=3500):
    return [request_str[i:i + chunk_size] for i in range(0, len(request_str), chunk_size)]


def callback(ch: BlockingChannel, method, properties, body):
    logging.info("GPT GENERATION")
    data = json.loads(body)
    answers = []

    for prompt_components in PROMPTS:
        prompt_chuncks = request_chunking(data['transcribed_text'])
        chunck_response_list = []

        for chunk in prompt_chuncks:
            # prompt = Prompt(
            #     llm_instructions=prompt_components["llm_instructions"],
            #     context=data['transcribed_text'],
            #     question=prompt_components["question"]
            # )

            request_data = {
                "modelUri": "gpt://b1g72uajlds114mlufqi/yandexgpt/latest",
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
            # logging.info(f"Text length: {len(prompt.prompt)}")
            response = requests.post(url, headers=headers, json=request_data)

            if response.status_code == 200:
                response_text = response.json()['result']['alternatives'][0]['message']['text']
                logging.info(response_text)

                try:
                    json_list = json.loads(response_text.replace("'", '"'))
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
    channel.basic_publish('', 'telegram_text_upload', json.dumps(body))


if __name__ == "__main__":
    channel.basic_consume(queue='transcribed_text_upload', auto_ack=True, on_message_callback=callback)

    channel.start_consuming()
