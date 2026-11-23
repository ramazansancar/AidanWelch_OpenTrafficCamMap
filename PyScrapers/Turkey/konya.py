# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from httpx     import AsyncClient, Timeout
from parsel    import Selector
from re        import search
from helpers   import str2latlng, kaydet

class Konya:
    def __init__(self):
        self.base_url = "https://www.konyabuyuksehir.tv"
        self.belediye_url = "https://www.konyabuyuksehir.tv/canliyayin_kameralar_tum/"
        self.oturum       = AsyncClient(timeout=Timeout(10, connect=10, read=5*60, write=10))

    async def kameralar(self) -> dict[str, str]:
        istek  = await self.oturum.get(self.belediye_url)
        secici = Selector(istek.text)

        return {
            kamera.css("div.video-content h5::text").get() : self.base_url + kamera.css("a::attr(href)").get()
                for kamera in secici.css("div.video-item-card")
        }

    async def kamera_detay(self, kamera_url:str) -> dict | None:
        istek  = await self.oturum.get(kamera_url)
        secici = Selector(istek.text)

        return {
            "ilce"        : secici.css("span.pl-10::text").get(),
            "hls"         : await self.iframe2hls(secici.css("iframe::attr(src)").get())
        }

    async def iframe2hls(self, iframe_url:str) -> str:
        istek  = await self.oturum.get(iframe_url)
        hls_id = search(r"id: '(.*)'", istek.text).group(1)

        return f"https://content.tvkur.com/l/{hls_id}/master.m3u8"

    async def getir(self) -> dict[list[dict]]:
        kameralar = await self.kameralar()

        veri = {"Belediye": []}
        for kamera_adi, kamera_url in kameralar.items():
            kamera_detay = await self.kamera_detay(kamera_url)
            if not kamera_detay:
                continue
            
            latlngstring = search(r"(.+?)\s*\d*$", kamera_adi).group(1)
            latitude, longitude = await str2latlng(f"{latlngstring}, Konya, Türkiye")

            veri["Belediye"].append({
                "description" : kamera_adi,
                "latitude"    : latitude,
                "longitude"   : longitude,
                "url"         : kamera_detay["hls"],
                "encoding"    : "H.264",
                "format"      : "M3U8"
            })

        return veri

async def basla():
    belediye      = Konya()
    gelen_veriler = await belediye.getir()

    kaydet("Konya", gelen_veriler)
