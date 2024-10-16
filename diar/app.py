from os import getenv
from dotenv import load_dotenv

import torch
from pydub import AudioSegment
from concurrent.futures import ThreadPoolExecutor
from whisperx.diarize import DiarizationPipeline
from speechbrain.inference.speaker import SpeakerRecognition
from whisperx import load_align_model, align, assign_word_speakers
import time
import pandas as pd

import aio_pika
from aio_pika import Message
import base64
import json
import asyncio

import logging
logging.basicConfig(level=logging.INFO)

load_dotenv()

import whisperx

import os
os.environ['HF_HOME'] = '/models'

torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True

HF_TOKEN = getenv('HF_TOKEN')
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST')
RABBITMQ_LOGIN = os.getenv('RABBITMQ_DEFAULT_USER')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_DEFAULT_PASS')

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
logging.info(f"### Device: {DEVICE} ###")

async def transcribe_audio(audio_file):
    loop = asyncio.get_event_loop()

    logging.info(f"### TRANSCRIBATION STARTED ###")

    transcription_result = await loop.run_in_executor(None, model.transcribe, audio_file)

    logging.info(f"### TRANSCRIBATION ENDED ###")

    return transcription_result

def extract_audio_segments(audio_file, diarize_df):
    audio = AudioSegment.from_file(audio_file)
    segments = []

    for _, row in diarize_df.iterrows():
        start = row['start'] * 1000
        end = row['end'] * 1000
        segment = audio[start:end]
        segments.append(segment)

    diarize_df['audio_segment'] = segments
    return diarize_df


def perform_diarization(audio_file):
    logging.info(f"### DIARIZATION STARTED ###")

    diarization_pipeline = DiarizationPipeline(use_auth_token=HF_TOKEN, device=DEVICE)
    diarized = diarization_pipeline(audio_file)

    logging.info(f"### DIARIZATION ENDED ###")

    return diarized


def perform_verification(longest_segments, reference_samples, reference_names):
    verification = SpeakerRecognition.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb",
                                                   savedir="pretrained_models/spkrec-ecapa-voxceleb",
                                                   use_auth_token=HF_TOKEN)

    results = {}
    with ThreadPoolExecutor() as executor:
        future_to_speaker = {
            executor.submit(compare_audio_with_references, row, reference_samples, verification): speaker for
            speaker, row in longest_segments.iterrows()}
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
    model_a, metadata = load_align_model(language_code=script["language"], device=DEVICE)
    script_aligned = align(script["segments"], model_a, metadata, audio_file, device=DEVICE)

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
    with open(output_file, "w", encoding="utf-8") as srt_file:
        for i, segment in enumerate(transcribed_text, start=1):
            start_time = segment['start']
            end_time = segment['end']
            text = segment['text']
            speaker = segment['speaker']

            start_time_srt = time.strftime('%H:%M:%S,',
                                           time.gmtime(start_time)) + f'{int((start_time * 1000) % 1000):03d}'
            end_time_srt = time.strftime('%H:%M:%S,', time.gmtime(end_time)) + f'{int((end_time * 1000) % 1000):03d}'

            srt_file.write(f"{i}\n")
            srt_file.write(f"{start_time_srt} --> {end_time_srt}\n")
            srt_file.write(f"{speaker}: {text}\n\n")

    print(f"SRT файл успешно создан: {output_file}")


def count_unique_speakers(diarize_df):
    unique_speakers = diarize_df['speaker'].nunique()
    return unique_speakers


def main(audio_file, reference_samples, reference_names):
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


async def verify_audio(message):
    async with message.process():
        input_data = json.loads(message.body)

        audio_file_path = f"/tmp/{input_data['audio']['filename']}"
        with open(audio_file_path, "wb") as buffer:
            buffer.write(base64.b64decode(input_data['audio']['buffer']))

        reference_names = input_data['members']
        reference_file_paths = []
        for ref_file in input_data['speakers']:
            ref_file_path = f"/tmp/{ref_file['filename']}"
            with open(ref_file_path, "wb") as buffer:
                buffer.write(base64.b64decode(ref_file['buffer']))
            reference_file_paths.append(ref_file_path)

        result = main(audio_file_path, reference_file_paths, reference_names)

        output_srt = f"/tmp/{input_data['audio']['filename']}.srt"
        generate_srt(result['transcription'], output_file=output_srt)

        with open(output_srt, 'r') as srt_file:

            data = {
                'chat_id': input_data['chat_id'],
                'transcribed_text': srt_file.read(),
                'file_name': input_data['audio']['filename'],
            }

            await channel.default_exchange.publish(Message(json.dumps(data).encode()), 'transcribed_text_upload')

async def process_audio(message):
    async with message.process():
        input_data = json.loads(message.body)

        file_location = f"./temp_{input_data['audio']['filename']}"

        with open(file_location, "wb+") as file_object:
            file_object.write(base64.b64decode(input_data['audio']['buffer']))

        logging.info("### Started handling audio ###")

        script = await transcribe_audio(file_location)

        diarize_df = perform_diarization(file_location)

        transcribed_text = align_speakers_to_text(script, diarize_df, file_location)

        unique_speakers = count_unique_speakers(diarize_df)
        speaker_mapping = {f"speaker{i + 1}": f"speaker{i + 1}" for i in range(unique_speakers)}

        for segment in transcribed_text:
            speaker_id = segment["speaker"]
            segment["speaker"] = speaker_mapping.get(speaker_id, f"Speaker {speaker_id}")

        output_srt = f"./{input_data['audio']['filename']}.srt"
        generate_srt(transcribed_text, output_file=output_srt)

        data = {'chat_id': input_data['chat_id'], "unique_speakers": unique_speakers,
                "srt_file": get_file_bytes_as_b64(output_srt)}

        await channel.default_exchange.publish(Message(json.dumps(data).encode()), 'asr_to_handler')

async def main():
    global channel
    global model

    connection = await aio_pika.connect(host=RABBITMQ_HOST, login=RABBITMQ_LOGIN, password=RABBITMQ_PASSWORD, heartbeat=5000)

    logging.info(f'### LOADING MODEL ###')
    model = whisperx.load_model("large-v2", device=DEVICE, compute_type="float16", language='ru')
    logging.info(f'### MODEL HAS BEEN CACHED ###')

    async with connection:
        channel = await connection.channel()

        await channel.set_qos(prefetch_count=10)

        auto_analyze = await channel.declare_queue('auto_analyze')
        manual_analyze = await channel.declare_queue('manual_analyze')

        await auto_analyze.consume(verify_audio)
        await manual_analyze.consume(process_audio)

        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())