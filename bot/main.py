import os
import asyncio
import json
import datetime
import argparse
import logging

# 配置日志
# 强制立即写入文件 (buffering=1)
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log", encoding='utf-8', mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from .config import TELEGRAM_BOT_TOKEN, ensure_dirs
from .db import init_schema, seed_minimal, find_city_by_name, find_region_by_auto_code, list_auto_codes_by_region, find_city_by_phone_code, list_phone_codes_by_city, save_query, find_city_by_name_fuzzy
from .nlp import detect_language, parse_intent
from .reply_templates import format_auto_result, format_auto_region_only, format_phone_result, format_not_found, format_license_plate

# 尝试导入telegram模块
try:
    from telegram import InputFile
    from telegram.ext import Application, CommandHandler, MessageHandler, filters
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    logger.warning("Telegram模块未安装，语音发送功能不可用")

async def start(update, context):
    await update.message.reply_text("Введите город, код региона или телефонный код. 支持中文输入。")

async def handle_text(update, context):
    try:
        text = update.message.text or ""
        logger.info(f"Received message: {text}")
        
        from .nlp import detect_language
        lang = detect_language(text)
        logger.info(f"Detected language: {lang}")
        
        # 向用户显示检测到的语言信息
        lang_msg = "检测到中文" if lang == "zh" else "Русский язык обнаружен"
        await update.message.reply_text(lang_msg)
        
        intent_data = parse_intent(text)
        intent = intent_data.get("intent")
        user_id = str(update.effective_user.id)
        now = datetime.datetime.utcnow().isoformat()
        if intent == "city_to_auto_code":
            city_name = intent_data.get("city", "").strip()
            city = find_city_by_name(city_name) or find_city_by_name_fuzzy(city_name)
            if not city:
                from .geocode import geocode_city
                geo = await asyncio.to_thread(geocode_city, city_name)
                if geo and geo.get("region"):
                    from .db import find_region_by_name
                    region_guess = find_region_by_name(geo["region"]) or find_region_by_name(city_name)
                    if region_guess:
                        region_id, region_ru, region_zh = region_guess
                        codes = list_auto_codes_by_region(region_id)
                        reply = format_auto_region_only(lang, region_ru, region_zh, codes)
                        await update.message.reply_text(reply)
                        from .maps import generate_city_dual_map
                        try:
                            img_bytes = await asyncio.to_thread(generate_city_dual_map, region_ru, geo.get("city"), geo.get("lat"), geo.get("lon"))
                            if img_bytes:
                                try:
                                    await update.message.reply_photo(InputFile(img_bytes, filename="map.png"))
                                    logger.info("Successfully sent map as photo")
                                except Exception as e:
                                    logger.error(f"Failed to send map as photo: {e}")
                                    try:
                                        await update.message.reply_document(InputFile(img_bytes, filename="map.png"))
                                        logger.info("Successfully sent map as document")
                                    except Exception as e2:
                                        logger.error(f"Failed to send map as document: {e2}")
                            else:
                                logger.error("Map generation returned empty bytes")
                        except Exception as e:
                            logger.error(f"Error generating map: {e}", exc_info=True)
                        # 生成并发送语音
                        try:
                            from .tts import synthesize
                            audio_path = await asyncio.to_thread(synthesize, reply, lang)
                            if audio_path and os.path.exists(audio_path):
                                if TELEGRAM_AVAILABLE:
                                    # 必须以二进制模式打开文件
                                    with open(audio_path, 'rb') as audio_file:
                                        await update.message.reply_voice(audio_file, filename=os.path.basename(audio_path))
                                    logger.info("Successfully sent voice")
                                else:
                                    logger.warning("Telegram模块不可用，跳过语音发送")
                                # 清理临时语音文件
                                os.remove(audio_path)
                            else:
                                logger.error("Audio file not generated or missing")
                        except Exception as e:
                            logger.error(f"Failed to generate or send voice: {e}", exc_info=True)
                        save_query(user_id, lang, intent, text, json.dumps(intent_data, ensure_ascii=False), json.dumps({"reply": reply}, ensure_ascii=False), now)
                        return
                await update.message.reply_text(format_not_found(lang))
                save_query(user_id, lang, intent, text, json.dumps(intent_data, ensure_ascii=False), json.dumps({"found": False}, ensure_ascii=False), now)
                return
            city_id, city_ru, city_zh, region_id, lat, lon = city
            codes = list_auto_codes_by_region(region_id)
            from .db import get_region_by_id
            region_row = get_region_by_id(region_id)
            region_ru = region_row[1] if region_row else ""
            region_zh = region_row[2] if region_row else ""
            reply = format_auto_result(lang, city_ru, city_zh, region_ru, region_zh, codes)
            await update.message.reply_text(reply)
            from .maps import generate_city_dual_map
            img_bytes = await asyncio.to_thread(generate_city_dual_map, region_ru or region_zh, city_ru, lat, lon)
            try:
                await update.message.reply_photo(InputFile(img_bytes, filename="map.png"))
            except Exception as e:
                logger.error(f"Failed to send map photo: {e}")
                try:
                    await update.message.reply_document(InputFile(img_bytes, filename="map.png"))
                    logger.info(f"Successfully sent map document")
                except Exception as e:
                    logger.error(f"Failed to send map document: {e}")
            try:
                from .tts import synthesize
                audio_path = await asyncio.to_thread(synthesize, reply, lang)
                if audio_path and os.path.exists(audio_path):
                    if TELEGRAM_AVAILABLE:
                        with open(audio_path, 'rb') as audio_file:
                            await update.message.reply_voice(audio_file, filename=os.path.basename(audio_path))
                        logger.info("Successfully sent voice")
                    else:
                        logger.warning("Telegram模块不可用，跳过语音发送")
                    # 清理临时语音文件
                    os.remove(audio_path)
                else:
                    logger.warning("Voice synthesis failed or audio file not generated")
            except Exception as e:
                logger.error(f"Failed to generate or send voice: {e}")
            save_query(user_id, lang, intent, text, json.dumps(intent_data, ensure_ascii=False), json.dumps({"reply": reply}, ensure_ascii=False), now)
            return
        if intent == "auto_code_to_region":
            code = intent_data.get("code", "")
            region = find_region_by_auto_code(code)
            if not region:
                await update.message.reply_text(format_not_found(lang))
                save_query(user_id, lang, intent, text, json.dumps(intent_data, ensure_ascii=False), json.dumps({"found": False}, ensure_ascii=False), now)
                return
            region_id, region_ru, region_zh = region
            codes = list_auto_codes_by_region(region_id)
            reply = format_auto_region_only(lang, region_ru, region_zh, codes)
            await update.message.reply_text(reply)
            from .maps import generate_city_dual_map
            from .db import get_city_by_region
            city_row = get_city_by_region(region_id)
            lat = city_row[3] if city_row else None
            lon = city_row[4] if city_row else None
            
            # 生成并发送地图
            try:
                img_bytes = await asyncio.to_thread(generate_city_dual_map, region_ru, city_row[1] if city_row else None, lat, lon)
                if img_bytes:
                    if TELEGRAM_AVAILABLE:
                        try:
                            await update.message.reply_photo(InputFile(img_bytes, filename="map.png"))
                            logger.info("Successfully sent map as photo")
                        except Exception as e:
                            logger.error(f"Failed to send map as photo: {e}")
                            try:
                                await update.message.reply_document(InputFile(img_bytes, filename="map.png"))
                                logger.info("Successfully sent map as document")
                            except Exception as e2:
                                logger.error(f"Failed to send map as document: {e2}")
                    else:
                        logger.warning("Telegram模块不可用，跳过地图发送")
                else:
                    logger.error("Map generation returned empty bytes")
            except Exception as e:
                logger.error(f"Error generating map: {e}", exc_info=True)
            
            # 生成并发送语音
            try:
                from .tts import synthesize
                audio_path = await asyncio.to_thread(synthesize, reply, lang)
                if audio_path and os.path.exists(audio_path):
                    if TELEGRAM_AVAILABLE:
                        with open(audio_path, 'rb') as audio_file:
                            await update.message.reply_voice(audio_file, filename=os.path.basename(audio_path))
                        logger.info("Successfully sent voice")
                    else:
                        logger.warning("Telegram模块不可用，跳过语音发送")
                    # 清理临时文件
                    try:
                        os.remove(audio_path)
                        logger.info(f"Cleaned up temporary audio file: {audio_path}")
                    except Exception as e:
                        logger.error(f"Failed to clean up audio file: {e}")
                else:
                    logger.error("Failed to generate audio or file not found")
            except Exception as e:
                logger.error(f"Error in TTS process: {e}", exc_info=True)
            save_query(user_id, lang, intent, text, json.dumps(intent_data, ensure_ascii=False), json.dumps({"reply": reply}, ensure_ascii=False), now)
            return
        if intent == "city_to_phone_code":
            city_name = intent_data.get("city", "").strip()
            city = find_city_by_name(city_name) or find_city_by_name_fuzzy(city_name)
            if not city:
                from .geocode import geocode_city
                geo = await asyncio.to_thread(geocode_city, city_name)
                if geo and geo.get("region"):
                            from .db import find_region_by_name
                            region_guess = find_region_by_name(geo["region"]) or find_region_by_name(city_name)
                            if region_guess:
                                region_id, region_ru, region_zh = region_guess
                                from .db import get_city_by_region
                                city_row = get_city_by_region(region_id)
                                codes = list_phone_codes_by_city(city_row[0]) if city_row else []
                                reply = format_phone_result(lang, geo.get("city"), None, region_ru, region_zh, codes or ["—"])
                                await update.message.reply_text(reply)
                                from .maps import generate_city_dual_map
                try:
                    img_bytes = await asyncio.to_thread(generate_city_dual_map, region_ru, geo.get("city"), geo.get("lat"), geo.get("lon"))
                    if img_bytes:
                        try:
                            await update.message.reply_photo(InputFile(img_bytes, filename="map.png"))
                            logger.info("Successfully sent map as photo")
                        except Exception as e:
                            logger.error(f"Failed to send map as photo: {e}")
                            try:
                                await update.message.reply_document(InputFile(img_bytes, filename="map.png"))
                                logger.info("Successfully sent map as document")
                            except Exception as e2:
                                logger.error(f"Failed to send map as document: {e2}")
                    else:
                        logger.error("Map generation returned empty bytes")
                except Exception as e:
                    logger.error(f"Error generating map: {e}", exc_info=True)
                # 生成并发送语音
                try:
                    from .tts import synthesize
                    audio_path = await asyncio.to_thread(synthesize, reply, lang)
                    if audio_path and os.path.exists(audio_path):
                        if TELEGRAM_AVAILABLE:
                            with open(audio_path, 'rb') as audio_file:
                                await update.message.reply_voice(audio_file, filename=os.path.basename(audio_path))
                            logger.info("Successfully sent voice")
                        else:
                            logger.warning("Telegram模块不可用，跳过语音发送")
                        # 清理临时语音文件
                        try:
                            os.remove(audio_path)
                            logger.info(f"Removed temporary audio file: {audio_path}")
                        except Exception as e:
                            logger.error(f"Failed to remove audio file: {e}")
                    else:
                        logger.error("Audio file not generated or missing")
                except Exception as e:
                    logger.error(f"Failed to generate or send voice: {e}", exc_info=True)
                save_query(user_id, lang, intent, text, json.dumps(intent_data, ensure_ascii=False), json.dumps({"reply": reply}, ensure_ascii=False), now)
                return
                await update.message.reply_text(format_not_found(lang))
                save_query(user_id, lang, intent, text, json.dumps(intent_data, ensure_ascii=False), json.dumps({"found": False}, ensure_ascii=False), now)
                return
            city_id, city_ru, city_zh, region_id, lat, lon = city
            region_row = get_region_by_id(region_id)
            region_ru = region_row[1] if region_row else ""
            region_zh = region_row[2] if region_row else ""
            codes = list_phone_codes_by_city(city_id)
            reply = format_phone_result(lang, city_ru, city_zh, region_ru, region_zh, codes)
            await update.message.reply_text(reply)
            
            # 生成并发送地图
            from .maps import generate_city_dual_map
            try:
                img_bytes = await asyncio.to_thread(generate_city_dual_map, region_ru, city_ru, lat, lon)
                if img_bytes:
                    try:
                        await update.message.reply_photo(InputFile(img_bytes, filename="map.png"))
                        logger.info("Successfully sent map as photo")
                    except Exception as e:
                        logger.error(f"Failed to send map as photo: {e}")
                        try:
                            await update.message.reply_document(InputFile(img_bytes, filename="map.png"))
                            logger.info("Successfully sent map as document")
                        except Exception as e2:
                            logger.error(f"Failed to send map as document: {e2}")
                else:
                    logger.error("Map generation returned empty bytes")
            except Exception as e:
                logger.error(f"Error generating map: {e}", exc_info=True)
            
            # 生成并发送语音
            try:
                from .tts import synthesize
                audio_path = await asyncio.to_thread(synthesize, reply, lang)
                if audio_path and os.path.exists(audio_path):
                    if TELEGRAM_AVAILABLE:
                        with open(audio_path, 'rb') as audio_file:
                            await update.message.reply_voice(audio_file, filename=os.path.basename(audio_path))
                        logger.info("Successfully sent voice")
                    else:
                        logger.warning("Telegram模块不可用，跳过语音发送")
                    # 清理临时语音文件
                    os.remove(audio_path)
                else:
                    logger.error("Audio file not generated or missing")
            except Exception as e:
                logger.error(f"Failed to generate or send voice: {e}", exc_info=True)
            save_query(user_id, lang, intent, text, json.dumps(intent_data, ensure_ascii=False), json.dumps({"reply": reply}, ensure_ascii=False), now)
            return
        if intent == "phone_code_to_city":
            code = intent_data.get("code", "")
            row = find_city_by_phone_code(code)
            if not row:
                await update.message.reply_text(format_not_found(lang))
                save_query(user_id, lang, intent, text, json.dumps(intent_data, ensure_ascii=False), json.dumps({"found": False}, ensure_ascii=False), now)
                return
            city_id, city_ru, city_zh, region_id, region_ru, region_zh, lat, lon = row
            codes = list_phone_codes_by_city(city_id)
            reply = format_phone_result(lang, city_ru, city_zh, region_ru, region_zh, codes)
            await update.message.reply_text(reply)
            from .maps import generate_city_dual_map
            
            # 生成并发送地图
            try:
                img_bytes = await asyncio.to_thread(generate_city_dual_map, region_ru, city_ru, lat, lon)
                if img_bytes:
                    try:
                        await update.message.reply_photo(InputFile(img_bytes, filename="map.png"))
                        logger.info("Successfully sent map as photo")
                    except Exception as e:
                        logger.error(f"Failed to send map as photo: {e}")
                        try:
                            await update.message.reply_document(InputFile(img_bytes, filename="map.png"))
                            logger.info("Successfully sent map as document")
                        except Exception as e2:
                            logger.error(f"Failed to send map as document: {e2}")
                else:
                    logger.error("Map generation returned empty bytes")
            except Exception as e:
                logger.error(f"Error generating map: {e}", exc_info=True)
            
            # 生成并发送语音
            try:
                from .tts import synthesize
                audio_path = await asyncio.to_thread(synthesize, reply, lang)
                if audio_path and os.path.exists(audio_path):
                    if TELEGRAM_AVAILABLE:
                        with open(audio_path, 'rb') as audio_file:
                            await update.message.reply_voice(audio_file, filename=os.path.basename(audio_path))
                        logger.info("Successfully sent voice")
                    else:
                        logger.warning("Telegram模块不可用，跳过语音发送")
                    # 清理临时语音文件
                    os.remove(audio_path)
                else:
                    logger.error("Audio file not generated or missing")
            except Exception as e:
                logger.error(f"Failed to generate or send voice: {e}", exc_info=True)
            save_query(user_id, lang, intent, text, json.dumps(intent_data, ensure_ascii=False), json.dumps({"reply": reply}, ensure_ascii=False), now)
            return
        
        # 处理车牌号码查询
        if intent == "license_plate":
            plate = intent_data.get("plate", "")
            region_code = intent_data.get("region_code", "")
            region = find_region_by_auto_code(region_code)
            
            if not region:
                await update.message.reply_text(format_not_found(lang))
                save_query(user_id, lang, intent, text, json.dumps(intent_data, ensure_ascii=False), json.dumps({"found": False}, ensure_ascii=False), now)
                return
            
            region_id, region_ru, region_zh = region
            reply = format_license_plate(lang, plate, region_ru, region_zh)
            await update.message.reply_text(reply)
            
            # 生成地图
            from .maps import generate_city_dual_map
            from .db import get_city_by_region
            city_row = get_city_by_region(region_id)
            lat = city_row[3] if city_row else None
            lon = city_row[4] if city_row else None
            
            try:
                img_bytes = await asyncio.to_thread(generate_city_dual_map, region_ru, city_row[1] if city_row else None, lat, lon)
                if img_bytes:
                    try:
                        await update.message.reply_photo(InputFile(img_bytes, filename="map.png"))
                        logger.info("Successfully sent map as photo")
                    except Exception as e:
                        logger.error(f"Failed to send map as photo: {e}")
                        try:
                            await update.message.reply_document(InputFile(img_bytes, filename="map.png"))
                            logger.info("Successfully sent map as document")
                        except Exception as e2:
                            logger.error(f"Failed to send map as document: {e2}")
                else:
                    logger.error("Map generation returned empty bytes")
            except Exception as e:
                logger.error(f"Error generating map: {e}", exc_info=True)
            
            # 生成语音播报
            try:
                from .tts import synthesize
                audio_path = await asyncio.to_thread(synthesize, reply, lang)
                if audio_path and os.path.exists(audio_path):
                    if TELEGRAM_AVAILABLE:
                        await update.message.reply_voice(InputFile(audio_path))
                        logger.info("Successfully sent voice")
                    else:
                        logger.warning("Telegram模块不可用，跳过语音发送")
                    # 清理临时语音文件
                    os.remove(audio_path)
                else:
                    logger.error("Audio file not generated or missing")
            except Exception as e:
                logger.error(f"Failed to generate or send voice: {e}", exc_info=True)
            
            save_query(user_id, lang, intent, text, json.dumps(intent_data, ensure_ascii=False), json.dumps({"reply": reply}, ensure_ascii=False), now)
            return
        
        await update.message.reply_text(format_not_found(lang))
        save_query(user_id, lang, intent, text, json.dumps(intent_data, ensure_ascii=False), json.dumps({"found": False}, ensure_ascii=False), now)
    except Exception as e:
        logger.error(f"Unexpected error in handle_text: {e}", exc_info=True)
        try:
            from .nlp import detect_language
            lang = detect_language(getattr(update.message, "text", "") or "")
            msg = "服务暂不可用，请稍后再试" if lang == "zh" else "Сервис недоступен, попробуйте позже"
            await update.message.reply_text(msg)
        except Exception as e2:
            logger.error(f"Failed to send error message: {e2}")

def run_bot():
    ensure_dirs()
    init_schema()
    from .db import seed_full_regions, seed_auto_codes_full, seed_phone_codes_capitals, seed_cities_full
    seed_full_regions()
    seed_auto_codes_full()
    seed_phone_codes_capitals()
    seed_cities_full()
    seed_minimal()
    
    # 只有在非自检模式下才导入telegram模块
    try:
        # 清理可能导致 httpx 报错的环境代理
        for k in [
            "HTTP_PROXY","HTTPS_PROXY","ALL_PROXY",
            "http_proxy","https_proxy","all_proxy",
            "SOCKS_PROXY","socks_proxy"
        ]:
            os.environ.pop(k, None)
        from telegram.request import HTTPXRequest
        # 为不同用途创建不同的请求实例
        req = HTTPXRequest(connection_pool_size=8, pool_timeout=5.0, read_timeout=10.0, write_timeout=10.0, connect_timeout=5.0, proxy={})
        get_updates_req = HTTPXRequest(connection_pool_size=8, pool_timeout=5.0, read_timeout=15.0, write_timeout=10.0, connect_timeout=5.0, proxy={})
        from telegram.ext import Application, CommandHandler, MessageHandler, filters
        app = Application.builder().token(TELEGRAM_BOT_TOKEN).request(req).get_updates_request(get_updates_req).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        async def on_error(update, context):
            try:
                from .nlp import detect_language
                txt = getattr(getattr(update, "message", None), "text", "") or ""
                lang = detect_language(txt)
                msg = "服务暂不可用，请稍后再试" if lang == "zh" else "Сервис недоступен, попробуйте позже"
                if update and update.effective_chat:
                    await update.effective_chat.send_message(msg)
            except Exception as e2:
                logger.error(f"Failed to send error message: {e2}")
        app.add_error_handler(on_error)
        logger.info("Starting bot...")
        app.run_polling()
    except ImportError as e:
        logger.warning(f"Telegram dependencies not installed: {e}")
        logger.info("Bot can only run in self-test mode without telegram dependencies")

def run_selftest():
    ensure_dirs()
    init_schema()
    seed_minimal()
    samples = [
        "莫斯科车牌代码",
        "199 是哪个地区",
        "圣彼得堡电话区号",
        "812 对应哪个城市",
        "Екатеринбург номер региона",
        "495",
        "Казань код региона",
        # 测试车牌号码识别
        "А123ВЕ199",
        "M345AB777",
        "车牌号码 А567КМ123",
    ]
    print("Starting self-test...")
    print("=" * 60)
    
    for s in samples:
        print(f"\nTest input: '{s}'")
        print("-" * 40)
        
        # 测试语言检测
        try:
            lang = detect_language(s)
            print(f"✓ Language detection: {lang}")
        except Exception as e:
            print(f"✗ Language detection failed: {e}")
            lang = "unknown"
        
        # 测试意图解析
        try:
            intent = parse_intent(s)
            print(f"✓ Intent parsing: {intent.get('intent')}")
            if intent.get('city'):
                print(f"  City: {intent.get('city')}")
            if intent.get('code'):
                print(f"  Code: {intent.get('code')}")
            if intent.get('license_plate'):
                print(f"  License plate: {intent.get('license_plate')}")
        except Exception as e:
            print(f"✗ Intent parsing failed: {e}")
        
        # 测试数据库查询
        try:
            intent = parse_intent(s)
            intent_type = intent.get('intent')
            
            if intent_type == "city_to_auto_code":
                city_name = intent.get("city", "").strip()
                if city_name:
                    city = find_city_by_name(city_name) or find_city_by_name_fuzzy(city_name)
                    if city:
                        print(f"✓ City found: {city[1]} ({city[2]})")
                        codes = list_auto_codes_by_region(city[3])
                        if codes:
                            print(f"  Auto codes: {', '.join(codes)}")
                    else:
                        print(f"⚠ City not found: {city_name}")
            
            elif intent_type == "auto_code_to_region":
                code = intent.get("code", "")
                if code:
                    region = find_region_by_auto_code(code)
                    if region:
                        print(f"✓ Region found: {region[1]} ({region[2]})")
                        codes = list_auto_codes_by_region(region[0])
                        if codes:
                            print(f"  Auto codes: {', '.join(codes)}")
                    else:
                        print(f"⚠ Region not found for code: {code}")
        
        except Exception as e:
            print(f"✗ Database test failed: {e}")
    
    print("\n" + "=" * 60)
    print("Self-test completed!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        run_selftest()
    else:
        if not TELEGRAM_BOT_TOKEN:
            print("Missing TELEGRAM_BOT_TOKEN")
        else:
            run_bot()
