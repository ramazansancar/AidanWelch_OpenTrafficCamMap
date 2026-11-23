# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

# Kaynak: Uçhisar Belediyesi — sitede her kamera ayrı sayfada, HLS adresi sayfanın içinde.

from httpx     import AsyncClient, Timeout
from re        import search
from helpers   import str2latlng, kaydet, canli_mi

SAYFALAR = {
    # açıklama          : (sayfa, geocode için yer adı)
    "Uçhisar Merkez"    : ("https://www.uchisar.bel.tr/uchisar-canli-kamera-merkez/", "Uçhisar Kalesi"),
    "Uçhisar Vadi"      : ("https://www.uchisar.bel.tr/uchisar-canli-kamera-vadi/",   "Güvercinlik Vadisi"),
}

class Uchisar:
    def __init__(self):
        self.oturum = AsyncClient(
            timeout          = Timeout(10, connect=10, read=60, write=10),
            follow_redirects = True,
            headers          = {"User-Agent": "Mozilla/5.0"}
        )

    async def getir(self) -> dict[list[dict]]:
        veri = {"Uçhisar": []}
        for aciklama, (sayfa, yer) in SAYFALAR.items():
            istek = await self.oturum.get(sayfa)
            hls   = search(r"https://[^\"'\s]+\.m3u8", istek.text)
            if not hls or not await canli_mi(self.oturum, hls.group(0)):
                continue

            latitude, longitude = await str2latlng(f"{yer}, Uçhisar, Nevşehir, Türkiye", merkez=(38.6297, 34.8053), yaricap=0.1)

            veri["Uçhisar"].append({
                "description" : aciklama,
                "latitude"    : latitude,
                "longitude"   : longitude,
                "url"         : hls.group(0),
                "encoding"    : "H.264",
                "format"      : "M3U8"
            })

        return veri

async def basla():
    belediye      = Uchisar()
    gelen_veriler = await belediye.getir()

    kaydet("Nevşehir", gelen_veriler)
