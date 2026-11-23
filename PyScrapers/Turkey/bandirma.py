# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from httpx     import AsyncClient, Timeout
from helpers   import str2latlng, kaydet

class Bandirma:
    def __init__(self):
        self.oturum = AsyncClient(timeout=Timeout(10, connect=10, read=5*60, write=10))

    async def kameralar(self) -> dict[str, str]:
        istek = await self.oturum.get("https://wowza.yayin.com.tr/playlist/bandirmabeltr/playlist_bandirmabeltr.json")
        return istek.json()

    async def getir(self) -> dict[list[dict]]:
        kameralar = await self.kameralar()

        veri = {"Bandirma": []}
        for kamera_veri in kameralar.get("playlist", []):
            latitude, longitude = await str2latlng(f"{kamera_veri['title']}, Bandırma, Balıkesir, Türkiye")

            veri["Bandirma"].append({
                "description" : kamera_veri["title"],
                "latitude"    : latitude,
                "longitude"   : longitude,
                "url"         : "https:" + kamera_veri["sources"][0]["file"],
                "encoding"    : "H.264",
                "format"      : "M3U8"
            })

        return veri

async def basla():
    belediye      = Bandirma()
    gelen_veriler = await belediye.getir()

    kaydet("Balıkesir", gelen_veriler)
