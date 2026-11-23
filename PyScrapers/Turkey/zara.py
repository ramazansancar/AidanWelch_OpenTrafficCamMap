# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

# Kaynak: Zara Belediyesi — https://www.zara.bel.tr/zarayi-canli-izle
# Sekmelerdeki iframe'ler (server.arvas.com.tr/<ad>.html) HLS adresini içeriyor.
# HTML yorumu içindeki eski iframe'ler (rtsp.me) seçiciye takılmaz.

from httpx     import AsyncClient, Timeout
from parsel    import Selector
from re        import search
from helpers   import str2latlng, kaydet, canli_mi, ssl_baglami

class Zara:
    def __init__(self):
        self.belediye_url = "https://www.zara.bel.tr/zarayi-canli-izle"
        self.oturum       = AsyncClient(
            timeout          = Timeout(10, connect=10, read=60, write=10),
            follow_redirects = True,
            headers          = {"User-Agent": "Mozilla/5.0"},
            verify           = ssl_baglami(),  # server.arvas.com.tr ara sertifikayı göndermiyor
        )

    async def kameralar(self) -> dict[str, str]:
        istek  = await self.oturum.get(self.belediye_url)
        secici = Selector(istek.text)

        # Sekme adları: <a href="#dortyolkamera">Dortyol</a>
        sekmeler = {
            a.attrib["href"].lstrip("#") : a.css("::text").get("").strip()
                for a in secici.css("ul.tab-nav a[href^='#']")
        }

        kameralar = {}
        for icerik in secici.css("div.tab-content[id]"):
            iframe = icerik.css("iframe::attr(src)").get()
            if not iframe:
                continue

            oynatici = await self.oturum.get(iframe)
            hls      = search(r"https://[^\"'\s]+\.m3u8", oynatici.text)
            if not hls:
                continue

            ad = sekmeler.get(icerik.attrib["id"]) or icerik.attrib["id"]
            kameralar[f"Zara {ad.replace('Dortyol', 'Dörtyol')}"] = hls.group(0)

        return kameralar

    async def getir(self) -> dict[list[dict]]:
        veri = {"Zara": []}
        for kamera_adi, hls in (await self.kameralar()).items():
            if not await canli_mi(self.oturum, hls):
                continue

            latitude, longitude = await str2latlng(f"{kamera_adi}, Sivas, Türkiye", merkez=(39.8958, 37.7533), yaricap=0.1)

            veri["Zara"].append({
                "description" : kamera_adi,
                "latitude"    : latitude,
                "longitude"   : longitude,
                "url"         : hls,
                "encoding"    : "H.264",
                "format"      : "M3U8"
            })

        return veri

async def basla():
    belediye      = Zara()
    gelen_veriler = await belediye.getir()

    kaydet("Sivas", gelen_veriler)
