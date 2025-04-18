# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from Kekik.cli import konsol
from httpx     import AsyncClient, Timeout
from json      import load, dumps
from helpers   import str2latlng

class Marmaris:
    def __init__(self):
        self.oturum = AsyncClient(timeout=Timeout(10, connect=10, read=5*60, write=10))

    async def kameralar(self) -> dict[str, str]:
        istek = await self.oturum.get("https://wowza.yayin.com.tr/playlist/marmarisbel/playlist_marmarisbel.json")
        return istek.json()

    async def getir(self) -> dict[list[dict]]:
        kameralar = await self.kameralar()

        veri = {"Marmaris": []}
        for kamera_veri in kameralar.get("playlist", []):
            latitude, longitude = await str2latlng(f"{kamera_veri['title']}, Marmaris, Muğla, Türkiye")

            veri["Marmaris"].append({
                "description" : kamera_veri["title"],
                "latitude"    : latitude,
                "longitude"   : longitude,
                "url"         : "https:" + kamera_veri["sources"][0]["file"],
                "encoding"    : "H.264",
                "format"      : "M3U8"
            })

        return veri


async def basla():
    belediye      = Marmaris()
    gelen_veriler = await belediye.getir()

    konsol.print(gelen_veriler)
    konsol.log(f"[yellow][Muğla][Marmaris] [+] {len(gelen_veriler['Marmaris'])} Adet Kamera Bulundu")

    turkey_json = "../cameras/Turkey.json"

    with open(turkey_json, "r", encoding="utf-8") as dosya:
        mevcut_veriler = load(dosya)

    if gelen_veriler == mevcut_veriler.get("Mugla"):
        konsol.log("[red][Muğla][Marmaris] [!] Yeni Veri Yok")
        return

    if mevcut_veriler.get("Mugla"):
        del mevcut_veriler["Mugla"]
    mevcut_veriler["Mugla"] = gelen_veriler

    with open(turkey_json, "w", encoding="utf-8") as dosya:
        dosya.write(dumps(mevcut_veriler, sort_keys=True, ensure_ascii=False, indent=2))

    konsol.log(f"[green][Muğla][Marmaris] [+] {len(gelen_veriler['Marmaris'])} Adet Kamera Eklendi")