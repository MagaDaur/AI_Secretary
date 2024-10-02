FROM huggingface/transformers-pytorch-gpu

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

#RUN python3 -m pytorch_lightning.utilities.upgrade_checkpoint /root/.cache/torch/whisperx-vad-segmentation.bin

CMD python3 app.py
