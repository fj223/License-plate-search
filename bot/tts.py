import os
import time
import pyttsx3
from .config import TTS_AUDIO_DIR

def synthesize(text, lang="ru"):
    os.makedirs(TTS_AUDIO_DIR, exist_ok=True)
    engine = pyttsx3.init()
    rate = engine.getProperty('rate')
    engine.setProperty('rate', max(120, rate - 40))
    voices = engine.getProperty('voices')
    target = None
    if lang == "zh":
        for v in voices:
            if "zh" in v.languages or "Chinese" in v.name:
                target = v.id
                break
    else:
        for v in voices:
            if "ru" in str(v.languages).lower() or "Russian" in v.name:
                target = v.id
                break
    if target:
        engine.setProperty('voice', target)
    fname = f"tts_{int(time.time()*1000)}.wav"
    fpath = os.path.join(TTS_AUDIO_DIR, fname)
    engine.save_to_file(text, fpath)
    engine.runAndWait()
    return fpath