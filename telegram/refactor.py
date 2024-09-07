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
def get_chat_metadata(chat_id):
    return get_metadata(f'./temp/{chat_id}.json')
def set_chat_metadata(chat_id, value):
    set_metadata(f'./temp/{chat_id}.json', value)

load_dotenv()

BASE_METADATA = {
    'names': [],
    'speakers': [],
}

API_KEY = getenv('API_KEY')

START = 0
PASSWORD = 1
TYPE = 2
SPEAKERS = 3
MAIN_AUDIO = 4
WAIT_REPLY = 5

# credentials = pika.PlainCredentials('user', 'password')
# connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq-server', credentials=credentials, heartbeat=500))
#connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost', heartbeat=500))

# channel = connection.channel()
# channel.queue_declare(queue='auto_analyze')
# channel.queue_declare(queue='manual_analyze')

async def start(update: Update, ctx):
    CreateDirectory(f'./temp/{update.message.chat_id}/', exist_ok=True)

    metadata = BASE_METADATA.copy()
    metadata['chat_id'] = update.message.chat_id
    set_chat_metadata(update.message.chat_id, metadata)

    keyboard = [['Запуск']]
    await update.message.reply_text('Привет я ИИ-Секретарь. Начнём?', reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True))

    return START

async def ask_password(update: Update, ctx):
    keydoard = [
        [
            InlineKeyboardButton('Да', callback_data='1'),
            InlineKeyboardButton('Нет', callback_data='2'),
        ]
    ]
    await update.message.reply_text('Желаете ли установить пароль на итоговый отчет?', reply_markup=InlineKeyboardMarkup(keydoard))

    return PASSWORD

async def wait_for_password(update: Update, ctx):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text('Введите желаемый пароль...')

    return PASSWORD

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

async def get_password(update: Update, ctx):
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
    !!ВАЖНО!! - Названия аудио-файлов будут считаться именами спикеров.
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
        await query.message.chat.send_message(auto_instruction, reply_markup=ReplyKeyboardMarkup([['Сохранить выбор']], one_time_keyboard=True, resize_keyboard=True))
        return SPEAKERS

    await query.message.chat.send_message(manual_instruction)
    return MAIN_AUDIO
    

async def get_speakers(update: Update, ctx):
    file_data = update.message.document or update.message.audio or update.message.voice
    if file_data is None:
        await update.message.reply_text('Неправильный формат файла!')
        return SPEAKERS

    metadata = get_chat_metadata(update.message.chat_id)
    
    file = await file_data.get_file()
    file_bytearray = await file.download_as_bytearray()

    metadata['speakers'].append({
        'filename': file_data.file_name,
        'buffer': base64.b64encode(file_bytearray).decode(),
    })

    return SPEAKERS

async def get_speakers_done(update: Update, ctx):
    await update.message.reply_text('Примеры голосов спикеров сохранены!')
    await update.message.reply_text('Теперь отправьте аудио-файл для обработки...')
    return MAIN_AUDIO

async def get_main_audio(update: Update, ctx):
    file_data = update.message.document or update.message.audio or update.message.voice
    if file_data is None:
        await update.message.reply_text('Неправильный формат файла!')
        return MAIN_AUDIO

    metadata = get_chat_metadata(update.message.chat_id)
    
    file = await file_data.get_file()
    file_bytearray = await file.download_as_bytearray()

    metadata['audio'] = {
        'filename': file_data.file_name,
        'buffer': base64.b64encode(file_bytearray).decode(),
    }

    #return WAIT_REPLY
    return ConversationHandler.END

async def get_speakers_names(update: Update, ctx):
    pass

async def get_speakers_names_done(update: Update, ctx):
    pass

async def end(update: Update, ctx):
    pass

application = ApplicationBuilder()
application.token(API_KEY)
#application.base_url('http://sfo_prep-telegram-bot-api-1:8081/bot')
#application.base_url('http://localhost:8081/bot')

application = application.build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        START: [
            MessageHandler(filters.Regex('^Запуск$'), ask_password),
        ],
        PASSWORD: [
            CallbackQueryHandler(wait_for_password, pattern='^1$'),
            CallbackQueryHandler(skip_password, pattern='^2$'),
            MessageHandler(filters.Language('en'), get_password),
        ],
        TYPE: [
            CallbackQueryHandler(get_type),
        ],
        SPEAKERS: [
            MessageHandler(filters.AUDIO | filters.VOICE, get_speakers),
            MessageHandler(filters.Regex('^Сохранить выбор$'), get_speakers_done)
        ],
        MAIN_AUDIO: [
            MessageHandler(filters.AUDIO | filters.VOICE, get_main_audio),
        ],
    },
    fallbacks=[CommandHandler("start", start)],
)

application.add_handler(conv_handler)
application.run_polling()