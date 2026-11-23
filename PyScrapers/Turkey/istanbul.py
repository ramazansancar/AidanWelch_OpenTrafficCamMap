# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

# İBB trafik kameraları — ikinci yayın adresi.
# İstanbul/UYM (compilation/Turkey/istanbul.mjs) hls.ibb.gov.tr adreslerini kullanıyor.
# "tkm1" sunucusunun yayınları ayrıca İBB'nin Wowza StreamLock adresinden de veriliyor
# (601a55c88ec6d.streamlock.net, aynı kamera numaraları; İBB IP bloğu 185.68.222.0/23).
# hls.ibb.gov.tr cevap vermediğinde bu adresler çalışıyor (2026-11-24). Liste ve konumlar İBB API'sinden.

from asyncio   import Semaphore, gather
from httpx     import AsyncClient, Timeout
from re        import search
from helpers   import kaydet, canli_mi

API_URL      = "https://tkmservices.ibb.gov.tr/web/api/IntensityMap/v1/Camera"
STREAMLOCK   = "https://601a55c88ec6d.streamlock.net/hls/{no}.stream/playlist.m3u8"

class IstanbulYedek:
    def __init__(self):
        self.oturum = AsyncClient(
            timeout = Timeout(10, connect=10, read=60, write=10),
            headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json, text/plain, */*"}
        )

    async def kameralar(self) -> list[dict]:
        veri = (await self.oturum.get(API_URL)).json()

        # Grup kameraları da kendi adresleriyle listede
        tumu = []
        for kamera in veri:
            tumu.append(kamera)
            tumu.extend(kamera.get("Group") or [])

        kameralar = {}
        for kamera in tumu:
            tkm1 = search(r"/tkm1/hls/(\d+)\.stream", kamera.get("VideoURL_SSL") or "")
            if not tkm1 or not kamera.get("XCoord") or not kamera.get("YCoord"):
                continue
            kameralar[tkm1.group(1)] = kamera

        return [{"no": no, **kamera} for no, kamera in kameralar.items()]

    async def getir(self) -> dict[list[dict]]:
        kameralar = await self.kameralar()
        sinir     = Semaphore(8)

        async def kontrol(kamera: dict) -> dict | None:
            hls = STREAMLOCK.format(no=kamera["no"])
            async with sinir:
                if not await canli_mi(self.oturum, hls):
                    return None
            return {
                "description" : " ".join(kamera["Name"].split()),
                "latitude"    : float(kamera["YCoord"]),
                "longitude"   : float(kamera["XCoord"]),
                "url"         : hls,
                "encoding"    : "H.264",
                "format"      : "M3U8"
            }

        sonuclar = await gather(*(kontrol(k) for k in kameralar))
        return {"UYM Yedek": sorted((s for s in sonuclar if s), key=lambda k: k["description"])}

async def basla():
    kaynak        = IstanbulYedek()
    gelen_veriler = await kaynak.getir()

    kaydet("İstanbul", gelen_veriler)
