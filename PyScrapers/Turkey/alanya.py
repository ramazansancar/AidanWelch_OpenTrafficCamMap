# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from httpx     import AsyncClient, Timeout
from re        import search
from helpers   import str2latlng, kaydet

class Alanya:
    def __init__(self):
        self.oturum = AsyncClient(timeout=Timeout(10, connect=10, read=5*60, write=10))

    async def kameralar(self) -> dict[str, str]:
        istek = await self.oturum.get("https://wowza.yayin.com.tr/playlist/alanyabeltr/playlist_alanyabeltr.json")
        return istek.json()

    async def getir(self) -> dict[list[dict]]:
        kameralar = await self.kameralar()

        veri = {"Alanya": []}
        for kamera_veri in kameralar.get("playlist", []):
            
            latlngstring = search(r"(.+?)\s*\d*$", kamera_veri['title']).group(1)
            latitude, longitude = await str2latlng(f"{latlngstring}, Alanya, Antalya, Türkiye")

            veri["Alanya"].append({
                "description" : kamera_veri["title"],
                "latitude"    : latitude,
                "longitude"   : longitude,
                "url"         : "https:" + kamera_veri["sources"][0]["file"],
                "encoding"    : "H.264",
                "format"      : "M3U8"
            })

        return veri

async def basla():
    belediye      = Alanya()
    gelen_veriler = await belediye.getir()

    kaydet("Antalya", gelen_veriler)
