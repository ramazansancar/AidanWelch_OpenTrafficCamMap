# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

# ipcamlive.com kameraları — gömme oynatıcı (EMBED).
# HLS adresi oturum başına üretildiği için doğrudan M3U8 tutulamıyor; oynatıcı sayfası iframe'de açılıyor.
# Yayın durumu ipcamlive'ın kendi oynatıcısının kullandığı getcamerastreamstate.php ile denetleniyor.
# Takma ad (alias) kamera sahibinin sitesindeki gömme kodundan alınır; domain kilidi açık olanlar eklenemez.

from asyncio   import gather
from httpx     import AsyncClient, Timeout
from helpers   import kaydet, konsol

KAMERALAR = [
    # takma ad,               sunucu,              il,       alt grup,     açıklama,                         (enlem, boylam)
    ("belcekizbeachclub", "ipcamlive.com",    "Mugla",  "Fethiye",    "Ölüdeniz Belcekız Beach Club",   (36.5497, 29.1150)),
    ("674efe17585d8",     "g2.ipcamlive.com", "Bolu",   "Kartalkaya", "Kartal Otel",                    (40.6100, 31.7575)),
]

class IPCamLive:
    def __init__(self):
        self.oturum = AsyncClient(
            timeout = Timeout(10, connect=10, read=30, write=10),
            headers = {"User-Agent": "Mozilla/5.0"}
        )

    async def yayinda_mi(self, takma_ad: str, sunucu: str) -> bool:
        oynatici = f"https://{sunucu}/player/player.php?alias={takma_ad}"
        try:
            istek = await self.oturum.get(
                f"https://{sunucu}/player/getcamerastreamstate.php",
                params  = {"alias": takma_ad},
                headers = {"Referer": oynatici}
            )
            durum = istek.json().get("details", {})
        except Exception as hata:
            konsol.log(f"[red][ipcamlive][{takma_ad}] Durum okunamadı: {hata}")
            return False

        return durum.get("enabled", "1") == "1" and durum.get("streamavailable") == "1" and durum.get("domainlockenabled") != "1"

    async def kamera(self, takma_ad, sunucu, il, alt, ad, konum) -> tuple[str, str, dict | None]:
        if not await self.yayinda_mi(takma_ad, sunucu):
            konsol.log(f"[yellow][ipcamlive] Yayın yok: {ad}")
            return il, alt, None

        return il, alt, {
            "description" : ad,
            "latitude"    : konum[0],
            "longitude"   : konum[1],
            "url"         : f"https://{sunucu}/player/player.php?alias={takma_ad}&autoplay=1&mute=1",
            "encoding"    : "H.264",
            "format"      : "EMBED"
        }

    async def getir(self) -> dict[str, dict[str, list[dict]]]:
        iller: dict[str, dict[str, list[dict]]] = {}
        for il, alt, kamera in await gather(*(self.kamera(*satir) for satir in KAMERALAR)):
            iller.setdefault(il, {}).setdefault(alt, [])
            if kamera:
                iller[il][alt].append(kamera)

        return iller

async def basla():
    kaynak = IPCamLive()
    for il, gruplar in (await kaynak.getir()).items():
        kaydet(il, gruplar)
