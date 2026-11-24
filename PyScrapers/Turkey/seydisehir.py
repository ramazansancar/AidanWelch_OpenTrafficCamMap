# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

# Seydişehir Belediyesi kent kameraları — https://www.seydisehir.bel.tr/canliyayinlar
# Sayfa React; kamera listesi sitenin JS paketinde sabit (SEHIR_KAMERALARI, MAHALLE_KAMERALARI).
# Şehir merkezi: MOBOTIX kameralar, http MJPEG (faststream.jpg) → IMAGE_STREAM / MJPEG.
#   Harita http üzerinden yayınlandığı için <img> ile oynuyor; https'te tarayıcı engelleyebilir.
# Mahalleler: player.im gömme oynatıcısı → EMBED. Oynatıcı "Güncelleyin" uyarısı verdiği sürece alınmaz.

from asyncio   import Semaphore, gather
from httpx     import AsyncClient, Timeout
from re        import search, findall
from helpers   import str2latlng, kaydet, konsol, mjpeg_canli_mi

SITE    = "https://www.seydisehir.bel.tr"
MERKEZ  = (37.4192, 31.8486)

class Seydisehir:
    def __init__(self):
        self.oturum = AsyncClient(
            timeout          = Timeout(10, connect=10, read=30, write=10),
            follow_redirects = True,
            headers          = {"User-Agent": "Mozilla/5.0"}
        )
        self.sinir  = Semaphore(4)

    async def paket(self) -> str:
        """Sitenin JS paketi (adı her derlemede değişiyor)"""
        sayfa = (await self.oturum.get(f"{SITE}/canliyayinlar")).text
        yol   = search(r'src="([^"]*/build/assets/app-[^"]+\.js)"', sayfa)
        if not yol:
            raise ValueError("JS paketi bulunamadı")

        return (await self.oturum.get(yol.group(1))).text

    @staticmethod
    def liste(paket: str, ad: str) -> list[tuple[str, str]]:
        dizi = search(rf"{ad}=\[(.*?)\]", paket)
        return findall(r'ad:"([^"]+)",url:("[^"]+"|\w+\("[^"]+"\))', dizi.group(1)) if dizi else []

    async def player_im_canli_mi(self, url: str) -> bool:
        try:
            async with self.sinir:
                istek = await self.oturum.get(url, headers={"Referer": f"{SITE}/"})
            return istek.status_code == 200 and "Güncelleyin" not in istek.text and len(istek.text) > 1000
        except Exception:
            return False

    async def kamera(self, ad: str, url: str, bicim: str, kodlama: str) -> dict | None:
        if bicim == "EMBED":
            canli = await self.player_im_canli_mi(url)
        else:
            async with self.sinir:
                canli = await mjpeg_canli_mi(self.oturum, url)

        if not canli:
            konsol.log(f"[yellow][Seydişehir] Yayın yok: {ad}")
            return None

        latitude, longitude = await str2latlng(f"{ad}, Seydişehir, Konya, Türkiye", merkez=MERKEZ, yaricap=0.3)
        return {
            "description" : ad,
            "latitude"    : latitude,
            "longitude"   : longitude,
            "url"         : url,
            "encoding"    : kodlama,
            "format"      : bicim
        }

    async def getir(self) -> dict[list[dict]]:
        paket = await self.paket()

        # Mahalle adresi paketteki şablon fonksiyonuyla üretiliyor: mahalleKamerasi("ad")
        sablon = search(r"mahalleKamerasi=\w+=>`([^`]+)\$\{\w+\}([^`]*)`", paket)

        isler = []
        for ad, url in self.liste(paket, "SEHIR_KAMERALARI"):
            isler.append(self.kamera(ad, url.strip('"'), "IMAGE_STREAM", "MJPEG"))

        if sablon:
            for ad, url in self.liste(paket, "MAHALLE_KAMERALARI"):
                kamera = search(r'\("([^"]+)"\)', url)
                if kamera:
                    isler.append(self.kamera(ad, f"{sablon.group(1)}{kamera.group(1)}{sablon.group(2)}", "EMBED", "H.264"))

        sonuclar = await gather(*isler)
        return {"Seydişehir": [k for k in sonuclar if k]}

async def basla():
    belediye      = Seydisehir()
    gelen_veriler = await belediye.getir()

    kaydet("Konya", gelen_veriler)
