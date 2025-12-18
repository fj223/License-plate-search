import os
import time
import logging

from .config import TTS_AUDIO_DIR

# 初始化可用引擎列表
ENGINES = {}

try:
    from gtts import gTTS
    ENGINES['gtts'] = True
except ImportError:
    ENGINES['gtts'] = False
    logging.warning("gTTS 模块未安装")

try:
    import pyttsx3
    ENGINES['pyttsx3'] = True
except ImportError:
    ENGINES['pyttsx3'] = False
    logging.warning("pyttsx3 模块未安装")

def synthesize(text, lang="ru"):
    """
    合成语音并保存为文件。
    优先使用 gTTS (Google TTS)，如果失败则回退到 pyttsx3 (本地 TTS)。
    
    Args:
        text: 要合成的文本
        lang: 语言代码 ("ru" 或 "zh")
        
    Returns:
        合成的音频文件路径，如果失败则返回 None
    """
    os.makedirs(TTS_AUDIO_DIR, exist_ok=True)
    
    # 记录要合成的文本信息
    logging.info(f"准备合成语音 (语言: {lang}), 文本长度: {len(text)}")
    logging.info(f"文本内容预览: {text[:100]}...")

    # 尝试 gTTS
    if ENGINES.get('gtts'):
        try:
            logging.info(f"正在使用 gTTS 合成语音 ({lang})...")
            # gTTS 语言代码: 'zh-CN' 或 'zh-TW' for Chinese, 'ru' for Russian
            gtts_lang = 'zh-CN' if lang == 'zh' else 'ru'
            
            tts = gTTS(text=text, lang=gtts_lang)
            fname = f"tts_gtts_{int(time.time()*1000)}.mp3"
            fpath = os.path.join(TTS_AUDIO_DIR, fname)
            
            tts.save(fpath)
            
            if os.path.exists(fpath) and os.path.getsize(fpath) > 0:
                logging.info(f"gTTS 语音文件生成成功: {fpath}")
                return fpath
            else:
                logging.warning("gTTS 生成文件为空")
        except Exception as e:
            logging.error(f"gTTS 合成失败: {e}", exc_info=True)
            # 继续尝试下一个引擎
    
    # 回退到 pyttsx3
    if ENGINES.get('pyttsx3'):
        try:
            logging.info(f"正在使用 pyttsx3 合成语音 ({lang})...")
            engine = pyttsx3.init()
            
            # 设置语速
            try:
                rate = engine.getProperty('rate')
                engine.setProperty('rate', max(120, rate - 40))
            except Exception:
                pass
            
            # 设置语音
            try:
                voices = engine.getProperty('voices')
                target_voice = None
                if lang == "zh":
                    for v in voices:
                        if "zh" in str(v.languages).lower() or "Chinese" in v.name:
                            target_voice = v.id
                            break
                else:  # 默认俄语
                    for v in voices:
                        if "ru" in str(v.languages).lower() or "Russian" in v.name:
                            target_voice = v.id
                            break
                if target_voice:
                    engine.setProperty('voice', target_voice)
            except Exception:
                pass
            
            fname = f"tts_pyttsx3_{int(time.time()*1000)}.wav"
            fpath = os.path.join(TTS_AUDIO_DIR, fname)
            
            engine.save_to_file(text, fpath)
            engine.runAndWait()
            
            if os.path.exists(fpath) and os.path.getsize(fpath) > 0:
                logging.info(f"pyttsx3 语音文件生成成功: {fpath}")
                return fpath
            else:
                logging.error(f"pyttsx3 语音文件生成失败或为空")
                return None
                
        except Exception as e:
            logging.error(f"pyttsx3 语音合成过程中发生错误: {e}", exc_info=True)
            return None
    
    logging.error("没有可用的语音合成引擎或所有引擎均失败")
    return None
