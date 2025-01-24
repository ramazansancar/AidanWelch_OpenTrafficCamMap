# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from httpx import AsyncClient
from Kekik import unicode_tr
import re

async def str2latlng(str:str) -> tuple[float, float]:
    oturum  = AsyncClient(headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"}, timeout=15)
    yer_adi = re.sub(r"\s*\d+$", "", unicode_tr(str).title())
    istek   = await oturum.get(f"https://publicapi.ramazansancar.com.tr/google/maps/names/{yer_adi}")

    try:
        lat = istek.json()["data"][0]["geometry"]["location"]["lat"]
        lng = istek.json()["data"][0]["geometry"]["location"]["lng"]
        print(yer_adi, lat, lng)

        return float(lat) , float(lng)
    except Exception:
        print(0.0, 0.0, yer_adi)
        return 0.0, 0.0
