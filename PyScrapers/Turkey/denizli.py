from Kekik.cli import konsol
from httpx     import AsyncClient, Timeout
from parsel    import Selector
from re        import search
from json      import load, dumps
from helpers   import str2latlng

class Denizli:
    def __init__(self):
        self.belediye_url = "http://www.denizli.bel.tr/Default.aspx?k=kameralar"
        self.oturum       = AsyncClient(timeout=Timeout(10, connect=10, read=5*60, write=10))

    async def kameralar(self) -> dict[str, str]:
        istek = await self.oturum.get("http://www.denizli.bel.tr/Default.aspx?k=kameralar")
        secici = Selector(text=istek.text)

        # http://[ip_adresi]:1935/canliyayin/[rel_degeri].stream/playlist.m3u8

        ip_adresi = search(r"var rtmpip='(.*?)';", secici.css("#ctl14_areaScript script::text").get()).group(1)

        kameralar = []
        for kamera in secici.css("a.dropdown-item.kamera"):
            rel_degeri = kamera.attrib.get("rel")
            isim = kamera.css("::text").get().strip()
            if rel_degeri and isim:
                kameralar.append({
                    "title" : isim,
                    "hls"         : f"http://{ip_adresi}:1935/canliyayin/{rel_degeri}.stream/playlist.m3u8"
                })
        return kameralar

    async def getir(self) -> dict[list[dict]]:
        kameralar = await self.kameralar()

        veri = {"Belediye": []}
        for kamera_veri in kameralar:

            latlngstring = search(r"(.+?)(?:\s*-\s*.*)?$", kamera_veri['title']).group(1)
            latitude, longitude = await str2latlng(f"{latlngstring}, Denizli, Türkiye")

            veri["Belediye"].append({
                "description" : kamera_veri["title"],
                "latitude"    : latitude,
                "longitude"   : longitude,
                "url"         : kamera_veri["hls"],
                "encoding"    : "H.264",
                "format"      : "M3U8"
            })

        return veri

async def basla():
    belediye      = Denizli()
    gelen_veriler = await belediye.getir()

    konsol.print(gelen_veriler)
    konsol.log(f"[yellow][Denizli] [+] {len(gelen_veriler['Belediye'])} Adet Kamera Bulundu")

    turkey_json = "../cameras/Turkey.json"

    with open(turkey_json, "r", encoding="utf-8") as dosya:
        mevcut_veriler = load(dosya)

    if gelen_veriler == mevcut_veriler.get("Denizli"):
        konsol.log("[red][Denizli] [!] Yeni Veri Yok")
        return

    if mevcut_veriler.get("Denizli"):
        del mevcut_veriler["Denizli"]
    mevcut_veriler["Denizli"] = gelen_veriler

    with open(turkey_json, "w", encoding="utf-8") as dosya:
        dosya.write(dumps(mevcut_veriler, sort_keys=True, ensure_ascii=False, indent=2))

    konsol.log(f"[green][Denizli] [+] {len(gelen_veriler['Belediye'])} Adet Kamera Eklendi")