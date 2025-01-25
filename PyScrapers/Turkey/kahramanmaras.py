# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from Kekik.cli import konsol
from httpx     import AsyncClient, Timeout
from parsel    import Selector
from re        import search
from json      import load, dumps
from helpers   import str2latlng

class Kahramanmaras:
    def __init__(self):
        self.belediye_url = "https://kamera.kahramanmaras.bel.tr/"
        self.oturum       = AsyncClient(timeout=Timeout(10, connect=10, read=5*60, write=10))

    async def kameralar(self) -> dict[str, str]:
        istek  = await self.oturum.get(self.belediye_url)
        secici = Selector(istek.text)

        return {
            kamera.css("a::text").get() : self.belediye_url + kamera.css("a::attr(href)").get()
            for kamera in secici.css("ul.menuzord-menu li")
            if "fa-video-camera" in kamera.css("i::attr(class)").get() and not kamera.css("li.hidden") and not kamera.css("li a::attr(href)").re(r"<!--.*-->")
        }

    async def kamera_detay(self, kamera_url:str) -> dict | None:
        istek  = await self.oturum.get(kamera_url)
        secici = Selector(istek.text)

        return {
            "title"        : secici.css("h4.text-uppercase::text").get(),
            "hls"          : secici.css("source::attr(src)").get()
        }

    async def getir(self) -> dict[list[dict]]:
        kameralar = await self.kameralar()

        veri = {"Belediye": []}
        for kamera_adi, kamera_url in kameralar.items():
            kamera_detay = await self.kamera_detay(kamera_url)
            if not kamera_detay:
                continue
            latitude, longitude = await str2latlng(f"{search(r"(.+?)\s*\d*$", kamera_adi).group(1)}, Kahramanmaraş, Türkiye")

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
    belediye      = Kahramanmaras()
    gelen_veriler = await belediye.getir()

    konsol.print(gelen_veriler)
    konsol.log(f"[yellow][Kahramanmaraş] [+] {len(gelen_veriler['Belediye'])} Adet Kamera Bulundu")

    turkey_json = "../cameras/Turkey.json"

    with open(turkey_json, "r", encoding="utf-8") as dosya:
        mevcut_veriler = load(dosya)

    if gelen_veriler == mevcut_veriler.get("Kahramanmaras"):
        konsol.log("[red][!] [Kahramanmaraş] Yeni Veri Yok")
        return

    if mevcut_veriler.get("Kahramanmaras"):
        del mevcut_veriler["Kahramanmaras"]
    mevcut_veriler["Kahramanmaras"] = gelen_veriler

    with open(turkey_json, "w", encoding="utf-8") as dosya:
        dosya.write(dumps(mevcut_veriler, sort_keys=True, ensure_ascii=False, indent=2))

    konsol.log(f"[green][Kahramanmaraş] [+] {len(gelen_veriler['Belediye'])} Adet Kamera Eklendi")