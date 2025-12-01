import io
import math
import urllib.request
import urllib.parse
from PIL import Image, ImageDraw, ImageFont
from .geocode import geocode_region_polygon, geocode_city_label

def _get_font(size):
    for name in [
        "arial.ttf","Arial.ttf","msyh.ttc","Microsoft YaHei.ttf",
        "simhei.ttf","SimHei.ttf","NotoSansCJK-Regular.ttc",
        "NotoSans-Regular.ttf","DejaVuSans.ttf"
    ]:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()

def generate_region_map(region_name, city_name=None, lat=None, lon=None):
    poly = None
    # 优先城市边界，其次区域边界
    try:
        if city_name:
            poly = geocode_region_polygon(city_name)
        if not poly:
            poly = geocode_region_polygon(region_name)
    except Exception:
        poly = None
    if poly and poly.get("geojson"):
        bbox = poly["bbox"]
        minlon, minlat, maxlon, maxlat = bbox
        w, h = 800, 500
        # 优先 ll+spn，可靠性更好
        cx = (minlon + maxlon) / 2.0
        cy = (minlat + maxlat) / 2.0
        dx = (maxlon - minlon) * 1.08
        dy = (maxlat - minlat) * 1.08
        try:
            url = f"https://static-maps.yandex.ru/1.x/?ll={cx},{cy}&spn={dx},{dy}&l=map&size={w},{h}&lang=ru_RU"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                base = Image.open(io.BytesIO(resp.read())).convert("RGBA")
        except Exception:
            try:
                url = f"https://static-maps.yandex.ru/1.x/?bbox={minlon},{minlat}~{maxlon},{maxlat}&l=map&size={w},{h}&lang=ru_RU"
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=8) as resp:
                    base = Image.open(io.BytesIO(resp.read())).convert("RGBA")
            except Exception:
                base = None
        if base is None:
            base = Image.new("RGBA", (w, h), (230, 240, 250, 255))
        overlay = Image.new("RGBA", base.size, (0,0,0,0))
        d = ImageDraw.Draw(overlay)
        pad = 0
        def project(lon, lat):
            x = pad + (lon - minlon) / (maxlon - minlon + 1e-9) * (w - 2*pad)
            y = pad + (maxlat - lat) / (maxlat - minlat + 1e-9) * (h - 2*pad)
            return (x, y)
        gj = poly["geojson"]
        fill = (255, 0, 0, 60)
        outline = (220, 60, 60, 255)
        # 绘制多边形（若为 OSM 静态底图无需特殊投影处理，按 bbox 线性映射）
        if gj.get("type") == "Polygon":
            rings = gj.get("coordinates", [])
            for ring in rings:
                pts = [project(lon, lat) for lon, lat in ring]
                d.polygon(pts, outline=outline, fill=fill)
        elif gj.get("type") == "MultiPolygon":
            for polygon in gj.get("coordinates", []):
                for ring in polygon:
                    pts = [project(lon, lat) for lon, lat in ring]
                    d.polygon(pts, outline=outline, fill=fill)
        if lat is not None and lon is not None:
            px, py = project(lon, lat)
            d.ellipse([px-7, py-7, px+7, py+7], fill=(255,60,60,255))
            label_en = None
            try:
                if city_name:
                    label_en = geocode_city_label(city_name, "en")
            except Exception:
                label_en = None
            label = (label_en + " / " + city_name) if (label_en and city_name) else (city_name or region_name)
            font = _get_font(18)
            bbox = d.textbbox((0,0), label, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            bx, by = px+10, py-10
            d.rectangle([bx, by, bx+tw+12, by+th+8], fill=(255,255,255,230), outline=(180,180,180,255))
            d.text((bx+6, by+4), label, font=font, fill=(10,10,10,255))
        font2 = _get_font(24)
        title = region_name if not city_name else f"{region_name} / {city_name}"
        d.text((10, 10), title, font=font2, fill=(10,10,10,255))
        composed = Image.alpha_composite(base, overlay).convert("RGB")
        buf = io.BytesIO()
        composed.save(buf, format="PNG")
        buf.seek(0)
        return buf.getvalue()
    if lat is not None and lon is not None:
        try:
            url = f"https://static-maps.yandex.ru/1.x/?ll={lon},{lat}&z=6&size=650,450&l=map&pt={lon},{lat},pm2rdm"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = resp.read()
            return data
        except Exception:
            pass
    img = Image.new("RGB", (800, 500), (220, 235, 245))
    d = ImageDraw.Draw(img)
    title = region_name if not city_name else f"{region_name} / {city_name}"
    font = _get_font(28)
    d.rectangle([40, 90, 760, 460], outline=(40, 80, 180), width=6)
    d.text((50, 30), title, font=font, fill=(10, 10, 10))
    d.ellipse([390, 265, 410, 285], fill=(200, 60, 60))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()

def generate_full_russia_map(region_name, city_name=None, lat=None, lon=None):
    if lat is not None and lon is not None:
        try:
            url = f"https://static-maps.yandex.ru/1.x/?ll={lon},{lat}&z=3&size=650,450&l=map&pt={lon},{lat},pm2rdm"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                base = Image.open(io.BytesIO(resp.read())).convert("RGBA")
        except Exception:
            base = None
        if base is not None:
            overlay = Image.new("RGBA", base.size, (0,0,0,0))
            d = ImageDraw.Draw(overlay, "RGBA")
            cx, cy = base.size[0]//2, base.size[1]//2
            d.ellipse([cx-52, cy-52, cx+52, cy+52], fill=(255,0,0,60))
            d.ellipse([cx-22, cy-22, cx+22, cy+22], fill=(255,0,0,180))
            font = _get_font(20)
            title = region_name if not city_name else f"{region_name} / {city_name}"
            d.rectangle([0,0,base.size[0],28], fill=(255,255,255,220))
            d.text((8,6), title, font=font, fill=(0,0,0,255))
            composed = Image.alpha_composite(base, overlay).convert("RGB")
            out = io.BytesIO()
            composed.save(out, format="PNG")
            out.seek(0)
            return out.getvalue()
    return generate_region_map(region_name, city_name, lat, lon)

def generate_russia_location_map(region_name, city_name=None, lat=None, lon=None):
    if lat is not None and lon is not None:
        try:
            url = f"https://static-maps.yandex.ru/1.x/?ll={lon},{lat}&z=3&size=650,450&l=map&pt={lon},{lat},pm2rdm"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                base = Image.open(io.BytesIO(resp.read())).convert("RGBA")
        except Exception:
            base = None
        if base is not None:
            overlay = Image.new("RGBA", base.size, (0,0,0,0))
            d = ImageDraw.Draw(overlay, "RGBA")
            font = _get_font(20)
            title = region_name if not city_name else f"{region_name} / {city_name}"
            d.rectangle([0,0,base.size[0],28], fill=(255,255,255,220))
            d.text((8,6), title, font=font, fill=(0,0,0,255))
            composed = Image.alpha_composite(base, overlay).convert("RGB")
            out = io.BytesIO()
            composed.save(out, format="PNG")
            out.seek(0)
            return out.getvalue()
    return generate_region_map(region_name, city_name, lat, lon)

def generate_city_focus_map(region_name, city_name=None, lat=None, lon=None):
    if lat is not None and lon is not None:
        try:
            url = f"https://static-maps.yandex.ru/1.x/?ll={lon},{lat}&z=10&size=700,450&l=map&pt={lon},{lat},pm2rdm"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                base = Image.open(io.BytesIO(resp.read())).convert("RGBA")
        except Exception:
            base = None
        if base is not None:
            overlay = Image.new("RGBA", base.size, (0,0,0,0))
            d = ImageDraw.Draw(overlay, "RGBA")
            font = _get_font(20)
            title = region_name if not city_name else f"{region_name} / {city_name}"
            d.rectangle([0,0,base.size[0],32], fill=(255,255,255,230))
            d.text((10,7), title, font=font, fill=(0,0,0,255))
            composed = Image.alpha_composite(base, overlay).convert("RGB")
            out = io.BytesIO()
            composed.save(out, format="PNG")
            out.seek(0)
            return out.getvalue()
    return generate_russia_location_map(region_name, city_name, lat, lon)

def generate_city_dual_map(region_name, city_name=None, lat=None, lon=None):
    if lat is None or lon is None:
        return generate_city_focus_map(region_name, city_name, lat, lon)
    base_left = None
    base_right = None
    try:
        u1 = f"https://static-maps.yandex.ru/1.x/?ll={lon},{lat}&z=3&size=650,450&l=map&pt={lon},{lat},pm2rdm"
        r1 = urllib.request.Request(u1, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(r1, timeout=8) as resp:
            base_left = Image.open(io.BytesIO(resp.read())).convert("RGBA")
    except Exception:
        base_left = None
    try:
        u2 = f"https://static-maps.yandex.ru/1.x/?ll={lon},{lat}&z=11&size=650,450&l=map&pt={lon},{lat},pm2rdm"
        r2 = urllib.request.Request(u2, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(r2, timeout=8) as resp:
            base_right = Image.open(io.BytesIO(resp.read())).convert("RGBA")
    except Exception:
        base_right = None
    if base_left is None and base_right is None:
        return generate_city_focus_map(region_name, city_name, lat, lon)
    if base_left is None:
        base_left = base_right
    if base_right is None:
        base_right = base_left
    canvas = Image.new("RGBA", (1200, 450), (255, 255, 255, 255))
    canvas.paste(base_left.resize((600, 450)), (0, 0))
    canvas.paste(base_right.resize((600, 450)), (600, 0))
    overlay = Image.new("RGBA", canvas.size, (0,0,0,0))
    d = ImageDraw.Draw(overlay, "RGBA")
    font = _get_font(22)
    title = region_name if not city_name else f"{region_name} / {city_name}"
    d.rectangle([0,0,1200,36], fill=(255,255,255,230))
    d.text((10,7), title, font=font, fill=(0,0,0,255))
    composed = Image.alpha_composite(canvas, overlay).convert("RGB")
    out = io.BytesIO()
    composed.save(out, format="PNG")
    out.seek(0)
    return out.getvalue()

def generate_federation_detail_map(region_name, city_name=None, lat=None, lon=None):
    base = None
    inset = None
    cx = lon
    cy = lat
    if cx is None or cy is None:
        cx = 37.6173
        cy = 55.7558
    try:
        url = f"https://static-maps.yandex.ru/1.x/?ll={cx},{cy}&z=3&size=700,450&l=map&pt={cx},{cy},pm2rdm"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            base = Image.open(io.BytesIO(resp.read())).convert("RGBA")
    except Exception:
        try:
            osm = f"https://staticmap.openstreetmap.de/staticmap.php?center={cy},{cx}&zoom=3&size=700x450&maptype=mapnik&markers={cy},{cx},lightred1"
            req = urllib.request.Request(osm, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                base = Image.open(io.BytesIO(resp.read())).convert("RGBA")
        except Exception:
            try:
                img = _tile_fallback(cy, cx, 3, (700, 450))
                base = img.convert("RGBA")
            except Exception:
                base = Image.new("RGBA", (700, 450), (230, 240, 250, 255))
    z = 6 if city_name or (lat is not None and lon is not None) else 4
    try:
        url2 = f"https://static-maps.yandex.ru/1.x/?ll={cx},{cy}&z={z}&size=700,450&l=map&pt={cx},{cy},pm2rdm"
        req2 = urllib.request.Request(url2, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req2, timeout=10) as resp:
            inset = Image.open(io.BytesIO(resp.read())).convert("RGBA")
    except Exception:
        try:
            osm2 = f"https://staticmap.openstreetmap.de/staticmap.php?center={cy},{cx}&zoom={z}&size=700x450&maptype=mapnik&markers={cy},{cx},lightred1"
            req2 = urllib.request.Request(osm2, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req2, timeout=10) as resp:
                inset = Image.open(io.BytesIO(resp.read())).convert("RGBA")
        except Exception:
            try:
                img = _tile_fallback(cy, cx, z, (700, 450))
                inset = img.convert("RGBA")
            except Exception:
                inset = Image.new("RGBA", (700, 450), (220, 235, 245, 255))
    canvas = Image.new("RGBA", (1200, 450), (255, 255, 255, 255))
    base_resized = base.resize((600, 450))
    inset_resized = inset.resize((600, 450))
    canvas.paste(base_resized, (0, 0))
    canvas.paste(inset_resized, (600, 0))
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay, "RGBA")
    font = _get_font(22)
    title = region_name if not city_name else f"{region_name} / {city_name}"
    d.rectangle([0, 0, 1200, 36], fill=(255, 255, 255, 230))
    d.text((10, 6), title, font=font, fill=(0, 0, 0, 255))
    composed = Image.alpha_composite(canvas, overlay).convert("RGB")
    out = io.BytesIO()
    composed.save(out, format="PNG")
    out.seek(0)
    return out.getvalue()

def _tile_fallback(lat, lon, z, size):
    ts = 256
    n = 2 ** z
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.log(math.tan(math.radians(lat)) + 1.0 / math.cos(math.radians(lat))) / math.pi) / 2.0 * n)
    urls = []
    for dy in [-1, 0, 1]:
        for dx in [-1, 0, 1]:
            tx = max(0, min(n - 1, x + dx))
            ty = max(0, min(n - 1, y + dy))
            urls.append((dx + 1, dy + 1, f"https://tile.openstreetmap.org/{z}/{tx}/{ty}.png"))
    canvas = Image.new("RGBA", (ts * 3, ts * 3), (235, 240, 250, 255))
    for ox, oy, u in urls:
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                img = Image.open(io.BytesIO(resp.read())).convert("RGBA")
            canvas.paste(img, (ox * ts, oy * ts))
        except Exception:
            pass
    cxp = ts * 1.5
    cyp = ts * 1.5
    out = canvas.resize(size)
    d = ImageDraw.Draw(out, "RGBA")
    d.ellipse([out.size[0] // 2 - 52, out.size[1] // 2 - 52, out.size[0] // 2 + 52, out.size[1] // 2 + 52], fill=(255, 0, 0, 60))
    d.ellipse([out.size[0] // 2 - 22, out.size[1] // 2 - 22, out.size[0] // 2 + 22, out.size[1] // 2 + 22], fill=(255, 0, 0, 180))
    return out
