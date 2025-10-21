FROM python:3.10-slim

# Zorg dat apt een paar basis dingen heeft
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Installeer Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ✅ Installeer direct het SpaCy model (werkt op Render, geen 404)
RUN pip install https://github.com/explosion/spacy-models/releases/download/nl_core_news_lg-3.2.0/nl_core_news_lg-3.2.0.tar.gz

# Copy app
COPY app.py .

# Start server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
