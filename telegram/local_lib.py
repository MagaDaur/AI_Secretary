import json
import base64
from os import listdir
import secrets
import string

BASE_METADATA = {
    'speakers': [],
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