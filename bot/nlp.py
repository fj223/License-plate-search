import re

def detect_language(text):
    if re.search(r"[\u4e00-\u9fff]", text):
        return "zh"
    if re.search(r"[А-Яа-яЁё]", text):
        return "ru"
    return "ru"

def parse_intent(text):
    t = text.strip().lower()
    # 检测完整车牌号码格式 (俄罗斯车牌格式: А123ВЕ199)
    license_plate_pattern = r"[АВЕКМНОРСТУХABEKMHOPCTYX]\d{3}[АВЕКМНОРСТУХABEKMHOPCTYX]{2}\d{2,3}"
    license_plate_match = re.search(license_plate_pattern, text.upper())
    if license_plate_match:
        plate = license_plate_match.group()
        # 提取车牌中的区域代码（最后2-3位数字）
        region_code = re.search(r"\d{2,3}$", plate).group()
        return {"intent": "license_plate", "plate": plate, "region_code": region_code}
    
    if any(k in t for k in ["电话", "区号", "area code", "телефон", "код города", "телефонный код"]):
        digits = re.findall(r"\d{3,4}", t)
        if digits:
            return {"intent": "phone_code_to_city", "code": digits[0]}
        name = re.sub(r"(телефон(ный)?\s*код|код\s*города)", "", t)
        name = re.sub(r"[^\w\sА-Яа-яЁё\u4e00-\u9fff-]", "", name)
        return {"intent": "city_to_phone_code", "city": name}
    if any(k in t for k in ["车牌", "车牌代码", "region code", "автокод", "номер региона", "код региона"]):
        digits = re.findall(r"\d{2,3}", t)
        if digits:
            return {"intent": "auto_code_to_region", "code": digits[0]}
        name = re.sub(r"(номер\s*региона|код\s*региона)", "", t)
        name = re.sub(r"[^\w\sА-Яа-яЁё\u4e00-\u9fff-]", "", name)
        return {"intent": "city_to_auto_code", "city": name}
    digits = re.findall(r"\d{2,4}", t)
    if digits:
        d = digits[0]
        if any(k in t for k in ["город", "телефон", "код города", "телефонный код"]):
            return {"intent": "phone_code_to_city", "code": d}
        if any(k in t for k in ["регион", "номер региона", "код региона"]):
            return {"intent": "auto_code_to_region", "code": d}
        if len(d) == 4:
            return {"intent": "phone_code_to_city", "code": d}
        if len(d) == 2:
            return {"intent": "auto_code_to_region", "code": d}
        return {"intent": "phone_code_to_city", "code": d}
    name = re.sub(r"(какой\s*регион|какой\s*город)", "", t)
    name = re.sub(r"[^\w\sА-Яа-яЁё\u4e00-\u9fff-]", "", name)
    return {"intent": "city_to_auto_code", "city": name}