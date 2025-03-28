# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from Kekik.cli import konsol
from httpx     import AsyncClient, Timeout
from json      import load, dumps
from helpers   import str2latlng

class Caycuma:
    def __init__(self):
        self.oturum = AsyncClient(timeout=Timeout(10, connect=10, read=5*60, write=10))

    async def kameralar(self) -> dict[str, str]:
        istek = await self.oturum.get("https://wowza.yayin.com.tr/playlist/caycumabeltr/playlist_caycumabeltr.json")
        return istek.json()

    async def getir(self) -> dict[list[dict]]:
        kameralar = await self.kameralar()

        veri = {"Caycuma": []}
        for kamera_veri in kameralar.get("playlist", []):
            latitude, longitude = await str2latlng(f"{kamera_veri['title']}, Çaycuma, Zonguldak, Türkiye")

            veri["Caycuma"].append({
                "description" : kamera_veri["title"],
                "latitude"    : latitude,
                "longitude"   : longitude,
                "url"         : "https:" + kamera_veri["sources"][0]["file"],
                "encoding"    : "H.264",
                "format"      : "M3U8"
            })

        return veri

async def basla():
    belediye      = Caycuma()
    gelen_veriler = await belediye.getir()

    konsol.print(gelen_veriler)
    konsol.log(f"[yellow][Zonguldak][Caycuma] [+] {len(gelen_veriler['Caycuma'])} Adet Kamera Bulundu")

    turkey_json = "../cameras/Turkey.json"

    with open(turkey_json, "r", encoding="utf-8") as dosya:
        mevcut_veriler = load(dosya)

    if gelen_veriler == mevcut_veriler.get("Zonguldak"):
        konsol.log("[red][Zonguldak][Caycuma] [!] Yeni Veri Yok")
        return

    if mevcut_veriler.get("Zonguldak"):
        del mevcut_veriler["Zonguldak"]
    mevcut_veriler["Zonguldak"] = gelen_veriler

    with open(turkey_json, "w", encoding="utf-8") as dosya:
        dosya.write(dumps(mevcut_veriler, sort_keys=True, ensure_ascii=False, indent=2))

    konsol.log(f"[green][Zonguldak][Caycuma] [+] {len(gelen_veriler['Caycuma'])} Adet Kamera Eklendi")