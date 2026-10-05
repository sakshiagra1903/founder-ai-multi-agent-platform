FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --timeout=120 --retries=5 --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

# ── Pre-download NLP models at BUILD time (new, additive) ──────────────────
# sentiment_service / topic_modeling_service otherwise lazy-download these
# from HuggingFace Hub the first time analysis actually runs, i.e. at
# request time inside the running container. If that container has no
# outbound internet at that moment (or HF Hub is slow), every analysis
# stage fails silently (each is wrapped in its own try/except that just
# logs and moves on — see analysis_pipeline.py) and an upload "succeeds"
# with zero sentiment/complaint/feature/topic results. Baking the weights
# into the image removes that runtime dependency entirely. No application
# code changes — this only warms the same HuggingFace cache the app already
# reads from.
RUN python -c "\
from transformers import pipeline; \
pipeline('text-classification', model='cardiffnlp/twitter-roberta-base-sentiment-latest', top_k=None); \
pipeline('text-classification', model='distilbert-base-uncased-finetuned-sst-2-english', top_k=None); \
from sentence_transformers import SentenceTransformer; \
SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

COPY . .

RUN mkdir -p /app/uploads/reports /app/logs

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
