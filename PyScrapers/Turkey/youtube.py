# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

# YouTube'da 7/24 canlı kamera yayını yapan belediye / köy / yayla kanalları.
# Her kanalın "Canlı" (streams) sekmesi okunur; o an CANLI rozetli videolar alınır.
# Yayın yeniden başlayınca video kimliği değişse de kanal üzerinden yenisi bulunur.
# Gömme açıksa EMBED (iframe), kapalıysa canlı küçük resim (IMAGE_STREAM).
# Gölyayla kanalları ayrı: golyayla.py.

from asyncio   import Semaphore, gather
from httpx     import AsyncClient, Timeout
from json      import loads, dumps
from re        import search, sub, IGNORECASE
from helpers   import str2latlng, kaydet, konsol

KANALLAR = [
    # kanal kimliği,              il,           alt grup,        geocode eki,                   merkez (enlem, boylam),  yarıçap, başlık süzgeci
    ("UCRaLemo6M0haUrwGWTQoM1A", "Giresun",   "Hasan Yayında",  "Giresun",                     (40.9128, 38.3895),     1.0,     None),
    ("UCnNnhgdt28Azq1HPMtKsLNg", "Giresun",   "Keşap",          "Keşap, Giresun",              (40.9174, 38.5139),     0.3,     None),
    ("UCCNJc-Fx-xz5Kquksih0TzA", "Giresun",   "Alucra",         "Alucra, Giresun",             (40.3189, 38.7660),     0.3,     None),
    ("UC0mzEl3xtDs59izgIaWSW4g", "Giresun",   "Merkez Köyleri", "Merkez, Giresun",             (40.9128, 38.3895),     0.5,     None),
    ("UC5nsD9S24JzzJZK-H5ExN0Q", "Giresun",   "Şebinkarahisar", "Şebinkarahisar, Giresun",     (40.2886, 38.4239),     0.4,     None),
    ("UCKRILTo_VTbb0GwY3bcthFw", "Tokat",     "Pınarbeyli",     "Pınarbeyli, Erbaa, Tokat",    (40.6370, 36.5370),     0.3,     None),
    ("UCD2RmMbZ0-Wsigb_kUJFSCg", "Tokat",     "Pınarbeyli",     "Pınarbeyli, Erbaa, Tokat",    (40.6370, 36.5370),     0.3,     None),
    ("UCfFX6PtRQGLulexxQH7QGXA", "Zonguldak", "Devrek",         "Devrek, Zonguldak",           (41.2197, 31.9558),     0.3,     None),
    ("UCW-0vM5gzfqHaHecrSYW_Mg", "Aksaray",   "Selime",         "Selime, Güzelyurt, Aksaray",  (38.2955, 34.2589),     0.3,     None),
    ("UC3X8M2MY_hcoMvA0DN9-olA", "Osmaniye",  "Karaçay",        "Karaçay, Osmaniye",           (37.1500, 36.2500),     0.5,     None),
    ("UCtjBLnQuaEgrZtyhpNsn9uw", "Antalya",   "Muratpaşa",      "Muratpaşa, Antalya",          (36.8850, 30.7056),     0.3,     None),
    ("UCUwiUvWeYt_YliYWjqBhkeg", "Nevşehir",  "Göreme",         "Göreme, Nevşehir",            (38.6431, 34.8289),     0.3,     r"cappadocia|kapadokya|göreme"),
]

# Başlıktaki yayın sözcükleri, emojiler, sıra numaraları geocode'u bozuyor
TEMIZLE = r"canlı\s*yayın|canli\s*yayin|live\s*cam|live|7/24|24/7|hareketli\s*camera|kesintisiz|\(.*?\)|\|.*$|[-–:]\s*$"
# Emoji, tuş başlığı (rakam + U+FE0F + U+20E3) ve simge blokları; editörde ? görünmesin diye kaçış dizisiyle yazıldı
EMOJI   = r"\d?[\uFE0F\u20E3]+|[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF]"

def temiz_baslik(baslik: str) -> str:
    baslik = sub(EMOJI, " ", baslik)
    baslik = sub(TEMIZLE, " ", baslik, flags=IGNORECASE)
    baslik = sub(r"^\s*\(?\d+\)?\s*", "", baslik)
    return " ".join(baslik.split()).strip(" -–:|")

class YouTube:
    def __init__(self):
        self.oturum = AsyncClient(
            timeout          = Timeout(15, connect=10, read=60, write=10),
            follow_redirects = True,
            headers          = {"User-Agent": "Mozilla/5.0", "Accept-Language": "tr"},
            cookies          = {"CONSENT": "YES+"},
        )
        self.sinir  = Semaphore(4)

    async def canli_videolar(self, kanal: str) -> list[tuple[str, str]]:
        """Kanalın Canlı sekmesinde CANLI rozetli videolar: [(video_id, başlık)]"""
        async with self.sinir:
            istek = await self.oturum.get(f"https://www.youtube.com/channel/{kanal}/streams")

        veri = search(r"var ytInitialData = (\{.*?\});</script>", istek.text)
        if not veri:
            return []

        videolar = []
        def gez(o):
            if isinstance(o, dict):
                if "lockupViewModel" in o:
                    kutu  = dumps(o["lockupViewModel"], ensure_ascii=False)
                    video = o["lockupViewModel"].get("contentId")
                    ad    = search(r'"title":\s*\{"content":\s*"((?:[^"\\]|\\.)*)"', kutu)
                    if video and ad and "BADGE_STYLE_LIVE" in kutu:
                        videolar.append((video, loads(f'"{ad.group(1)}"')))
                for x in o.values():
                    gez(x)
            elif isinstance(o, list):
                for x in o:
                    gez(x)

        gez(loads(veri.group(1)))
        return list(dict.fromkeys(videolar))

    async def gomulebilir_mi(self, video_id: str) -> bool:
        async with self.sinir:
            try:
                istek = await self.oturum.get("https://www.youtube.com/oembed", params={"url": f"https://www.youtube.com/watch?v={video_id}", "format": "json"})
                return istek.status_code == 200
            except Exception:
                return False

    async def kanal_getir(self, kanal, il, alt, ek, merkez, yaricap, suzgec) -> tuple[str, str, list[dict]]:
        try:
            videolar = await self.canli_videolar(kanal)
        except Exception as hata:
            konsol.log(f"[red][YouTube][{alt}] Kanal okunamadı: {hata}")
            return il, alt, []

        kameralar = []
        for video_id, baslik in videolar:
            if suzgec and not search(suzgec, baslik, IGNORECASE):
                continue

            ad = temiz_baslik(baslik) or alt
            latitude, longitude = await str2latlng(f"{ad}, {ek}, Türkiye", merkez=merkez, yaricap=yaricap)

            if await self.gomulebilir_mi(video_id):
                url, bicim, kodlama = f"https://www.youtube.com/embed/{video_id}?autoplay=1&mute=1", "EMBED", "H.264"
            else:
                url, bicim, kodlama = f"https://i.ytimg.com/vi/{video_id}/hqdefault_live.jpg", "IMAGE_STREAM", "JPEG"

            kameralar.append({
                "description" : ad,
                "latitude"    : latitude,
                "longitude"   : longitude,
                "url"         : url,
                "encoding"    : kodlama,
                "format"      : bicim
            })

        return il, alt, kameralar

    async def getir(self) -> dict[str, dict[str, list[dict]]]:
        sonuclar = await gather(*(self.kanal_getir(*satir) for satir in KANALLAR))

        iller: dict[str, dict[str, list[dict]]] = {}
        for il, alt, kameralar in sonuclar:
            iller.setdefault(il, {}).setdefault(alt, []).extend(kameralar)

        # Aynı adlı kameralar (ör. birkaç "Pınarbeyli köyü") ayırt edilsin
        for gruplar in iller.values():
            for kameralar in gruplar.values():
                sayac: dict[str, int] = {}
                for kamera in kameralar:
                    sayac[kamera["description"]] = sayac.get(kamera["description"], 0) + 1
                    if sayac[kamera["description"]] > 1:
                        kamera["description"] += f" {sayac[kamera['description']]}"

        return iller

async def basla():
    kaynak = YouTube()
    for il, gruplar in (await kaynak.getir()).items():
        kaydet(il, gruplar)
