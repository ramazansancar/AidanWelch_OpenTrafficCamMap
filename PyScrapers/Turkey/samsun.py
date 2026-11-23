# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from httpx     import AsyncClient, Timeout
from re        import findall
from helpers   import str2latlng, kaydet

class Samsun:
    def __init__(self):
        self.belediye_url = "https://samsun.bel.tr/canli-yayinlar"
        self.oturum       = AsyncClient(
            timeout          = Timeout(10, connect=10, read=5*60, write=10),
            follow_redirects = True,
            headers          = {"User-Agent": "Mozilla/5.0"}
        )

    async def kameralar(self) -> dict[str, str]:
        istek = await self.oturum.get(self.belediye_url)
        # Next.js sayfası: kamera listesi gömülü JSON içinde (kaçışlı tırnaklarla)
        metin = istek.text.replace('\\"', '"')

        kameralar = {}
        for ad, url in findall(r'"name":"([^"]+)","url":"(https://canli\.samsun\.bel\.tr/[^"]+\.m3u8)"', metin):
            if url not in kameralar.values():
                kameralar[ad.strip()] = url

        return kameralar

    async def getir(self) -> dict[list[dict]]:
        kameralar = await self.kameralar()

        veri = {"Belediye": []}
        for kamera_adi, hls in kameralar.items():
            latitude, longitude = await str2latlng(f"{kamera_adi}, Samsun, Türkiye", merkez=(41.2867, 36.3300), yaricap=0.5)

            veri["Belediye"].append({
                "description" : kamera_adi,
                "latitude"    : latitude,
                "longitude"   : longitude,
                "url"         : hls,
                "encoding"    : "H.264",
                "format"      : "M3U8"
            })

        return veri

async def basla():
    belediye      = Samsun()
    gelen_veriler = await belediye.getir()

    kaydet("Samsun", gelen_veriler)
