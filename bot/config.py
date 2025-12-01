import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
DEFAULT_LANG = os.getenv("DEFAULT_LANG", "ru")
DATA_DB_PATH = os.getenv("DATA_DB_PATH", os.path.join(os.path.dirname(__file__), "data.db"))
MAP_IMG_DIR = os.getenv("MAP_IMG_DIR", os.path.join(os.path.dirname(__file__), "maps"))
TTS_AUDIO_DIR = os.getenv("TTS_AUDIO_DIR", os.path.join(os.path.dirname(__file__), "tts"))

def ensure_dirs():
    for d in [MAP_IMG_DIR, TTS_AUDIO_DIR]:
        os.makedirs(d, exist_ok=True)