# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

# Listeleyen bir sayfası olmayan, adresi sabit canlı yayınlar.
# Kaynak: http://www.kocbey.com/webcam.html (kcam/*.html sayfalarındaki oynatıcılar).
# Her çalışmada yayın kontrol edilir; kapalı olan yazılmaz.

from httpx     import AsyncClient, Timeout
from helpers   import kaydet, canli_mi, ssl_baglami

KAMERALAR = [
    # il,        alt grup,   açıklama,           enlem,    boylam,   HLS
    ("Burdur",   "Yeşilova", "Salda Gölü",       37.5470,  29.6790,  "https://5a1178b42cc03.streamlock.net:443/salda-golu-2/salda_golu_2.stream/playlist.m3u8"),
    ("Sivas",    "Zara",     "Zara Dörtyol",     39.8953,  37.7522,  "https://server.arvas.com.tr/dortyol.m3u8"),
    ("Sivas",    "Zara",     "Zara Meydan",      39.8961,  37.7540,  "https://server.arvas.com.tr/meydan.m3u8"),
    ("Nevşehir", "Uçhisar",  "Uçhisar Kalesi",   38.6297,  34.8053,  "https://player.rade.com.tr/live/uchisar1.stream/playlist.m3u8"),
]

async def basla():
    oturum = AsyncClient(
        timeout = Timeout(10, connect=10, read=60, write=10),
        headers = {"User-Agent": "Mozilla/5.0"},
        verify  = ssl_baglami(),  # server.arvas.com.tr eksik zincir
    )

    iller: dict[str, dict[str, list[dict]]] = {}
    for il, alt, aciklama, enlem, boylam, hls in KAMERALAR:
        grup = iller.setdefault(il, {}).setdefault(alt, [])
        if not await canli_mi(oturum, hls):
            continue

        grup.append({
            "description" : aciklama,
            "latitude"    : enlem,
            "longitude"   : boylam,
            "url"         : hls,
            "encoding"    : "H.264",
            "format"      : "M3U8"
        })

    for il, gruplar in iller.items():
        kaydet(il, gruplar)
