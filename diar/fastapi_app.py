from typing import List
import shutil
import torch
from pydub import AudioSegment
from concurrent.futures import ThreadPoolExecutor
from whisperx.diarize import DiarizationPipeline
from speechbrain.inference.speaker import SpeakerRecognition
import whisperx
from whisperx import load_align_model, align, assign_word_speakers
import time

import pika
import base64
import json

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Токен для Hugging Face
HF_TOKEN = "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"

# Устройство (CPU или GPU)
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def transcribe_audio(audio_file, model_name="large-v2", compute_type="float16"):
    """Транскрибация аудиофайла"""
    model = whisperx.load_model(model_name, device='cuda', compute_type=compute_type)
    transcription_result = model.transcribe(audio_file)
    return transcription_result

def extract_audio_segments(audio_file, diarize_df):
    """Извлечение аудиосегментов для каждого спикера"""
    audio = AudioSegment.from_file(audio_file)
    segments = []

    for _, row in diarize_df.iterrows():
        start = row['start'] * 1000  # переводим в миллисекунды
        end = row['end'] * 1000
        segment = audio[start:end]
        segments.append(segment)

    diarize_df['audio_segment'] = segments
    return diarize_df

def perform_diarization(audio_file):
    """Диаризация аудиофайла"""
    diarization_pipeline = DiarizationPipeline(use_auth_token=HF_TOKEN, device='cuda')
    diarized = diarization_pipeline(audio_file)
    return diarized

def perform_verification(longest_segments, reference_samples, reference_names):
    """Сравнение каждого спикера с эталонными голосами и присвоение имен"""
    verification = SpeakerRecognition.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb", savedir="pretrained_models/spkrec-ecapa-voxceleb")

    results = {}
    with ThreadPoolExecutor() as executor:
        future_to_speaker = {executor.submit(compare_audio_with_references, row, reference_samples, verification): speaker for speaker, row in longest_segments.iterrows()}
        for future in future_to_speaker:
            speaker, comparison_results = future.result()
            results[speaker] = comparison_results

    matching = {}
    used_references = set()

    for _ in range(len(results)):
        best_match = None
        best_score = -float('inf')

        for speaker, comparisons in results.items():
            for i, score in enumerate(comparisons):
                reference_name = reference_names[i]
                if reference_name not in used_references and score > best_score:
                    best_match = (speaker, reference_name)
                    best_score = score

        if best_match:
            speaker, reference_name = best_match
            matching[speaker] = reference_name
            used_references.add(reference_name)

    return matching

def compare_audio_with_references(segment_row, reference_samples, verification):
    """Сравнение одного сегмента с эталонными голосами"""
    audio_segment = segment_row['audio_segment']
    comparison_results = []
    for reference in reference_samples:
        temp_file = "temp_segment.wav"
        if audio_segment:
            audio_segment.export(temp_file, format="wav")
            score, prediction = verification.verify_files(temp_file, reference)
            comparison_results.append(score)
        else:
            print(f"Warning: Empty audio segment for speaker {segment_row['speaker']}")
            comparison_results.append(0)
    return segment_row['speaker'], comparison_results

def align_speakers_to_text(script, diarize_df, audio_file):
    """Выравнивание текста по спикерам"""
    model_a, metadata = load_align_model(language_code=script["language"], device=DEVICE)
    script_aligned = align(script["segments"], model_a, metadata, audio_file, DEVICE)

    result_segments, word_seg = list(assign_word_speakers(diarize_df, script_aligned).values())

    transcribed_text = []
    for result_segment in result_segments:
        speaker = result_segment.get("speaker", "Unknown")
        transcribed_text.append(
            {
                "start": result_segment["start"],
                "end": result_segment["end"],
                "text": result_segment["text"],
                "speaker": speaker,
            }
        )

    return transcribed_text

def generate_srt(transcribed_text, output_file="output.srt"):
    """Генерация SRT файла из транскрибированного текста с указанием имен спикеров"""
    with open(output_file, "w", encoding="utf-8") as srt_file:
        for i, segment in enumerate(transcribed_text, start=1):
            start_time = segment['start']
            end_time = segment['end']
            text = segment['text']
            speaker = segment['speaker']
            
            # Формат времени для SRT (HH:MM:SS,ms)
            start_time_srt = time.strftime('%H:%M:%S,', time.gmtime(start_time)) + f'{int((start_time * 1000) % 1000):03d}'
            end_time_srt = time.strftime('%H:%M:%S,', time.gmtime(end_time)) + f'{int((end_time * 1000) % 1000):03d}'
            
            # Запись сегмента в файл
            srt_file.write(f"{i}\n")
            srt_file.write(f"{start_time_srt} --> {end_time_srt}\n")
            srt_file.write(f"{speaker}: {text}\n\n")
    
    print(f"SRT файл успешно создан: {output_file}")


def count_unique_speakers(diarize_df):
    """Подсчёт уникальных спикеров в результатах диаризации"""
    unique_speakers = diarize_df['speaker'].nunique()
    return unique_speakers

def main(audio_file, reference_samples, reference_names):
    """Основная функция анализа аудиофайла"""
    start_time = time.time()

    script = transcribe_audio(audio_file)
    diarize_df = perform_diarization(audio_file)
    diarize_df = extract_audio_segments(audio_file, diarize_df)
    longest_segments = diarize_df.groupby('speaker').apply(lambda x: x.loc[(x['end'] - x['start']).idxmax()])

    speaker_matching = perform_verification(longest_segments, reference_samples, reference_names)
    transcribed_text = align_speakers_to_text(script, diarize_df, audio_file)

    for segment in transcribed_text:
        speaker_id = segment["speaker"]
        segment["speaker"] = speaker_matching.get(speaker_id, f"Speaker {speaker_id}")

    end_time = time.time()
    processing_time = end_time - start_time

    result = {
        "transcription": transcribed_text,
        "processing_time": processing_time
    }

    return result

def get_file_bytes_as_b64(file_path: str):
    with open(file_path, 'rb') as file:
        return base64.b64encode(file.read()).decode() 

'''
    audio_file: UploadFile = File(...),
    reference_files: List[UploadFile] = File(...),
    '''

def verify_audio(ch, method, properties, body):
    input_data = json.loads(body)

    # Сохранение загруженного аудиофайла
    audio_file_path = f"/tmp/{input_data['audio']['filename']}"
    with open(audio_file_path, "wb") as buffer:
        buffer.write(base64.b64decode(input_data['audio']['buffer']))

    # Сохранение эталонных файлов
    reference_names = []
    reference_file_paths = []
    for ref_file in input_data['speakers']:
        reference_names.append(ref_file['filename'])
        ref_file_path = f"/tmp/{ref_file['filename']}"
        with open(ref_file_path, "wb") as buffer:
            buffer.write(base64.b64decode(ref_file['buffer']))
        reference_file_paths.append(ref_file_path)

    # Вызов основной функции
    result = main(audio_file_path, reference_file_paths, reference_names)
    
    # Генерация SRT файла
    output_srt = f"/tmp/{input_data['audio']['filename']}.srt"
    generate_srt(result['transcription'], output_file=output_srt)
    
    # Подсчёт уникальных спикеров
    unique_speakers = count_unique_speakers(pd.DataFrame(result['transcription']))

    data = {'chat_id': input_data['chat_id'],"unique_speakers": unique_speakers, "srt_file": get_file_bytes_as_b64(output_srt)}

    channel.basic_publish('', 'telegram_text_upload', json.dumps(data))


def process_audio(ch, method, properties, body):
    input_data = json.loads(body)

    file_location = f"./temp_{input_data['audio']['filename']}"
    
    with open(file_location, "wb+") as file_object:
        file_object.write(base64.b64decode(input_data['audio']['buffer']))

    # Транскрибация
    script = transcribe_audio(file_location)

    # Диаризация
    diarize_df = perform_diarization(file_location)

    # Выравнивание текста
    transcribed_text = align_speakers_to_text(script, diarize_df, file_location)

    # Присвоение имен спикерам в тексте
    unique_speakers = count_unique_speakers(diarize_df)
    speaker_mapping = {f"speaker{i+1}": f"speaker{i+1}" for i in range(unique_speakers)}
    
    for segment in transcribed_text:
        speaker_id = segment["speaker"]
        segment["speaker"] = speaker_mapping.get(speaker_id, f"Speaker {speaker_id}")

    # Генерация SRT файла
    output_srt = f"./{input_data['audio']['filename']}.srt"
    generate_srt(transcribed_text, output_file=output_srt)

    data = {'chat_id': input_data['chat_id'], "unique_speakers": unique_speakers, "srt_file": get_file_bytes_as_b64(output_srt)}

    channel.basic_publish('', 'asr_line', json.dumps(data))

channel.queue_declare(queue='auto_analyze')
channel.queue_declare(queue='manual_analyze')
channel.queue_declare(queue='asr_line')

channel.basic_consume(queue='auto_analyze', auto_ack=True, on_message_callback=verify_audio)
channel.basic_consume(queue='manual_analyze', auto_ack=True, on_message_callback=process_audio)

channel.start_consuming()