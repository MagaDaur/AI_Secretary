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

from os import (
    makedirs as CreateDirectory,
    listdir,
    getenv,
)

from shutil import (
    rmtree as RemoveDirectory
)

from dotenv import (
    load_dotenv
)

import pika
import base64
import json

BASE_METADATA = {
    'names': [],
    'password': False,
    'type': 1,
}

load_dotenv()

API_KEY = getenv('API_KEY')

credentials = pika.PlainCredentials('user', 'password')
#connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq-server', credentials=credentials, heartbeat=500))
connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost', heartbeat=500))

channel = connection.channel()
channel.queue_declare(queue='audio_upload')

SET_PASSWORD, SET_TYPE, SET_MAIN_AUDIO, SET_SPEAKERS, SET_SPEAKERS_NAMES, WAIT_REPLY = range(6)

def get_directory_filenames(directory_path: str):
    filenames = []
    for filename in listdir(directory_path):
        filenames.append(filename)

    return filenames
def get_file_bytes_as_b64(file_path: str):
    with open(file_path, 'rb') as file:
        return base64.b64encode(file.read()).decode() 
def get_speaker_files_b64(directory_path: str):
    data = []
    filenames = get_directory_filenames(directory_path)
    for filename in filenames:
        data.append({
            'filename': filename,
            'buffer': get_file_bytes_as_b64(directory_path + filename)
        })

    return data
def get_metadata(file_path: str):
    with open(file_path, 'r') as file:
        return json.load(file)
def set_metadata(file_path: str, value: dict):
    with open(file_path, 'w') as file:
        json.dump(value, file)

async def start(update : Update, ctx):
    keyboard = [
        [
            InlineKeyboardButton("Да", callback_data='1'),
            InlineKeyboardButton("Нет", callback_data='2'),
        ]
    ]

    CreateDirectory(f'./temp/{update.message.chat_id}/', exist_ok=True)
    set_metadata(f'./temp/{update.message.chat_id}.json', BASE_METADATA)

    await update.message.reply_text('Привет, нужен ли пароль?', reply_markup=InlineKeyboardMarkup(keyboard))
    
    return SET_PASSWORD

async def set_password(update : Update, ctx):
    query = update.callback_query
    await query.answer()

    metadata_path = f'./temp/{query.message.chat.id}.json'

    metadata = get_metadata(metadata_path)
    metadata['password'] = True if query.data == '1' else False
    set_metadata(metadata_path, metadata)

    keyboard = [
        [
            InlineKeyboardButton("Авто", callback_data='1'),
            InlineKeyboardButton("Ручной", callback_data='2'),
        ]
    ]

    await query.edit_message_text('Теперь выбери режим анализа', reply_markup=InlineKeyboardMarkup(keyboard))

    return SET_TYPE

async def set_type(update : Update, ctx):
    query = update.callback_query
    await query.answer()

    metadata_path = f'./temp/{query.message.chat.id}.json'
    metadata = get_metadata(metadata_path)
    metadata['type'] = int(query.data)
    set_metadata(metadata_path, metadata)

    if query.data == '1':
        await query.delete_message()

        keyboard = [[InlineKeyboardButton('Отправить')]]
        await query.message.chat.send_message('Кидай аудио спикеров (названия файлов ФИО)', reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
        
        return SET_SPEAKERS

    await query.edit_message_text('Кидай аудио для аналитики')
    return SET_MAIN_AUDIO
    
async def get_speakers(update : Update, ctx):
    file_data = update.message.document or update.message.audio or update.message.voice
    if file_data is None:
        await update.message.reply_text('Неправильный формат файла!')
        return SET_SPEAKERS
    
    file = await file_data.get_file()
    await file.download_to_drive(f'./temp/{update.message.chat_id}/{file_data.file_name}')
    
    return SET_SPEAKERS

async def speakers_done(update : Update, ctx):
    await update.message.reply_text(
        'Теперь загрузите аудио-файл на обработку...',
        reply_markup=ReplyKeyboardRemove()
        )
    return SET_MAIN_AUDIO

async def get_audio(update : Update, ctx):
    file_data = update.message.document or update.message.audio or update.message.voice
    if file_data is None:
        await update.message.reply_text('Неправильный формат файла!')
        return SET_MAIN_AUDIO

    file = await file_data.get_file()
    file_bytearray = await file.download_as_bytearray()

    json_data = {
        'chat_id': update.message.chat_id,
        'audio': {
            'filename': file_data.file_name,
            'buffer': base64.b64encode(file_bytearray).decode(),
        },
        'speakers': get_speaker_files_b64(f'./temp/{update.message.chat_id}/')
    }

    metadata_path = f'./temp/{update.message.chat_id}.json'
    metadata = get_metadata(metadata_path)

    if metadata['type'] == 1:
        channel.basic_publish('', 'auto_analyze', json.dumps(json_data))
    elif metadata['type'] == 2:
        channel.basic_publish('', 'manual_analyze', json.dumps(json_data))

    RemoveDirectory(f'./temp/{update.message.chat_id}/', ignore_errors=True)

    await update.message.reply_text('Идет обработка вашего запроса, ожидайте...')

    return WAIT_REPLY

async def get_speakers_names(update : Update, ctx):
    metadata_path = f'./temp/{update.message.chat_id}.json'
    metadata = get_metadata(metadata_path)
    metadata['names'].append(update.message.text)
    set_metadata(metadata_path, metadata)

    return SET_SPEAKERS_NAMES

def main():
    application = ApplicationBuilder()
    application.token(API_KEY)
    #application.base_url('http://sfo_prep-telegram-bot-api-1:8081/bot')
    application.base_url('http://localhost:8081/bot')

    application = application.build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SET_PASSWORD: [
                CallbackQueryHandler(set_password),
            ],
            SET_TYPE: [
                CallbackQueryHandler(set_type)
            ],
            SET_SPEAKERS: [
                MessageHandler(filters.ATTACHMENT | filters.VOICE, get_speakers),
                MessageHandler(filters.Regex('^Отправить$'), speakers_done)
            ],
            SET_MAIN_AUDIO: [
                MessageHandler(filters.ATTACHMENT | filters.VOICE, get_audio),
            ],
            SET_SPEAKERS_NAMES: [
                MessageHandler(filters.Regex('SPEAKER(\d+)\s*:\s*(.+)'), get_speakers_names)
            ],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()

