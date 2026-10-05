FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --timeout=120 --retries=5 --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

# Pre-download the RAG embedding model at BUILD time (same reasoning as the
# Feedback agent's Dockerfile): sentence-transformers otherwise lazy-downloads
# this from HuggingFace Hub the first time rag_service.py actually embeds
# something, i.e. at request time inside the running container. Baking it
# into the image removes that runtime network dependency.
RUN python -c "from langchain_huggingface import HuggingFaceEmbeddings; HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2', model_kwargs={'device': 'cpu'})"

COPY . .

RUN mkdir -p uploads chroma_db

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
