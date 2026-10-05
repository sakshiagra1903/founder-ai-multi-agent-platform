FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed for compiling python packages (like psycopg2, uvicorn, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout=120 --retries=5 --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

# Copy application source
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
