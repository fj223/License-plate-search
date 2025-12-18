import urllib.parse
import urllib.request
import json

def geocode_city(name):
    q = name.strip()
    url = "https://nominatim.openstreetmap.org/search?format=json&addressdetails=1&accept-language=ru&limit=1&q=" + urllib.parse.quote(q)
    req = urllib.request.Request(url, headers={"User-Agent": "rf-region-bot/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = resp.read()
    arr = json.loads(data.decode("utf-8"))
    if not arr:
        return None
    it = arr[0]
    lat = float(it.get("lat"))
    lon = float(it.get("lon"))
    addr = it.get("address", {})
    city_ru = addr.get("city") or addr.get("town") or addr.get("village") or q
    region_ru = addr.get("state") or addr.get("region") or addr.get("county")
    return {"city": city_ru, "region": region_ru, "lat": lat, "lon": lon}

def geocode_region_polygon(name):
    q = name.strip()
    url = "https://nominatim.openstreetmap.org/search?format=jsonv2&polygon_geojson=1&limit=1&accept-language=ru&q=" + urllib.parse.quote(q)
    req = urllib.request.Request(url, headers={"User-Agent": "rf-region-bot/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = resp.read()
    arr = json.loads(data.decode("utf-8"))
    if not arr:
        return None
    it = arr[0]
    geojson = it.get("geojson")
    bbox = it.get("boundingbox")
    if bbox:
        minlat = float(bbox[0]); maxlat = float(bbox[1]); minlon = float(bbox[2]); maxlon = float(bbox[3])
    else:
        minlat = min([pt[1] for pt in geojson.get("coordinates", [[]])[0]]) if geojson else 0
        maxlat = max([pt[1] for pt in geojson.get("coordinates", [[]])[0]]) if geojson else 0
        minlon = min([pt[0] for pt in geojson.get("coordinates", [[]])[0]]) if geojson else 0
        maxlon = max([pt[0] for pt in geojson.get("coordinates", [[]])[0]]) if geojson else 0
    return {"geojson": geojson, "bbox": (minlon, minlat, maxlon, maxlat)}

def geocode_city_label(name, lang="en"):
    q = name.strip()
    url = "https://nominatim.openstreetmap.org/search?format=json&addressdetails=1&accept-language=" + lang + "&limit=1&q=" + urllib.parse.quote(q)
    req = urllib.request.Request(url, headers={"User-Agent": "rf-region-bot/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = resp.read()
    arr = json.loads(data.decode("utf-8"))
    if not arr:
        return None
    it = arr[0]
    addr = it.get("address", {})
    return addr.get("city") or addr.get("town") or addr.get("village") or q