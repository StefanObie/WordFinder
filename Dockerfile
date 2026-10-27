FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Bake the NLTK corpora into the image so startup needs no network.
RUN python -m nltk.downloader -d /app/backend/nltk_data words brown

COPY backend/ backend/
COPY frontend/ frontend/

RUN useradd --system --create-home app
USER app

WORKDIR /app/backend
EXPOSE 8000
# --preload builds the word list once and shares it across workers.
CMD ["gunicorn", "--preload", "--workers", "2", "--bind", "0.0.0.0:8000", "main:app"]
