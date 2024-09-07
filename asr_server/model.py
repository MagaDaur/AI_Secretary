import torch

from transformers import WhisperForConditionalGeneration
from transformers import WhisperFeatureExtractor
from transformers import WhisperTokenizer

from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline, AutoModelForSeq2SeqLM, BitsAndBytesConfig

device = "cuda:0"

asr_model_id = "openai/whisper-large-v3"

feature_extractor = WhisperFeatureExtractor.from_pretrained(asr_model_id)
tokenizer = WhisperTokenizer.from_pretrained(asr_model_id, language="russian", task="transcribe")

model = WhisperForConditionalGeneration.from_pretrained(asr_model_id)
forced_decoder_ids = tokenizer.get_decoder_prompt_ids(language="russian", task="transcribe")

asr_pipe = pipeline(
    "automatic-speech-recognition",
    model=model,
    feature_extractor=feature_extractor,
    tokenizer=tokenizer,
    chunk_length_s=30,
    stride_length_s=(4, 2),
    device=device,
)
