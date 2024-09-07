FROM huggingface/transformers-pytorch-gpu

COPY ./ ./

RUN pip install -r requirements.txt

RUN ls

CMD python3 app.py