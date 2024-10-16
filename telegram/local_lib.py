import json
import base64
from os import listdir
import secrets
import string
import subtitle_parser

BASE_METADATA = {
    'speakers': [],
    'members': [],
    'speakers_samples': {},
}

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
    return get_metadata(f'./temp/{chat_id}/metadata.json')
def set_chat_metadata(chat_id, value):
    set_metadata(f'./temp/{chat_id}/metadata.json', value)

def create_password(l: int):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(l))

def seconds_to_time(total_seconds):
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    return f"{hours:02}:{minutes:02}:{seconds:02}"

def get_srt_data(srt_filepath, timeout: int = 10000, chunk_size: int = 7000):
    with open(srt_filepath, 'r', encoding='utf-8') as srt_file:
        srt = subtitle_parser.SrtParser(srt_file)
        srt.parse()

    data = []

    for subtitle in srt.subtitles:
        speaker, text = subtitle.text.split(':', 1)
        prev = data[-1] if len(data) > 0 else None

        if prev is not None and speaker == prev['speaker'] and subtitle.start - prev['end'] < timeout and len(prev['text']) + len(subtitle.text) < chunk_size:
            prev['end'] = subtitle.end
            prev['text'] = prev['text'] + ' ' + text
            continue

        data.append({
            'speaker': speaker,
            'start': subtitle.start,
            'end': subtitle.end,
            'text': text
        })

    text = ''
    chunks = []
    data_size = len(data)

    for i in range(data_size):
        subtitle = data[i]
        start, end = subtitle['start'] // 1000, subtitle['end'] // 1000

        temp_str = f'Speaker: {subtitle["speaker"]}\n'
        temp_str += f'Time: {seconds_to_time(start)} - {seconds_to_time(end)}\n'
        temp_str += f'Text: {subtitle["text"]}\n\n'

        if len(text) + len(temp_str) <= chunk_size:
            text += temp_str
        else:
            chunks.append(text)
            text = temp_str

        if i == data_size - 1:
            chunks.append(text)

    return chunks

def fix_llm_respond(data):
    questions = data[0].copy()
    assignments = data[1].copy()

    for i in range(len(questions)):
        questions[i] = {k:v for k,v in questions[i].items() if v is not None and len(v) > 0}

    for i in range(len(assignments)):
        assignments[i] = {k:v for k,v in assignments[i].items() if v is not None and len(v) > 0}

    for question in questions:
        question['Вопрос обсуждения'] = question.get('Вопрос обсуждения', 'Вопрос не обнаружен').capitalize()
        question['Принятое решение'] = question.get('Принятое решение', 'Решение не обнаружено').capitalize()
        question['Контекст обсуждения'] = question.get('Контекст обсуждения', 'Контекст не обнаружен').capitalize()

        if len(question['Участники обсуждения']) == 0:
            question['Участники обсуждения'] = ['Не определен']
            continue

        for i in range(len(question['Участники обсуждения'])):
            question['Участники обсуждения'][i] = question['Участники обсуждения'][i].title()

    for assignment in assignments:
        assignment['Имя исполнителя'] = assignment.get('Имя исполнителя', 'Адресат поручения не определен')
        assignment['Описание поручения'] = assignment.get('Описание поручения', 'Описание поручениян не определено').capitalize()
        assignment['Срок выполнения'] = assignment.get('Срок выполнения', 'Не определен')

    return [questions, assignments]
        