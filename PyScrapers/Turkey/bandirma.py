# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from Kekik.cli import konsol
from httpx     import AsyncClient, Timeout
from json      import load, dumps
from helpers   import str2latlng

class Bandirma:
    def __init__(self):
        self.oturum = AsyncClient(timeout=Timeout(10, connect=10, read=5*60, write=10))

    async def kameralar(self) -> dict[str, str]:
        istek = await self.oturum.get("https://wowza.yayin.com.tr/playlist/bandirmabeltr/playlist_bandirmabeltr.json")
        return istek.json()

    async def getir(self) -> dict[list[dict]]:
        kameralar = await self.kameralar()

        veri = {"Bandirma": []}
        for kamera_veri in kameralar.get("playlist", []):
            latitude, longitude = await str2latlng(f"{kamera_veri['title']}, Bandırma, Balıkesir, Türkiye")

            veri["Bandirma"].append({
                "description" : kamera_veri["title"],
                "latitude"    : latitude,
                "longitude"   : longitude,
                "url"         : "https:" + kamera_veri["sources"][0]["file"],
                "encoding"    : "H.264",
                "format"      : "M3U8"
            })

        return veri

async def basla():
    belediye      = Bandirma()
    gelen_veriler = await belediye.getir()

    konsol.print(gelen_veriler)
    konsol.log(f"[yellow][Balıkesir][Bandırma] [+] {len(gelen_veriler['Bandirma'])} Adet Kamera Bulundu")

    turkey_json = "../cameras/Turkey.json"

    with open(turkey_json, "r", encoding="utf-8") as dosya:
        mevcut_veriler = load(dosya)

    if not mevcut_veriler.get("Balıkesir"):
        mevcut_veriler["Balıkesir"] = {}

    if gelen_veriler["Bandirma"] == mevcut_veriler.get("Balıkesir", {}).get("Bandirma"):
        konsol.log("[red][Balıkesir][Bandırma] [!] Yeni Veri Yok")
        return

    mevcut_veriler["Balıkesir"]["Bandirma"] = gelen_veriler["Bandirma"]

    with open(turkey_json, "w", encoding="utf-8") as dosya:
        dosya.write(dumps(mevcut_veriler, sort_keys=True, ensure_ascii=False, indent=2))

    konsol.log(f"[green][Balıkesir][Bandırma] [+] {len(gelen_veriler['Bandirma'])} Adet Kamera Eklendi")
