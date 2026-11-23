# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from httpx     import AsyncClient, Timeout
from re        import sub
from helpers   import str2latlng, kaydet, canli_mi

class Derebucak:
    def __init__(self):
        self.playlist_url = "https://wowza.yayin.com.tr/playlist/derebucakbeltr/playlist_derebucakbeltr.json"
        self.oturum       = AsyncClient(timeout=Timeout(10, connect=10, read=5*60, write=10))

    async def kameralar(self) -> list[dict]:
        istek = await self.oturum.get(self.playlist_url)
        return istek.json().get("playlist", [])

    async def getir(self) -> dict[list[dict]]:
        kameralar = await self.kameralar()

        veri = {"Derebucak": []}
        for kamera in kameralar:
            if not kamera.get("sources"):
                continue

            hls = "https:" + kamera["sources"][0]["file"]
            # Oynatma listesinde kapatılmış kameralar da duruyor
            if not await canli_mi(self.oturum, hls):
                continue

            baslik = kamera["title"].strip()
            yer    = sub(r"[\s\-]*\d*$", "", baslik)
            latitude, longitude = await str2latlng(f"{yer}, Derebucak, Konya, Türkiye", merkez=(37.3934, 31.5098), yaricap=0.3)

            veri["Derebucak"].append({
                "description" : baslik,
                "latitude"    : latitude,
                "longitude"   : longitude,
                "url"         : hls,
                "encoding"    : "H.264",
                "format"      : "M3U8"
            })

        return veri

async def basla():
    belediye      = Derebucak()
    gelen_veriler = await belediye.getir()

    kaydet("Konya", gelen_veriler)
