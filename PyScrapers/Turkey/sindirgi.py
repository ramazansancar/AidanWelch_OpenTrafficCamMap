# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from Kekik.cli import konsol
from httpx     import AsyncClient, Timeout
from json      import load, dumps
from helpers   import str2latlng

class Sindirgi:
    def __init__(self):
        self.oturum = AsyncClient(timeout=Timeout(10, connect=10, read=5*60, write=10))

    async def kameralar(self) -> dict[str, str]:
        try:
            istek = await self.oturum.get("https://wowza.yayin.com.tr/playlist/sindirgibel/playlist_sindirgibel.json")
            return istek.json()
        except Exception as e:
            konsol.log(f"[red][Sındırgı] Kameralar alınamadı: {str(e)}")
            return {}

    async def getir(self) -> dict[list[dict]]:
        kameralar = await self.kameralar()
        
        if not kameralar:
            konsol.log("[red][Sındırgı] Kamera listesi alınamadı")
            return {"Sındırgı": []}

        veri = {"Sındırgı": []}
        for kamera_veri in kameralar.get("playlist", []):
            try:
                latitude, longitude = await str2latlng(f"{kamera_veri['title']}, Sındırgı, Balıkesir, Türkiye")

                veri["Sındırgı"].append({
                    "description" : kamera_veri["title"],
                    "latitude"    : latitude,
                    "longitude"   : longitude,
                    "url"         : "https:" + kamera_veri["sources"][0]["file"],
                    "encoding"    : "H.264",
                    "format"      : "M3U8"
                })
            except Exception as e:
                konsol.log(f"[red][Sındırgı] {kamera_veri.get('title', 'Bilinmeyen')} kamerası işlenirken hata: {str(e)}")
                continue

        return veri

async def basla():
    belediye      = Sindirgi()
    gelen_veriler = await belediye.getir()

    konsol.print(gelen_veriler)
    konsol.log(f"[yellow][Balıkesir][Sındırgı] [+] {len(gelen_veriler['Sındırgı'])} Adet Kamera Bulundu")

    turkey_json = "../cameras/Turkey.json"

    with open(turkey_json, "r", encoding="utf-8") as dosya:
        mevcut_veriler = load(dosya)

    if gelen_veriler.get("Sındırgı") == mevcut_veriler.get("Balıkesir", {}).get("Sındırgı"):
        konsol.log("[red][Balıkesir][Sındırgı] [!] Yeni Veri Yok")
        return

    if "Balıkesir" not in mevcut_veriler:
        mevcut_veriler["Balıkesir"] = {}
    
    mevcut_veriler["Balıkesir"]["Sındırgı"] = gelen_veriler["Sındırgı"]

    with open(turkey_json, "w", encoding="utf-8") as dosya:
        dosya.write(dumps(mevcut_veriler, sort_keys=True, ensure_ascii=False, indent=2))

    konsol.log(f"[green][Balıkesir][Sındırgı] [+] {len(gelen_veriler['Sındırgı'])} Adet Kamera Eklendi")