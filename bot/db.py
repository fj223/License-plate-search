import sqlite3
import os
from .config import DATA_DB_PATH

def get_conn():
    return sqlite3.connect(DATA_DB_PATH)

def init_schema():
    conn = get_conn()
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS regions (id INTEGER PRIMARY KEY, name_ru TEXT, name_zh TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS cities (id INTEGER PRIMARY KEY, name_ru TEXT, name_zh TEXT, region_id INTEGER, aliases TEXT, lat REAL, lon REAL)")
    c.execute("CREATE TABLE IF NOT EXISTS auto_codes (id INTEGER PRIMARY KEY, code TEXT, region_id INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS phone_codes (id INTEGER PRIMARY KEY, area_code TEXT, city_id INTEGER, region_id INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS queries (id INTEGER PRIMARY KEY, user_id TEXT, language TEXT, intent TEXT, raw_text TEXT, parsed_entities TEXT, result TEXT, created_at TEXT)")
    conn.commit()
    conn.close()

def seed_minimal():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM cities")
    cities_count = c.fetchone()[0]
    if cities_count == 0:
        names = [
            ("Москва", "莫斯科", "Мск, Moscow", 55.7558, 37.6173),
            ("Санкт-Петербург", "圣彼得堡", "Питер, SPb", 59.9343, 30.3351),
            ("Новосибирск", "新西伯利亚", "", 55.0302, 82.9206),
            ("Екатеринбург", "叶卡捷琳堡", "", 56.8389, 60.6057),
            ("Нижний Новгород", "下诺夫哥罗德", "", 56.2965, 43.9361),
            ("Казань", "喀山", "", 55.8304, 49.0661),
        ]
        rows = []
        for name_ru, name_zh, aliases, lat, lon in names:
            c.execute("SELECT id FROM regions WHERE name_ru=?", (name_ru,))
            r = c.fetchone()
            region_id = r[0] if r else None
            rows.append((name_ru, name_zh, region_id, aliases, lat, lon))
        c.executemany("INSERT INTO cities(name_ru,name_zh,region_id,aliases,lat,lon) VALUES(?,?,?,?,?,?)", rows)
    c.execute("SELECT COUNT(*) FROM auto_codes")
    ac_count = c.fetchone()[0]
    if ac_count == 0:
        pairs = {
            "Москва": ["77","97","99","177","197","199","777"],
            "Санкт-Петербург": ["78","98","178"],
            "Новосибирская область": ["54"],
            "Свердловская область": ["66","96","196"],
            "Нижегородская область": ["52","152"],
            "Республика Татарстан": ["16","116"],
        }
        to_ac = []
        for region_name, codes in pairs.items():
            c.execute("SELECT id FROM regions WHERE name_ru=?", (region_name,))
            r = c.fetchone()
            if not r:
                continue
            region_id = r[0]
            for code in codes:
                to_ac.append((code, region_id))
        c.executemany("INSERT INTO auto_codes(code,region_id) VALUES(?,?)", to_ac)
    c.execute("SELECT COUNT(*) FROM phone_codes")
    pc_count = c.fetchone()[0]
    if pc_count == 0:
        pairs = {
            "Москва": ["495","499"],
            "Санкт-Петербург": ["812"],
            "Новосибирск": ["383"],
            "Екатеринбург": ["343"],
            "Нижний Новгород": ["831"],
            "Казань": ["843"],
        }
        to_pc = []
        for city_name, codes in pairs.items():
            c.execute("SELECT id,region_id FROM cities WHERE name_ru=?", (city_name,))
            r = c.fetchone()
            if not r:
                continue
            city_id, region_id = r
            for code in codes:
                to_pc.append((code, city_id, region_id))
        c.executemany("INSERT INTO phone_codes(area_code,city_id,region_id) VALUES(?,?,?)", to_pc)
    conn.commit()
    conn.close()

def seed_full_regions():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT name_ru FROM regions")
    existing = set(r[0] for r in c.fetchall())
    regions_full = [
        "Москва",
        "Санкт-Петербург",
        "Республика Адыгея",
        "Республика Башкортостан",
        "Республика Бурятия",
        "Республика Алтай",
        "Республика Дагестан",
        "Республика Ингушетия",
        "Кабардино-Балкарская Республика",
        "Республика Калмыкия",
        "Карачаево-Черкесская Республика",
        "Республика Карелия",
        "Республика Коми",
        "Республика Марий Эл",
        "Республика Мордовия",
        "Республика Саха (Якутия)",
        "Республика Северная Осетия — Алания",
        "Республика Татарстан",
        "Республика Тыва",
        "Удмуртская Республика",
        "Республика Хакасия",
        "Чеченская Республика",
        "Чувашская Республика",
        "Алтайский край",
        "Краснодарский край",
        "Красноярский край",
        "Приморский край",
        "Ставропольский край",
        "Хабаровский край",
        "Амурская область",
        "Архангельская область",
        "Астраханская область",
        "Белгородская область",
        "Брянская область",
        "Владимирская область",
        "Волгоградская область",
        "Вологодская область",
        "Воронежская область",
        "Ивановская область",
        "Иркутская область",
        "Калининградская область",
        "Калужская область",
        "Камчатский край",
        "Кемеровская область — Кузбасс",
        "Кировская область",
        "Костромская область",
        "Курганская область",
        "Курская область",
        "Ленинградская область",
        "Липецкая область",
        "Магаданская область",
        "Московская область",
        "Мурманская область",
        "Нижегородская область",
        "Новгородская область",
        "Новосибирская область",
        "Омская область",
        "Оренбургская область",
        "Орловская область",
        "Пензенская область",
        "Пермский край",
        "Псковская область",
        "Ростовская область",
        "Рязанская область",
        "Самарская область",
        "Саратовская область",
        "Сахалинская область",
        "Свердловская область",
        "Смоленская область",
        "Тамбовская область",
        "Тверская область",
        "Томская область",
        "Тульская область",
        "Тюменская область",
        "Ульяновская область",
        "Челябинская область",
        "Ярославская область",
        "Забайкальский край",
        "Еврейская автономная область",
        "Ненецкий автономный округ",
        "Ханты-Мансийский автономный округ — Югра",
        "Чукотский автономный округ",
        "Ямало-Ненецкий автономный округ",
        "Севастополь",
        "Республика Крым",
    ]
    to_insert = [(name, None) for name in regions_full if name not in existing]
    if to_insert:
        c.executemany("INSERT INTO regions(name_ru,name_zh) VALUES(?,?)", to_insert)
    conn.commit()
    conn.close()

def seed_auto_codes_full():
    conn = get_conn()
    c = conn.cursor()
    mapping = {
        "Москва": ["77","97","99","177","197","199","777"],
        "Санкт-Петербург": ["78","98","178"],
        "Московская область": ["50","90","150"],
        "Ленинградская область": ["47","147"],
        "Республика Татарстан": ["16","116"],
        "Республика Башкортостан": ["02","102","702"],
        "Республика Адыгея": ["01","101"],
        "Республика Алтай": ["04","104"],
        "Республика Бурятия": ["03","103"],
        "Республика Дагестан": ["05","105"],
        "Республика Ингушетия": ["06","106"],
        "Кабардино-Балкарская Республика": ["07","107"],
        "Республика Калмыкия": ["08","108"],
        "Карачаево-Черкесская Республика": ["09","109"],
        "Республика Карелия": ["10","110"],
        "Республика Коми": ["11","111"],
        "Республика Марий Эл": ["12","112"],
        "Республика Мордовия": ["13","113"],
        "Республика Саха (Якутия)": ["14","114"],
        "Республика Северная Осетия — Алания": ["15","115"],
        "Республика Тыва": ["17","117"],
        "Республика Хакасия": ["19","119"],
        "Удмуртская Республика": ["18","118"],
        "Чеченская Республика": ["95"],
        "Чувашская Республика": ["21","121"],
        "Алтайский край": ["22"],
        "Краснодарский край": ["23","93","123"],
        "Красноярский край": ["24","84","124"],
        "Приморский край": ["25","125"],
        "Ставропольский край": ["26","126"],
        "Хабаровский край": ["27"],
        "Амурская область": ["28"],
        "Архангельская область": ["29"],
        "Астраханская область": ["30"],
        "Белгородская область": ["31"],
        "Брянская область": ["32"],
        "Владимирская область": ["33"],
        "Волгоградская область": ["34","134"],
        "Вологодская область": ["35"],
        "Воронежская область": ["36","136"],
        "Ивановская область": ["37"],
        "Иркутская область": ["38","138"],
        "Калининградская область": ["39"],
        "Калужская область": ["40"],
        "Камчатский край": ["41"],
        "Кемеровская область — Кузбасс": ["42","142"],
        "Кировская область": ["43"],
        "Костромская область": ["44"],
        "Курганская область": ["45"],
        "Курская область": ["46"],
        "Липецкая область": ["48"],
        "Магаданская область": ["49"],
        "Нижегородская область": ["52","152"],
        "Новгородская область": ["53"],
        "Новосибирская область": ["54"],
        "Омская область": ["55"],
        "Оренбургская область": ["56"],
        "Орловская область": ["57"],
        "Пензенская область": ["58"],
        "Пермский край": ["59","81","159"],
        "Псковская область": ["60"],
        "Ростовская область": ["61","161"],
        "Рязанская область": ["62"],
        "Самарская область": ["63","163"],
        "Саратовская область": ["64","164"],
        "Сахалинская область": ["65"],
        "Свердловская область": ["66","96","196"],
        "Смоленская область": ["67"],
        "Тамбовская область": ["68"],
        "Тверская область": ["69"],
        "Томская область": ["70"],
        "Тульская область": ["71"],
        "Тюменская область": ["72"],
        "Ульяновская область": ["73"],
        "Челябинская область": ["74","174"],
        "Забайкальский край": ["75"],
        "Еврейская автономная область": ["79"],
        "Ненецкий автономный округ": ["83"],
        "Ханты-Мансийский автономный округ — Югра": ["86","186"],
        "Чукотский автономный округ": ["87"],
        "Ямало-Ненецкий автономный округ": ["89"],
        "Севастополь": ["92"],
        "Республика Крым": ["82"],
    }
    for region_name, codes in mapping.items():
        c.execute("SELECT id FROM regions WHERE name_ru=?", (region_name,))
        r = c.fetchone()
        if not r:
            continue
        region_id = r[0]
        for code in codes:
            c.execute("SELECT 1 FROM auto_codes WHERE code=? AND region_id=?", (code, region_id))
            exists = c.fetchone()
            if not exists:
                c.execute("INSERT INTO auto_codes(code,region_id) VALUES(?,?)", (code, region_id))
    conn.commit()
    conn.close()

def seed_cities_full():
    conn = get_conn()
    c = conn.cursor()
    pairs = [
        ("Москва", "Москва"),
        ("Санкт-Петербург", "Санкт-Петербург"),
        ("Новосибирск", "Новосибирская область"),
        ("Екатеринбург", "Свердловская область"),
        ("Нижний Новгород", "Нижегородская область"),
        ("Казань", "Республика Татарстан"),
        ("Челябинск", "Челябинская область"),
        ("Самара", "Самарская область"),
        ("Омск", "Омская область"),
        ("Ростов-на-Дону", "Ростовская область"),
        ("Уфа", "Республика Башкортостан"),
        ("Красноярск", "Красноярский край"),
        ("Пермь", "Пермский край"),
        ("Воронеж", "Воронежская область"),
        ("Волгоград", "Волгоградская область"),
        ("Краснодар", "Краснодарский край"),
        ("Саратов", "Саратовская область"),
        ("Тюмень", "Тюменская область"),
        ("Тольятти", "Самарская область"),
        ("Ижевск", "Удмуртская Республика"),
        ("Барнаул", "Алтайский край"),
        ("Ульяновск", "Ульяновская область"),
        ("Иркутск", "Иркутская область"),
        ("Хабаровск", "Хабаровский край"),
        ("Ярославль", "Ярославская область"),
        ("Владивосток", "Приморский край"),
        ("Махачкала", "Республика Дагестан"),
        ("Томск", "Томская область"),
        ("Оренбург", "Оренбургская область"),
        ("Кемерово", "Кемеровская область — Кузбасс"),
        ("Новокузнецк", "Кемеровская область — Кузбасс"),
        ("Рязань", "Рязанская область"),
        ("Астрахань", "Астраханская область"),
        ("Набережные Челны", "Республика Татарстан"),
        ("Пенза", "Пензенская область"),
        ("Липецк", "Липецкая область"),
        ("Тула", "Тульская область"),
        ("Калининград", "Калининградская область"),
        ("Чебоксары", "Чувашская Республика"),
        ("Брянск", "Брянская область"),
        ("Курск", "Курская область"),
        ("Киров", "Кировская область"),
        ("Орёл", "Орловская область"),
        ("Белгород", "Белгородская область"),
        ("Владимир", "Владимирская область"),
        ("Ставрополь", "Ставропольский край"),
        ("Нижний Тагил", "Свердловская область"),
        ("Тамбов", "Тамбовская область"),
        ("Псков", "Псковская область"),
        ("Тверь", "Тверская область"),
        ("Сочи", "Краснодарский край"),
        ("Калуга", "Калужская область"),
        ("Смоленск", "Смоленская область"),
        ("Якутск", "Республика Саха (Якутия)"),
        ("Кемерово", "Кемеровская область — Кузбасс"),
        ("Сургут", "Ханты-Мансийский автономный округ — Югра"),
        ("Тобольск", "Тюменская область"),
        ("Архангельск", "Архангельская область"),
        ("Мурманск", "Мурманская область"),
        ("Петрозаводск", "Республика Карелия"),
        ("Сыктывкар", "Республика Коми"),
        ("Владикавказ", "Республика Северная Осетия — Алания"),
        ("Грозный", "Чеченская Республика"),
        ("Нальчик", "Кабардино-Балкарская Республика"),
        ("Элиста", "Республика Калмыкия"),
        ("Черкесск", "Карачаево-Черкесская Республика"),
        ("Улан-Удэ", "Республика Бурятия"),
        ("Чита", "Забайкальский край"),
        ("Биробиджан", "Еврейская автономная область"),
        ("Ханты-Мансийск", "Ханты-Мансийский автономный округ — Югра"),
        ("Нарьян-Мар", "Ненецкий автономный округ"),
        ("Анадырь", "Чукотский автономный округ"),
        ("Симферополь", "Республика Крым"),
        ("Севастополь", "Севастополь"),
    ]
    for city_name, region_name in pairs:
        c.execute("SELECT id FROM regions WHERE name_ru=?", (region_name,))
        rr = c.fetchone()
        if not rr:
            continue
        region_id = rr[0]
        c.execute("SELECT id FROM cities WHERE name_ru=? AND region_id=?", (city_name, region_id))
        cr = c.fetchone()
        if not cr:
            c.execute("INSERT INTO cities(name_ru,name_zh,region_id,aliases,lat,lon) VALUES(?,?,?,?,?,?)", (city_name, None, region_id, "", None, None))
    conn.commit()
    conn.close()

def seed_phone_codes_capitals(geocode_fn=None):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM phone_codes")
    existing_count = c.fetchone()[0]
    mapping = [
        ("Москва", "Москва", ["495","499"]),
        ("Санкт-Петербург", "Санкт-Петербург", ["812"]),
        ("Республика Татарстан", "Казань", ["843"]),
        ("Республика Башкортостан", "Уфа", ["347"]),
        ("Пермский край", "Пермь", ["342"]),
        ("Самарская область", "Самара", ["846"]),
        ("Саратовская область", "Саратов", ["8452"]),
        ("Нижегородская область", "Нижний Новгород", ["831"]),
        ("Ростовская область", "Ростов-на-Дону", ["863"]),
        ("Краснодарский край", "Краснодар", ["861"]),
        ("Ставропольский край", "Ставрополь", ["8652"]),
        ("Воронежская область", "Воронеж", ["473"]),
        ("Волгоградская область", "Волгоград", ["8442"]),
        ("Белгородская область", "Белгород", ["4722"]),
        ("Курская область", "Курск", ["4712"]),
        ("Брянская область", "Брянск", ["4832"]),
        ("Смоленская область", "Смоленск", ["4812"]),
        ("Орловская область", "Орёл", ["4862"]),
        ("Липецкая область", "Липецк", ["4742"]),
        ("Тамбовская область", "Тамбов", ["4752"]),
        ("Тверская область", "Тверь", ["4822"]),
        ("Ярославская область", "Ярославль", ["4852"]),
        ("Ивановская область", "Иваново", ["4932"]),
        ("Владимирская область", "Владимир", ["4922"]),
        ("Костромская область", "Кострома", ["4942"]),
        ("Тульская область", "Тула", ["4872"]),
        ("Рязанская область", "Рязань", ["4912"]),
        ("Калужская область", "Калуга", ["4842"]),
        ("Калининградская область", "Калининград", ["4012"]),
        ("Псковская область", "Псков", ["8112"]),
        ("Новгородская область", "Великий Новгород", ["8162"]),
        ("Вологодская область", "Вологда", ["8172"]),
        ("Архангельская область", "Архангельск", ["8182"]),
        ("Мурманская область", "Мурманск", ["8152"]),
        ("Республика Карелия", "Петрозаводск", ["8142"]),
        ("Республика Коми", "Сыктывкар", ["8212"]),
        ("Ненецкий автономный округ", "Нарьян-Мар", ["81853"]),
        ("Севастополь", "Севастополь", ["8692"]),
        ("Республика Крым", "Симферополь", ["3652"]),
        ("Свердловская область", "Екатеринбург", ["343"]),
        ("Челябинская область", "Челябинск", ["351"]),
        ("Тюменская область", "Тюмень", ["3452"]),
        ("Курганская область", "Курган", ["3522"]),
        ("Оренбургская область", "Оренбург", ["3532"]),
        ("Омская область", "Омск", ["3812"]),
        ("Томская область", "Томск", ["3822"]),
        ("Новосибирская область", "Новосибирск", ["383"]),
        ("Кемеровская область — Кузбасс", "Кемерово", ["3842"]),
        ("Алтайский край", "Барнаул", ["3852"]),
        ("Республика Алтай", "Горно-Алтайск", ["38822"]),
        ("Красноярский край", "Красноярск", ["391"]),
        ("Иркутская область", "Иркутск", ["3952"]),
        ("Забайкальский край", "Чита", ["3022"]),
        ("Республика Бурятия", "Улан-Удэ", ["3012"]),
        ("Республика Тыва", "Кызыл", ["39422"]),
        ("Республика Хакасия", "Абакан", ["3902"]),
        ("Республика Саха (Якутия)", "Якутск", ["4112"]),
        ("Хабаровский край", "Хабаровск", ["4212"]),
        ("Приморский край", "Владивосток", ["423"]),
        ("Еврейская автономная область", "Биробиджан", ["42622"]),
        ("Сахалинская область", "Южно-Сахалинск", ["4242"]),
        ("Магаданская область", "Магадан", ["4132"]),
        ("Камчатский край", "Петропавловск-Камчатский", ["4152"]),
        ("Чукотский автономный округ", "Анадырь", ["42722"]),
        ("Удмуртская Республика", "Ижевск", ["3412"]),
        ("Кировская область", "Киров", ["8332"]),
        ("Республика Калмыкия", "Элиста", ["84722"]),
        ("Кабардино-Балкарская Республика", "Нальчик", ["8662"]),
        ("Карачаево-Черкесская Республика", "Черкесск", ["8782"]),
        ("Республика Дагестан", "Махачкала", ["8722"]),
        ("Республика Ингушетия", "Магас", ["8734"]),
        ("Чеченская Республика", "Грозный", ["8712"]),
        ("Республика Северная Осетия — Алания", "Владикавказ", ["8672"]),
        ("Чувашская Республика", "Чебоксары", ["8352"]),
        ("Республика Марий Эл", "Йошкар-Ола", ["8362"]),
        ("Пензенская область", "Пенза", ["8412"]),
        ("Ульяновская область", "Ульяновск", ["8422"]),
        ("Астраханская область", "Астрахань", ["8512"]),
        ("Амурская область", "Благовещенск", ["4162"]),
        ("Архангельская область", "Архангельск", ["8182"]),
    ]
    for region_name, city_name, codes in mapping:
        c.execute("SELECT id FROM regions WHERE name_ru=?", (region_name,))
        rr = c.fetchone()
        if not rr:
            continue
        region_id = rr[0]
        c.execute("SELECT id,lat,lon FROM cities WHERE name_ru=? AND region_id=?", (city_name, region_id))
        cr = c.fetchone()
        if not cr:
            lat = None
            lon = None
            if geocode_fn:
                g = geocode_fn(city_name)
                if g:
                    lat = g.get("lat")
                    lon = g.get("lon")
            c.execute("INSERT INTO cities(name_ru,name_zh,region_id,aliases,lat,lon) VALUES(?,?,?,?,?,?)", (city_name, None, region_id, "", lat, lon))
            city_id = c.lastrowid
        else:
            city_id = cr[0]
        for ac in codes:
            c.execute("SELECT COUNT(*) FROM phone_codes WHERE area_code=? AND city_id=?", (ac, city_id))
            if c.fetchone()[0] == 0:
                c.execute("INSERT INTO phone_codes(area_code,city_id,region_id) VALUES(?,?,?)", (ac, city_id, region_id))
    conn.commit()
    conn.close()

def seed_phone_codes_capitals():
    try:
        from .geocode import geocode_city
    except Exception:
        geocode_city = None
    conn = get_conn()
    c = conn.cursor()
    mapping = {
        "Уфа": ["347"], "Пермь": ["342"], "Самара": ["846"], "Ростов-на-Дону": ["863"],
        "Волгоград": ["8442"], "Воронеж": ["473"], "Омск": ["3812"], "Томск": ["3822"],
        "Тула": ["4872"], "Тюмень": ["3452"], "Челябинск": ["351"], "Ярославль": ["4852"],
        "Иркутск": ["3952"], "Кемерово": ["3842"], "Красноярск": ["391"], "Хабаровск": ["4212"],
        "Владивосток": ["423"], "Якутск": ["4112"], "Улан-Удэ": ["3012"], "Барнаул": ["3852"],
        "Астрахань": ["8512"], "Белгород": ["4722"], "Брянск": ["4832"], "Иваново": ["4932"],
        "Калуга": ["4842"], "Кострома": ["4942"], "Курск": ["4712"], "Липецк": ["4742"],
        "Псков": ["8112"], "Тверь": ["4822"], "Тамбов": ["4752"], "Смоленск": ["4812"],
        "Орел": ["4862"], "Пенза": ["8412"], "Ульяновск": ["8422"], "Оренбург": ["3532"],
        "Киров": ["8332"], "Курган": ["3522"], "Набережные Челны": ["8552"], "Нижний Тагил": ["3435"],
    }
    for city_name, codes in mapping.items():
        c.execute("SELECT id,region_id FROM cities WHERE name_ru=?", (city_name,))
        row = c.fetchone()
        if not row and geocode_city:
            geo = geocode_city(city_name)
            if geo:
                region = find_region_by_name(geo.get("region") or "")
                region_id = region[0] if region else None
                c.execute("INSERT INTO cities(name_ru,name_zh,region_id,aliases,lat,lon) VALUES(?,?,?,?,?,?)", (city_name, None, region_id, "", geo.get("lat"), geo.get("lon")))
                city_id = c.lastrowid
            else:
                continue
        else:
            if not row:
                continue
            city_id, region_id = row
        for code in codes:
            c.execute("INSERT INTO phone_codes(area_code,city_id,region_id) VALUES(?,?,?)", (code, city_id, region_id))
    conn.commit()
    conn.close()

def find_city_by_name(name):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id,name_ru,name_zh,region_id,lat,lon FROM cities WHERE lower(name_ru)=lower(?) OR lower(name_zh)=lower(?)", (name, name))
    row = c.fetchone()
    if not row:
        c.execute("SELECT id,name_ru,name_zh,region_id,lat,lon FROM cities WHERE lower(name_ru) LIKE lower(?)", (f"%{name}%",))
        row = c.fetchone()
    if not row:
        c.execute("SELECT id,name_ru,name_zh,region_id,lat,lon FROM cities WHERE aliases LIKE ?", (f"%{name}%",))
        row = c.fetchone()
    conn.close()
    return row

def find_city_by_name_fuzzy(text):
    conn = get_conn()
    c = conn.cursor()
    q = text.lower().strip()
    tokens = [t for t in q.replace(',', ' ').split() if t]
    if tokens:
        key = tokens[0]
        c.execute("SELECT id,name_ru,name_zh,region_id,lat,lon FROM cities WHERE lower(name_ru) LIKE ? ORDER BY length(name_ru) ASC", (f"%{key}%",))
        row = c.fetchone()
        if row:
            conn.close()
            return row
    c.execute("SELECT id,name_ru,name_zh,region_id,lat,lon FROM cities WHERE aliases LIKE ? ORDER BY length(name_ru) ASC", (f"%{q}%",))
    row = c.fetchone()
    conn.close()
    return row

def get_region_by_id(region_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id,name_ru,name_zh FROM regions WHERE id=?", (region_id,))
    row = c.fetchone()
    conn.close()
    return row

def find_region_by_name(name):
    conn = get_conn()
    c = conn.cursor()
    like = f"%{name}%"
    c.execute("SELECT id,name_ru,name_zh FROM regions WHERE lower(name_ru) LIKE lower(?) OR lower(name_zh) LIKE lower(?)", (like, like))
    row = c.fetchone()
    conn.close()
    return row

def get_city_by_region(region_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id,name_ru,name_zh,lat,lon FROM cities WHERE region_id=? ORDER BY id ASC", (region_id,))
    row = c.fetchone()
    conn.close()
    return row

def find_region_by_auto_code(code):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT r.id,r.name_ru,r.name_zh FROM auto_codes a JOIN regions r ON a.region_id=r.id WHERE a.code=?", (code,))
    row = c.fetchone()
    conn.close()
    return row

def list_auto_codes_by_region(region_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT code FROM auto_codes WHERE region_id=? ORDER BY code", (region_id,))
    rows = [r[0] for r in c.fetchall()]
    conn.close()
    return rows

def find_city_by_phone_code(area_code):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT c.id,c.name_ru,c.name_zh,r.id,r.name_ru,r.name_zh,c.lat,c.lon FROM phone_codes p JOIN cities c ON p.city_id=c.id JOIN regions r ON p.region_id=r.id WHERE p.area_code=?", (area_code,))
    row = c.fetchone()
    conn.close()
    return row

def list_phone_codes_by_city(city_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT area_code FROM phone_codes WHERE city_id=? ORDER BY area_code", (city_id,))
    rows = [r[0] for r in c.fetchall()]
    conn.close()
    return rows

def save_query(user_id, language, intent, raw_text, parsed_entities, result, created_at):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO queries(user_id,language,intent,raw_text,parsed_entities,result,created_at) VALUES(?,?,?,?,?,?,?)", (user_id, language, intent, raw_text, parsed_entities, result, created_at))
    conn.commit()
    conn.close()
