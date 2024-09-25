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

from pydub import (
    AudioSegment
)

from local_lib import *

from os import (
    makedirs as CreateDirectory,
    listdir,
    getenv,
)

from shutil import (
    rmtree as RemoveDirectory
)

from subtitle_parser import (
    SrtParser
)

from dotenv import (
    load_dotenv
)

import pika
import base64
import json
import db

from pathlib import Path

import logging
logging.basicConfig(level=logging.INFO)

load_dotenv()

API_KEY = getenv('API_KEY')
TELEGRAM_HOST = getenv('TELEGRAM_HOST')
RABBITMQ_HOST = getenv('RABBITMQ_HOST')

# Стейты диалога в боте

START = 0
PASSWORD = 1
TYPE = 2
SPEAKERS = 3
MAIN_AUDIO = 4
WAIT_REPLY = 5
SPEAKER_NAMES = 6

# Начальное состояние диалога
async def start(update: Update, ctx):
    RemoveDirectory(f'./temp/{update.message.chat_id}/', ignore_errors=True)
    CreateDirectory(f'./temp/{update.message.chat_id}/', exist_ok=True)

    records = db.get_stats_by_chat_id(update.message.chat_id)

    metadata = BASE_METADATA.copy()
    metadata['chat_id'] = update.message.chat_id
    metadata['db_uid'] = 1 if len(records) == 0 else records[-1].id + 1
    set_chat_metadata(update.message.chat_id, metadata)

    keyboard = [['Запуск']]
    

    await update.message.reply_text('Привет я ИИ-Секретарь. Начнём?',
                                    reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True,
                                    resize_keyboard=True, is_persistent=True))

    return START


async def ask_password(update: Update, ctx):
    keydoard = [
        [
            InlineKeyboardButton('Сгенерировать пароль', callback_data='1'),
            InlineKeyboardButton('Без пароля', callback_data='2'),
        ],
    ]
    
    await update.message.reply_text('Введите пароль для файла отчета или выберите иную опцию.',
                                reply_markup=InlineKeyboardMarkup(keydoard))

    return PASSWORD


async def generate_password(update: Update, ctx):
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat.id
    password = create_password(12)

    metadata = get_chat_metadata(chat_id)
    metadata['password'] = password
    set_chat_metadata(chat_id, metadata)

    await query.edit_message_text(f'Отлично\! Ваш пароль: `{password}`', parse_mode='MarkdownV2')

    keyboard = [
        [
            InlineKeyboardButton('Авто', callback_data='1'),
            InlineKeyboardButton('Ручной', callback_data='2')
        ]
    ]
    await query.message.chat.send_message('Теперь выберите тип анализа.', reply_markup=InlineKeyboardMarkup(keyboard))

    return TYPE


async def skip_password(update: Update, ctx):
    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton('Авто', callback_data='1'),
            InlineKeyboardButton('Ручной', callback_data='2')
        ]
    ]
    await query.edit_message_text('Хорошо. Теперь выберите тип анализа.', reply_markup=InlineKeyboardMarkup(keyboard))

    return TYPE


async def set_password(update: Update, ctx):
    metadata = get_chat_metadata(update.message.chat_id)
    metadata['password'] = update.message.text
    set_chat_metadata(update.message.chat_id, metadata)

    await update.message.chat.delete_message(update.message.message_id)

    await update.message.reply_text(f'Отлично\! Ваш пароль: ||{update.message.text}||', parse_mode='MarkdownV2')

    keyboard = [
        [
            InlineKeyboardButton('Авто', callback_data='1'),
            InlineKeyboardButton('Ручной', callback_data='2')
        ]
    ]
    await update.message.reply_text('Теперь выберите тип анализа.', reply_markup=InlineKeyboardMarkup(keyboard))

    return TYPE


auto_instruction = '''
В автоматическом режиме вам необходимо:
1. Отправить примеры голосов спикеров.
    !!ВАЖНО!! - Укажите имя спикера в описании к прилагаемому файлу.
    !!ВАЖНО!! - Если у файлов не будет описания то названия аудио-файлов будут считаться именами спикеров.
2. После загрузки всех аудио-файлов нажать на подсказку "Сохранить выбор".
3. Далее следовать инструкциям.
'''
manual_instruction = '''
В ручном режиме вам необходимо:
1. Отправить аудио-файл который будет проанализован.
2. После обработки, вам придет предварительный отчет, где имена спикеров будут иметь вид "SPEAKER_0".
3. Вручную ввести имена спикеров.
4. Далее следовать инструкциям.
'''


async def get_type(update: Update, ctx):
    query = update.callback_query
    await query.answer()

    metadata = get_chat_metadata(query.message.chat.id)
    metadata['type'] = int(query.data)
    set_chat_metadata(query.message.chat.id, metadata)

    await query.delete_message()

    if query.data == '1':
        await query.message.chat.send_message(auto_instruction, reply_markup=ReplyKeyboardMarkup([['Сохранить выбор']],
                                                                                                 one_time_keyboard=True,
                                                                                                 resize_keyboard=True,
                                                                                                 is_persistent=True))
        return SPEAKERS

    await query.message.chat.send_message(manual_instruction)
    return MAIN_AUDIO


async def get_speakers(update: Update, ctx):
    file_data = update.message.document or update.message.audio or update.message.voice

    if file_data is None:
        await update.message.reply_text('Неправильный формат файла!')
        return SPEAKERS

    file = await file_data.get_file()
    file_bytearray = await file.download_as_bytearray()

    metadata = get_chat_metadata(update.message.chat_id)
    metadata['speakers'].append({
        'filename': file_data.file_name,
        'buffer': base64.b64encode(file_bytearray).decode(),
    })
    metadata['members'].append(update.message.caption or Path(file_data.file_name).stem)
    set_chat_metadata(update.message.chat_id, metadata)

    return SPEAKERS


async def get_speakers_done(update: Update, ctx):
    await update.message.reply_text('Примеры голосов спикеров сохранены!')
    await update.message.reply_text('Теперь отправьте аудио-файл для обработки...')
    return MAIN_AUDIO


async def get_main_audio(update: Update, ctx):
    if update.message.voice is not None:
        await update.message.reply_text('Голосовые сообщения пока не поддерживаются :(')
        return
    
    file_data = update.message.document or update.message.audio
    if file_data is None:
        await update.message.reply_text('Неправильный формат файла!')
        return MAIN_AUDIO

    file = await file_data.get_file()
    file_path = await file.download_to_drive(f'./temp/{update.message.chat_id}/{file_data.file_name}')
    

    metadata: dict = get_chat_metadata(update.message.chat_id)
    metadata['audio'] = {
        'filename': file_data.file_name,
        'buffer': get_file_bytes_as_b64(file_path),
    }
    set_chat_metadata(update.message.chat_id, metadata)

    await update.message.reply_text('⏳')

    metadata.pop('password', None)

    if metadata['type'] == 1:
        channel.basic_publish('', 'auto_analyze', json.dumps(metadata))
        return ConversationHandler.END
    
    channel.basic_publish('', 'manual_analyze', json.dumps(metadata))
    return WAIT_REPLY

async def accept_response(update: Update, ctx):
    temp_directory = f'./temp/{update.message.chat_id}'

    CreateDirectory(f'{temp_directory}/samples/')
    metadata = get_chat_metadata(update.message.chat_id)
    speakers = {}

    with open(f'{temp_directory}/speakers.srt', 'r', encoding='utf-8') as srt_file:
        srt = SrtParser(srt_file)
        srt.parse()

    sound = AudioSegment.from_file(f'{temp_directory}/{metadata["audio"]["filename"]}')
    for subtitle in srt.subtitles:
        speaker_name = subtitle.text.split(':', 1)[0].split(' ')[1]

        if speaker_name not in speakers:
            speakers[speaker_name] = []

        if len(speakers[speaker_name]) >= 3:
            continue

        sample = sound[subtitle.start:subtitle.end]
        sample_path = f'{temp_directory}/samples/{speaker_name}_{subtitle.number}.mp3'
        sample.export(sample_path, format='mp3')

        speakers[speaker_name].append(sample_path)
    
    for speaker_name in sorted(speakers):
        await update.message.reply_text(f'Примеры голоса спикера: {speaker_name}')
        for sample_path in speakers[speaker_name]:
            with open(sample_path, 'rb') as sample:
                await update.message.reply_voice(sample)

    RemoveDirectory(f'{temp_directory}/samples')

    await update.message.reply_text('Введите имя для SPEAKER_00.')
    return SPEAKER_NAMES


async def get_speakers_names(update: Update, ctx):
    metadata = get_chat_metadata(update.message.chat_id)

    cur_speaker = metadata['cur_speaker']

    speaker_old = 'Speaker SPEAKER_' + str(cur_speaker).zfill(2)
    speaker_new = update.message.text

    with open(f'./temp/{update.message.chat_id}/speakers.srt', 'r') as srt_file:
        filedata = srt_file.read()

    filedata = filedata.replace(speaker_old, speaker_new)

    with open(f'./temp/{update.message.chat_id}/speakers.srt', 'w') as srt_file:
        srt_file.write(filedata)

    cur_speaker += 1
    metadata['cur_speaker'] = cur_speaker
    metadata['members'].append(speaker_new)
    set_chat_metadata(update.message.chat_id, metadata)

    if cur_speaker < metadata['num_speakers']:
        await update.message.reply_text(f'Введите имя для SPEAKER_' + str(cur_speaker).zfill(2))
        return SPEAKER_NAMES

    await update.message.reply_text('⏳')
    with open(f'./temp/{update.message.chat_id}/speakers.srt', 'r') as srt_file:
        request_body = {
            'chat_id': update.message.chat_id,
            'file_name': metadata['audio']['filename'],
            'transcribed_text': srt_file.read(),
        }

        channel.basic_publish('', 'transcribed_text_upload', json.dumps(request_body))

    return ConversationHandler.END

async def stats(update: Update, ctx):
    records = db.get_stats_by_chat_id(update.message.chat_id)
    records_count = len(records)

    if records_count > 0:
        await update.message.reply_text(f'Ваша история содержит {records_count} запросов:')
        msg = ''
        for record in records:
            msg += f'''
ID Запроса {record.id}:
    Офицальный отчет: {'Available' if record.formal_protocol else 'Not Available'}
    Неофицальный отчет: {'Available' if record.informal_protocol else 'Not Available'}
    Отчет о транскрибации: {'Available' if record.audio_transcription else 'Not Available'}
            '''
        
        await update.message.reply_text(msg)

        return
    
    await update.message.reply_text('Вы еще не сделали ни одного запроса.')


if __name__ == "__main__":
    # RabbitMQ

    credentials = pika.PlainCredentials('user', 'password')
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials, heartbeat=5000))
    channel = connection.channel()

    channel.queue_declare(queue='auto_analyze')
    channel.queue_declare(queue='manual_analyze')
    channel.queue_declare(queue='transcribed_text_upload')

    #TelegramBOT

    application = ApplicationBuilder()
    application.token(API_KEY)
    application.base_url(f'http://{TELEGRAM_HOST}:8081/bot')
    application.local_mode(True)
    application.read_timeout(30)
    application.write_timeout(30)

    application = application.build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            MessageHandler(filters.Regex('^Start$'), start),
        ],
        states={
            START: [
                MessageHandler(filters.Regex('^Запуск$'), ask_password),
            ],
            PASSWORD: [
                CallbackQueryHandler(generate_password, pattern='^1$'),
                CallbackQueryHandler(skip_password, pattern='^2$'),
                MessageHandler(filters.TEXT, set_password),
            ],
            TYPE: [
                CallbackQueryHandler(get_type),
            ],
            SPEAKERS: [
                MessageHandler(filters.ATTACHMENT | filters.AUDIO, get_speakers),
                MessageHandler(filters.Regex('^Сохранить выбор$'), get_speakers_done)
            ],
            MAIN_AUDIO: [
                MessageHandler(filters.ATTACHMENT | filters.AUDIO | filters.VOICE, get_main_audio),
            ],
            WAIT_REPLY: [
                MessageHandler(filters.Regex('^Продолжить$'), accept_response)
            ],
            SPEAKER_NAMES: [
                MessageHandler(filters.TEXT, get_speakers_names),
            ],
        },
        fallbacks=[
            CommandHandler("start", start),
            MessageHandler(filters.Regex('^Start$'), start),
        ],
    )

    application.add_handler(CommandHandler('stats', stats))
    application.add_handler(conv_handler)
    application.run_polling()
