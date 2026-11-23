# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from httpx     import AsyncClient, Timeout, get
from parsel    import Selector
from re        import sub
from ssl       import create_default_context
from certifi   import where
from helpers   import str2latlng, kaydet

# Sunucu ara sertifikayı göndermiyor (eksik zincir). Ara sertifika, sertifikadaki
# AIA adresinden alınıp güven deposuna eklenir; doğrulama açık kalır, zincir yine
# certifi'deki köke bağlanmak zorunda.
ARA_SERTIFIKA = "http://crt.sectigo.com/SectigoPublicServerAuthenticationCADVR36.crt"

def ssl_baglami():
    baglam = create_default_context(cafile=where())
    try:
        baglam.load_verify_locations(cadata=get(ARA_SERTIFIKA, timeout=15).content)
    except Exception as hata:
        print(f"[Nevşehir] Ara sertifika alınamadı: {hata}")
    return baglam

class Nevsehir:
    def __init__(self):
        self.belediye_url = "https://belsis.nevsehir.bel.tr/kameracanli/canli"
        self.hls_base     = "https://belsis.nevsehir.bel.tr/hls/live"
        self.oturum       = AsyncClient(
            timeout          = Timeout(10, connect=10, read=5*60, write=10),
            follow_redirects = True,
            verify           = ssl_baglami(),
            headers          = {"User-Agent": "Mozilla/5.0"}
        )

    async def kameralar(self) -> dict[str, str]:
        istek  = await self.oturum.get(self.belediye_url)
        secici = Selector(istek.text)

        return {
            kamera.attrib["data-name"].strip() : f"{self.hls_base}/{kamera.attrib['data-key']}/index.m3u8"
                for kamera in secici.css("div.cam[data-key][data-name]")
        }

    async def getir(self) -> dict[list[dict]]:
        kameralar = await self.kameralar()

        veri = {"Belediye": []}
        for kamera_adi, hls in kameralar.items():
            # "Meydan - PTZ" -> "Meydan"
            yer = sub(r"\s*-\s*(PTZ|Sabit)$", "", kamera_adi)
            latitude, longitude = await str2latlng(f"{yer}, Nevşehir, Türkiye", merkez=(38.6244, 34.7144), yaricap=0.5)

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
    belediye      = Nevsehir()
    gelen_veriler = await belediye.getir()

    kaydet("Nevşehir", gelen_veriler)
