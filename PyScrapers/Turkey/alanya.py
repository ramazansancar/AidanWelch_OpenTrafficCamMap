# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from Kekik.cli import konsol
from httpx     import AsyncClient, Timeout
from re        import search
from json      import load, dumps
from helpers   import str2latlng

class Alanya:
    def __init__(self):
        self.oturum = AsyncClient(timeout=Timeout(10, connect=10, read=5*60, write=10))

    async def kameralar(self) -> dict[str, str]:
        istek = await self.oturum.get("https://wowza.yayin.com.tr/playlist/alanyabeltr/playlist_alanyabeltr.json")
        return istek.json()

    async def getir(self) -> dict[list[dict]]:
        kameralar = await self.kameralar()

        veri = {"Alanya": []}
        for kamera_veri in kameralar.get("playlist", []):
            
            latitude, longitude = await str2latlng(f"{search(r'(.+?)\s*\d*$', kamera_veri['title']).group(1)}, Alanya, Antalya, Türkiye")

            veri["Alanya"].append({
                "description" : kamera_veri["title"],
                "latitude"    : latitude,
                "longitude"   : longitude,
                "url"         : "https:" + kamera_veri["sources"][0]["file"],
                "encoding"    : "H.264",
                "format"      : "M3U8"
            })

        return veri

async def basla():
    belediye      = Alanya()
    gelen_veriler = await belediye.getir()

    konsol.print(gelen_veriler)
    konsol.log(f"[yellow][Antalya][Alanya] [+] {len(gelen_veriler['Alanya'])} Adet Kamera Bulundu")

    turkey_json = "../cameras/Turkey.json"

    with open(turkey_json, "r", encoding="utf-8") as dosya:
        mevcut_veriler = load(dosya)

    if gelen_veriler == mevcut_veriler.get("Antalya"):
        konsol.log("[red][Antalya][Alanya] [!] Yeni Veri Yok")
        return

    if mevcut_veriler.get("Antalya"):
        del mevcut_veriler["Antalya"]
    mevcut_veriler["Antalya"] = gelen_veriler

    with open(turkey_json, "w", encoding="utf-8") as dosya:
        dosya.write(dumps(mevcut_veriler, sort_keys=True, ensure_ascii=False, indent=2))

    konsol.log(f"[green][Antalya][Alanya] [+] {len(gelen_veriler['Alanya'])} Adet Kamera Eklendi")