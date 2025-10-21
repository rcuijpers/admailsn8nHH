# Dockerfile for Render (Docker Web Service)
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Build deps (small)
RUN apt-get update && apt-get install -y --no-install-recommends \    build-essential \    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install -r requirements.txt

# Pre-download the Dutch model to speed up startup
RUN python -m spacy download nl_core_news_sm

# App
COPY app.py .

# Render provides $PORT; default to 10000 for local tests
ENV PORT=10000
EXPOSE 10000

CMD uvicorn app:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips="*"
