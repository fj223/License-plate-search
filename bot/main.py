import os
import asyncio
import json
import datetime
import argparse
from .config import TELEGRAM_BOT_TOKEN, ensure_dirs
from .db import init_schema, seed_minimal, find_city_by_name, find_region_by_auto_code, list_auto_codes_by_region, find_city_by_phone_code, list_phone_codes_by_city, save_query, find_city_by_name_fuzzy
from .nlp import detect_language, parse_intent
from .reply_templates import format_auto_result, format_auto_region_only, format_phone_result, format_not_found

async def start(update, context):
    await update.message.reply_text("Введите город, код региона или телефонный код. 支持中文输入。")

async def handle_text(update, context):
    try:
        text = update.message.text or ""
        from .nlp import detect_language
        lang = detect_language(text)
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
                        from telegram import InputFile
                        img_bytes = await asyncio.to_thread(generate_city_dual_map, region_ru, geo.get("city"), geo.get("lat"), geo.get("lon"))
                        try:
                            await update.message.reply_photo(InputFile(img_bytes, filename="map.png"))
                        except Exception:
                            try:
                                await update.message.reply_document(InputFile(img_bytes, filename="map.png"))
                            except Exception:
                                pass
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
            from telegram import InputFile
            img_bytes = await asyncio.to_thread(generate_city_dual_map, region_ru or region_zh, city_ru, lat, lon)
            try:
                await update.message.reply_photo(InputFile(img_bytes, filename="map.png"))
            except Exception:
                try:
                    await update.message.reply_document(InputFile(img_bytes, filename="map.png"))
                except Exception:
                    pass
            try:
                from .tts import synthesize
                audio_path = await asyncio.to_thread(synthesize, reply, lang)
                await update.message.reply_voice(open(audio_path, "rb"))
            except Exception:
                pass
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
            from telegram import InputFile
            from .db import get_city_by_region
            city_row = get_city_by_region(region_id)
            lat = city_row[3] if city_row else None
            lon = city_row[4] if city_row else None
            img_bytes = await asyncio.to_thread(generate_city_dual_map, region_ru, city_row[1] if city_row else None, lat, lon)
            try:
                await update.message.reply_photo(InputFile(img_bytes, filename="map.png"))
            except Exception:
                try:
                    await update.message.reply_document(InputFile(img_bytes, filename="map.png"))
                except Exception:
                    pass
            try:
                from .tts import synthesize
                audio_path = await asyncio.to_thread(synthesize, reply, lang)
                await update.message.reply_voice(open(audio_path, "rb"))
            except Exception:
                pass
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
                        from telegram import InputFile
                        img_bytes = await asyncio.to_thread(generate_city_dual_map, region_ru, geo.get("city"), geo.get("lat"), geo.get("lon"))
                        try:
                            await update.message.reply_photo(InputFile(img_bytes, filename="map.png"))
                        except Exception:
                            try:
                                await update.message.reply_document(InputFile(img_bytes, filename="map.png"))
                            except Exception:
                                pass
                        save_query(user_id, lang, intent, text, json.dumps(intent_data, ensure_ascii=False), json.dumps({"reply": reply}, ensure_ascii=False), now)
                        return
                await update.message.reply_text(format_not_found(lang))
                save_query(user_id, lang, intent, text, json.dumps(intent_data, ensure_ascii=False), json.dumps({"found": False}, ensure_ascii=False), now)
                return
            city_id, city_ru, city_zh, region_id, lat, lon = city
            codes = list_phone_codes_by_city(city_id)
            from .db import get_region_by_id
            region_row = get_region_by_id(region_id)
            region_ru = region_row[1] if region_row else ""
            region_zh = region_row[2] if region_row else ""
            reply = format_phone_result(lang, city_ru, city_zh, region_ru, region_zh, codes)
            await update.message.reply_text(reply)
            from .maps import generate_city_dual_map
            from telegram import InputFile
            img_bytes = await asyncio.to_thread(generate_city_dual_map, region_ru, city_ru, lat, lon)
            try:
                await update.message.reply_photo(InputFile(img_bytes, filename="map.png"))
            except Exception:
                try:
                    await update.message.reply_document(InputFile(img_bytes, filename="map.png"))
                except Exception:
                    pass
            try:
                from .tts import synthesize
                audio_path = await asyncio.to_thread(synthesize, reply, lang)
                await update.message.reply_voice(open(audio_path, "rb"))
            except Exception:
                pass
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
            from telegram import InputFile
            img_bytes = await asyncio.to_thread(generate_city_dual_map, region_ru, city_ru, lat, lon)
            try:
                await update.message.reply_photo(InputFile(img_bytes, filename="map.png"))
            except Exception:
                try:
                    await update.message.reply_document(InputFile(img_bytes, filename="map.png"))
                except Exception:
                    pass
            try:
                from .tts import synthesize
                audio_path = await asyncio.to_thread(synthesize, reply, lang)
                await update.message.reply_voice(open(audio_path, "rb"))
            except Exception:
                pass
            save_query(user_id, lang, intent, text, json.dumps(intent_data, ensure_ascii=False), json.dumps({"reply": reply}, ensure_ascii=False), now)
            return
        await update.message.reply_text(format_not_found(lang))
        save_query(user_id, lang, intent, text, json.dumps(intent_data, ensure_ascii=False), json.dumps({"found": False}, ensure_ascii=False), now)
    except Exception:
        try:
            from .nlp import detect_language
            lang = detect_language(getattr(update.message, "text", "") or "")
            msg = "服务暂不可用，请稍后再试" if lang == "zh" else "Сервис недоступен, попробуйте позже"
            await update.message.reply_text(msg)
        except Exception:
            pass

def run_bot():
    ensure_dirs()
    init_schema()
    from .db import seed_full_regions, seed_auto_codes_full, seed_phone_codes_capitals, seed_cities_full
    seed_full_regions()
    seed_auto_codes_full()
    seed_phone_codes_capitals()
    seed_cities_full()
    seed_minimal()
    # 清理可能导致 httpx 报错的环境代理
    for k in [
        "HTTP_PROXY","HTTPS_PROXY","ALL_PROXY",
        "http_proxy","https_proxy","all_proxy",
        "SOCKS_PROXY","socks_proxy"
    ]:
        os.environ.pop(k, None)
    from telegram.request import HTTPXRequest
    req = HTTPXRequest(connection_pool_size=8, pool_timeout=5.0, read_timeout=10.0, write_timeout=10.0, connect_timeout=5.0, proxy={})
    from telegram.ext import Application, CommandHandler, MessageHandler, filters
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).request(req).get_updates_request(req).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    async def on_error(update, context):
        try:
            from .nlp import detect_language
            txt = getattr(getattr(update, "message", None), "text", "") or ""
            lang = detect_language(txt)
            msg = "服务暂不可用，请稍后再试" if lang == "zh" else "Сервис недоступен, попробуйте позже"
            if update and update.effective_chat:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=msg)
        except Exception:
            pass
    app.add_error_handler(on_error)
    app.run_polling()

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
    ]
    for s in samples:
        lang = detect_language(s)
        intent = parse_intent(s)
        print(lang, intent)

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
