# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

# Kaynak: Çevre, Şehircilik ve İklim Değişikliği Bakanlığı — https://saldagolu.gov.tr/saldagolu/canli.html
# Oynatıcı iframe'i (saldagolu_cam.html) HLS adreslerini içeriyor.

from httpx     import AsyncClient, Timeout
from re        import findall, search
from helpers   import kaydet, canli_mi

class Salda:
    def __init__(self):
        self.oynatici_url = "https://saldagolu.gov.tr/saldagolu/saldagolu_cam.html"
        self.oturum       = AsyncClient(
            timeout          = Timeout(10, connect=10, read=60, write=10),
            follow_redirects = True,
            headers          = {"User-Agent": "Mozilla/5.0"}
        )

    async def kameralar(self) -> list[str]:
        istek = await self.oturum.get(self.oynatici_url)
        return list(dict.fromkeys(findall(r"https://[^\"'\s]+\.m3u8", istek.text)))

    async def getir(self) -> dict[list[dict]]:
        veri = {"Yeşilova": []}
        for hls in await self.kameralar():
            if not await canli_mi(self.oturum, hls):
                continue

            # .../salda_golu.stream/... -> "Salda Gölü", .../salda_golu_2.stream/... -> "Salda Gölü 2"
            numara = search(r"salda_golu_?(\d*)\.stream", hls)
            baslik = f"Salda Gölü {numara.group(1)}".strip() if numara else "Salda Gölü"

            veri["Yeşilova"].append({
                "description" : baslik,
                "latitude"    : 37.5470,  # Beyaz Adalar, kamera burada
                "longitude"   : 29.6790,
                "url"         : hls,
                "encoding"    : "H.264",
                "format"      : "M3U8"
            })

        return veri

async def basla():
    kaynak        = Salda()
    gelen_veriler = await kaynak.getir()

    kaydet("Burdur", gelen_veriler)
