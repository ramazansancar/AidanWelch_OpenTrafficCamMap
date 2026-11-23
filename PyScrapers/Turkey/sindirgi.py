# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from Kekik.cli import konsol
from httpx     import AsyncClient, Timeout
from helpers   import str2latlng, kaydet

class Sindirgi:
    def __init__(self):
        self.oturum = AsyncClient(timeout=Timeout(10, connect=10, read=5*60, write=10))

    async def kameralar(self) -> dict[str, str]:
        try:
            istek = await self.oturum.get("https://wowza.yayin.com.tr/playlist/sindirgibel/playlist_sindirgibel.json")
            return istek.json()
        except Exception as e:
            konsol.log(f"[red][Sındırgı] Kameralar alınamadı: {str(e)}")
            return {}

    async def getir(self) -> dict[list[dict]]:
        kameralar = await self.kameralar()
        
        if not kameralar:
            konsol.log("[red][Sındırgı] Kamera listesi alınamadı")
            return {"Sındırgı": []}

        veri = {"Sındırgı": []}
        for kamera_veri in kameralar.get("playlist", []):
            try:
                latitude, longitude = await str2latlng(f"{kamera_veri['title']}, Sındırgı, Balıkesir, Türkiye")

                veri["Sındırgı"].append({
                    "description" : kamera_veri["title"],
                    "latitude"    : latitude,
                    "longitude"   : longitude,
                    "url"         : "https:" + kamera_veri["sources"][0]["file"],
                    "encoding"    : "H.264",
                    "format"      : "M3U8"
                })
            except Exception as e:
                konsol.log(f"[red][Sındırgı] {kamera_veri.get('title', 'Bilinmeyen')} kamerası işlenirken hata: {str(e)}")
                continue

        return veri

async def basla():
    belediye      = Sindirgi()
    gelen_veriler = await belediye.getir()

    kaydet("Balıkesir", gelen_veriler)
