def format_auto_result(lang, city_ru, city_zh, region_ru, region_zh, codes):
    if lang == "zh":
        return f"城市：{city_zh or city_ru}\n区域：{region_zh or region_ru}\n车牌代码：{', '.join(codes)}"
    return f"Город: {city_ru or city_zh}\nРегион: {region_ru or region_zh}\nКоды региона: {', '.join(codes)}"

def format_auto_region_only(lang, region_ru, region_zh, codes):
    if lang == "zh":
        return f"区域：{region_zh or region_ru}\n车牌代码：{', '.join(codes)}"
    return f"Регион: {region_ru or region_zh}\nКоды региона: {', '.join(codes)}"

def format_phone_result(lang, city_ru, city_zh, region_ru, region_zh, codes):
    if lang == "zh":
        return f"城市：{city_zh or city_ru}\n区域：{region_zh or region_ru}\n电话区号：{', '.join(codes)}"
    return f"Город: {city_ru or city_zh}\nРегион: {region_ru or region_zh}\nКоды: {', '.join(codes)}"

def format_not_found(lang):
    if lang == "zh":
        return "未找到匹配结果"
    return "Ничего не найдено"