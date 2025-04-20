# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from json import dumps, loads
from httpx import AsyncClient
from Kekik import unicode_tr
import re

cache = {}

# Get Cache File
try:
    with open("cache.json", "r", encoding="utf-8") as dosya:
        cache = dosya.read()
        cache = loads(cache)
except FileNotFoundError:
    with open("cache.json", "w", encoding="utf-8") as dosya:
        dosya.write("{}")
except Exception as hata:
    print(f"Cache Dosyası Okunurken Hata Oluştu: {hata}")

async def str2latlng(str:str) -> tuple[float, float]:
    oturum  = AsyncClient(headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"}, timeout=15)
    yer_adi = re.sub(r"\s*\d+$", "", unicode_tr(str).title())

    if yer_adi in cache:
        return cache[yer_adi]
    istek   = await oturum.get(f"https://publicapi.ramazansancar.com.tr/google/maps/names/{yer_adi}")
    try:
        lat = istek.json()["data"][0]["geometry"]["location"]["lat"]
        lng = istek.json()["data"][0]["geometry"]["location"]["lng"]
        print(yer_adi, lat, lng)
        if yer_adi not in cache:
            cache[yer_adi] = lat, lng

        # Cache File Save
        with open("cache.json", "w", encoding="utf-8") as dosya:
            dosya.write(dumps(cache, sort_keys=True, ensure_ascii=False, indent=2))

        return float(lat) , float(lng)
    except Exception:
        print('- ',0.0, 0.0, yer_adi)
        return 36.14207255403557, 31.208844678148807
