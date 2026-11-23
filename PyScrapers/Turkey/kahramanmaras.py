# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from httpx     import AsyncClient, Timeout
from parsel    import Selector
from re        import search
from helpers   import str2latlng, kaydet

class Kahramanmaras:
    def __init__(self):
        self.belediye_url = "https://kamera.kahramanmaras.bel.tr/"
        self.oturum       = AsyncClient(timeout=Timeout(10, connect=10, read=5*60, write=10))

    async def kameralar(self) -> list[dict[str, str]]:
        istek  = await self.oturum.get(self.belediye_url)
        secici = Selector(istek.text)

        kameralar = []
        gorulen   = {}
        for kamera in secici.css("div.camera-card div[data-stream]"):
            baslik = (kamera.attrib.get("data-title") or "").strip()
            hls    = (kamera.attrib.get("data-stream") or "").strip()
            if not baslik or not hls:
                continue

            # Aynı başlıklı kameralar (ör. iki "Teras") ayırt edilsin
            gorulen[baslik] = gorulen.get(baslik, 0) + 1
            if gorulen[baslik] > 1:
                baslik = f"{baslik} {gorulen[baslik]}"

            kameralar.append({"baslik": baslik, "hls": hls})

        return kameralar

    async def getir(self) -> dict[list[dict]]:
        kameralar = await self.kameralar()

        veri = {"Belediye": []}
        for kamera in kameralar:
            latlngstring = search(r"(.+?)\s*\d*$", kamera["baslik"]).group(1)
            latitude, longitude = await str2latlng(f"{latlngstring}, Kahramanmaraş, Türkiye", merkez=(37.5753, 36.9228), yaricap=1.0)

            veri["Belediye"].append({
                "description" : kamera["baslik"],
                "latitude"    : latitude,
                "longitude"   : longitude,
                "url"         : kamera["hls"],
                "encoding"    : "H.264",
                "format"      : "M3U8"
            })

        return veri

async def basla():
    belediye      = Kahramanmaras()
    gelen_veriler = await belediye.getir()

    kaydet("Kahramanmaras", gelen_veriler)
