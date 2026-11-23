# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

# Kaynak: Gölyayla (Kabahor) köyü, İkizdere / Rize — https://golyayla.net
# Köyün kendi sitesi; kameralar YouTube canlı yayını olarak yayınlanıyor.
# youtube_status.php herkese açık durum tablosu: kamera adı, YouTube bağlantısı, "Yayinda" durumu.
# Harita EMBED biçimini iframe ile gösteriyor (map.html).

from httpx     import AsyncClient, Timeout
from parsel    import Selector
from re        import search, sub
from helpers   import kaydet

# Konumlar köyün Google My Maps haritasından (golyayla.net/map.php, KML: boylam,enlem).
# Kamera adı bu öneklerden biriyle başlıyorsa o noktaya konur; yoksa köy merkezi.
NOKTALAR = [
    # ad öneki       enlem       boylam
    ("Gavuz",        40.661734,  40.611726),  # Gavuzoğulları
    ("Yayla",        40.632729,  40.680413),
    ("Taşköprü",     40.631156,  40.685751),
    ("Kapar",        40.631854,  40.662514),
    ("Halko",        40.649037,  40.626756),
    ("Şako",         40.626442,  40.684680),
    ("Kuzey Merze",  40.637562,  40.644913),
    ("Merze",        40.637562,  40.644913),
    ("Koğoş",        40.648729,  40.634338),
    ("Çen",          40.653187,  40.636636),
    ("Feyiz",        40.637520,  40.651928),  # Feyizlerin Ayrımı
    ("Yanmış",       40.682024,  40.615779),  # Yanmışlık
    ("Petran",       40.623163,  40.714001),  # Kabahor Taşı yönü
]
KOY_MERKEZI = (40.614503, 40.721534)  # Gölyayla

def konum(ad: str) -> tuple[float, float]:
    for onek, enlem, boylam in NOKTALAR:
        if ad.startswith(onek):
            return enlem, boylam
    return KOY_MERKEZI

class Golyayla:
    def __init__(self):
        self.durum_url = "https://golyayla.net/youtube_status.php"
        self.oturum    = AsyncClient(
            timeout          = Timeout(10, connect=10, read=60, write=10),
            follow_redirects = True,
            headers          = {"User-Agent": "Mozilla/5.0"}
        )

    async def kameralar(self) -> dict[str, str]:
        istek  = await self.oturum.get(self.durum_url)
        secici = Selector(istek.text)

        kameralar = {}
        for satir in secici.css("table#customers tr"):
            baglanti = satir.css("td:nth-child(1) a::attr(href)").get("")
            ad       = satir.css("td:nth-child(1) a::text").get("").strip()
            durum    = satir.css("td:nth-child(4)::text").get("").strip()

            video = search(r"youtu\.be/([\w-]{11})", baglanti)
            if not video or not ad or durum != "Yayinda":
                continue

            kameralar[sub(r"^\d+\s*-\s*", "", ad)] = video.group(1)

        return kameralar

    async def gomulebilir_mi(self, video_id: str) -> bool:
        """Gömme kapalı videolarda YouTube oEmbed 401 döner; iframe'de oynamaz."""
        try:
            istek = await self.oturum.get("https://www.youtube.com/oembed", params={"url": f"https://www.youtube.com/watch?v={video_id}", "format": "json"})
            return istek.status_code == 200
        except Exception:
            return False

    async def getir(self) -> dict[list[dict]]:
        veri = {"Gölyayla": []}
        for ad, video_id in (await self.kameralar()).items():
            latitude, longitude = konum(ad)

            if await self.gomulebilir_mi(video_id):
                url, bicim = f"https://www.youtube.com/embed/{video_id}?autoplay=1&mute=1", "EMBED"
            else:
                # Gömme kapalı: canlı yayın küçük resmi (YouTube ~5 dk'da bir yeniliyor)
                url, bicim = f"https://i.ytimg.com/vi/{video_id}/hqdefault_live.jpg", "IMAGE_STREAM"

            veri["Gölyayla"].append({
                "description" : f"Gölyayla - {ad}",
                "latitude"    : latitude,
                "longitude"   : longitude,
                "url"         : url,
                "encoding"    : "H.264" if bicim == "EMBED" else "JPEG",
                "format"      : bicim
            })

        return veri

async def basla():
    kaynak        = Golyayla()
    gelen_veriler = await kaynak.getir()

    kaydet("Rize", gelen_veriler)
