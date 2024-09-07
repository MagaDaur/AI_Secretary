import os

import pika
from pika.adapters.blocking_connection import BlockingChannel
import json
import base64

from pedalboard import *
import noisereduce as nr
import audio2numpy as a2n
from pedalboard.io import AudioFile

from model import asr_pipe

audiofile_formats = (".mp3", ".wav", ".ogg", ".oga")

credentials = pika.PlainCredentials('user', 'password')
connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq-server', credentials=credentials, heartbeat=5000))
channel = connection.channel()

channel.queue_declare(queue='audio_upload')


def get_audio_sample(path):
    x, sr = a2n.audio_from_file(path)

    return dict({
        'path': path,
        'array': x,
        'sampling_rate': sr
    })


def delete_noise(upload_directory):
    audio_files = [file for file in os.listdir(upload_directory) if file.endswith(audiofile_formats)]

    for audio_name in audio_files:
        print(audio_name)

        x, sr = a2n.audio_from_file(upload_directory + audio_name)
        with AudioFile(upload_directory + audio_name).resampled_to(sr) as f:
            audio = f.read(f.frames)

        reduced_noise = nr.reduce_noise(y=audio, sr=sr, stationary=True, prop_decrease=1.0)

        board = Pedalboard([
            NoiseGate(threshold_db=-30, ratio=3, release_ms=250),
            Compressor(threshold_db=-16, ratio=2.5),
            LowShelfFilter(cutoff_frequency_hz=700, gain_db=10, q=1),
            Gain(gain_db=10)
        ])

        effected = board(reduced_noise, sr)

        with AudioFile(upload_directory + audio_name, 'w', sr,
                       effected.shape[0]) as f:
            f.write(effected)


def clear_upload_directory(upload_directory):
    audio_files = [file for file in os.listdir(upload_directory) if file.endswith(audiofile_formats)]

    for audio in audio_files:
        file_path = upload_directory + audio
        os.remove(file_path)


def transcribe_audio(upload_directory):
    transcribed_text = ""
    delete_noise(upload_directory)

    audio_files = [file for file in os.listdir(upload_directory) if file.endswith(audiofile_formats)]

    for audio in audio_files:
        transcribed_text = asr_pipe(inputs=upload_directory + audio)['text']

    clear_upload_directory(upload_directory)
    return transcribed_text


def callback(ch: BlockingChannel, method, properties, body):
    ch.basic_ack(delivery_tag=method.delivery_tag)
    data = json.loads(body)
    file_name = data["audio"]["filename"]

    with open(f"./uploaded_files/{file_name}", 'wb') as tfile:
        tfile.write(base64.b64decode(data["audio"]['buffer']))

    transcribed_text = transcribe_audio("uploaded_files/")

    body = {
        'chat_id': data['chat_id'],
        'file_name': file_name,
        'transcribed_text': transcribed_text
    }

    channel.basic_publish('', 'transcribed_text_upload', json.dumps(body))


if __name__ == "__main__":
    channel.basic_consume(queue='audio_upload', on_message_callback=callback)

    channel.start_consuming()
