FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install espeak and other dependencies
# espeak is needed for pyttsx3 fallback
RUN apt-get update && apt-get install -y --no-install-recommends \
    espeak espeak-ng libespeak-ng1 curl ca-certificates fonts-dejavu-core \
    libespeak1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY bot /app/bot

ENV TELEGRAM_BOT_TOKEN="" \
    DEFAULT_LANG="ru"

VOLUME ["/app/bot/maps", "/app/bot/tts"]

CMD ["python", "-m", "bot.main"]
