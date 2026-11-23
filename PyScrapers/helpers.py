# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from json     import dumps, loads, load
from httpx    import AsyncClient
from datetime import datetime
from os       import environ, path
from ssl      import SSLContext, create_default_context
from certifi  import where
import re
import ssl

TURKEY_JSON = "../cameras/Turkey.json"

# Bazı sunucular ara sertifikayı göndermiyor (eksik zincir); tarayıcılar bunu
# AIA ile tamamlıyor, Python tamamlamıyor. Eksik ara sertifikalar bu dosyada.
ARA_SERTIFIKALAR = path.join(path.dirname(path.abspath(__file__)), "ara_sertifikalar.pem")

def ssl_baglami() -> SSLContext:
    """certifi kökleri + ara_sertifikalar.pem. Doğrulama açık kalır."""
    baglam = create_default_context(cafile=where())
    baglam.load_verify_locations(cafile=ARA_SERTIFIKALAR)
    # Ara sertifika tek başına güven çapası sayılmasın (Python 3.13+ varsayılanı açık):
    # zincir yine certifi'deki bir köke bağlanmak zorunda.
    if hasattr(ssl, "VERIFY_X509_PARTIAL_CHAIN"):
        baglam.verify_flags &= ~ssl.VERIFY_X509_PARTIAL_CHAIN
    return baglam

class Konsol:
    """Kekik.cli.konsol (rich) yerine küçük çıktı yardımcısı.

    `[red]...` gibi rich etiketlerini ANSI renge çevirir; `[Konya]` gibi
    stil olmayan köşeli parantezler olduğu gibi kalır. NO_COLOR ile renk kapanır.
    """
    STILLER = {
        "bold": "1", "red": "31", "green": "32", "yellow": "33",
        "blue": "34", "purple": "35", "magenta": "35", "cyan": "36", "white": "37",
    }
    ETIKET  = re.compile(r"\[(/?)([a-z ]*)\]")

    def __init__(self):
        self.renkli = "NO_COLOR" not in environ

    def _bicimle(self, metin: str) -> str:
        def degistir(eslesme: re.Match) -> str:
            kapanis, kelimeler = eslesme.group(1), eslesme.group(2).split()
            if kapanis and not kelimeler:
                return "\033[0m" if self.renkli else ""
            if not kelimeler or any(k not in self.STILLER for k in kelimeler):
                return eslesme.group(0)
            if not self.renkli:
                return ""
            return "\033[0m" if kapanis else "\033[" + ";".join(self.STILLER[k] for k in kelimeler) + "m"

        sonuc = self.ETIKET.sub(degistir, metin)
        return sonuc + "\033[0m" if self.renkli and "\033[" in sonuc else sonuc

    def print(self, *nesneler) -> None:
        print(*(self._bicimle(n) if isinstance(n, str) else n for n in nesneler), flush=True)

    def log(self, *nesneler) -> None:
        self.print(f"[{datetime.now():%H:%M:%S}]", *nesneler)

konsol = Konsol()

def tr_baslik(metin: str) -> str:
    """Kekik.unicode_tr(metin).title() ile aynı sonuç (cache.json anahtarları buna bağlı).

    Her kelime: ilk harf Türkçe büyük (i→İ, ı→I), kalanı Türkçe küçük (I→ı, İ→i);
    sonra Python str.title() uygulanır.
    """
    def buyuk(s: str) -> str:
        return s.replace("ı", "I").replace("i", "İ").upper()

    def kucuk(s: str) -> str:
        return s.replace("I", "ı").replace("İ", "i").lower()

    return " ".join(buyuk(k[0]) + kucuk(k[1:]) for k in metin.split()).title()

cache = {}

async def canli_mi(oturum: AsyncClient, hls_url: str) -> bool:
    """HLS listesi şu an cevap veriyor mu (200 + #EXTM3U)."""
    try:
        istek = await oturum.get(hls_url)
        return istek.status_code == 200 and istek.text.lstrip().startswith("#EXTM3U")
    except Exception:
        return False

def kaydet(il: str, gelen_veriler: dict[str, list[dict]]) -> None:
    """Bir ilin alt gruplarını (ilçe / kaynak) Turkey.json'a yazar.

    Boş gelen alt gruplar yazılmaz: kaynak geçici olarak cevap vermediğinde
    ya da sayfa yapısı değiştiğinde mevcut kameralar silinmez.
    Diğer alt gruplara (başka betiklerin yazdıkları) dokunulmaz.
    """
    dolu = {alt: kameralar for alt, kameralar in gelen_veriler.items() if kameralar}
    bos  = [alt for alt, kameralar in gelen_veriler.items() if not kameralar]

    for alt in bos:
        konsol.log(f"[red][{il}][{alt}] [!] Kamera Bulunamadı, Mevcut Veri Korunuyor")

    if not dolu:
        return

    with open(TURKEY_JSON, "r", encoding="utf-8") as dosya:
        mevcut_veriler = load(dosya)

    il_veri = mevcut_veriler.get(il) or {}

    degisen = {alt: kameralar for alt, kameralar in dolu.items() if il_veri.get(alt) != kameralar}
    if not degisen:
        konsol.log(f"[yellow][{il}] [!] Yeni Veri Yok")
        return

    il_veri.update(degisen)
    mevcut_veriler[il] = il_veri

    with open(TURKEY_JSON, "w", encoding="utf-8", newline="\n") as dosya:
        dosya.write(dumps(mevcut_veriler, sort_keys=True, ensure_ascii=False, indent=2))

    for alt, kameralar in degisen.items():
        konsol.log(f"[green][{il}][{alt}] [+] {len(kameralar)} Adet Kamera Kaydedildi")

# Get Cache File
try:
    with open("cache.json", "r", encoding="utf-8") as dosya:
        cache = dosya.read()
        cache = loads(cache)
except FileNotFoundError:
    with open("cache.json", "w", encoding="utf-8", newline="\n") as dosya:
        dosya.write("{}")
except Exception as hata:
    print(f"Cache Dosyası Okunurken Hata Oluştu: {hata}")

async def str2latlng(str:str, merkez:tuple[float, float] | None = None, yaricap:float = 1.0) -> tuple[float, float]:
    """Yer adını koordinata çevirir.

    `merkez` verilirse: bulunamayan ya da merkeze `yaricap` dereceden uzak
    düşen sonuç (aynı adlı başka bir yer) yerine `merkez` döner.
    """
    lat, lng = await _str2latlng(str)

    if merkez and (abs(float(lat) - merkez[0]) > yaricap or abs(float(lng) - merkez[1]) > yaricap):
        print("- merkez kullanıldı:", str, lat, lng)
        return merkez

    return lat, lng

async def _str2latlng(str:str) -> tuple[float, float]:
    oturum  = AsyncClient(headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"}, timeout=15)
    yer_adi = re.sub(r"\s*\d+$", "", tr_baslik(str))

    if yer_adi in cache:
        return cache[yer_adi]
    istek   = await oturum.get(f"https://publicapi.ramazansancar.com.tr/google/maps/names/{yer_adi}")
    try:
        lat = istek.json()["data"][0]["geometry"]["location"]["lat"]
        lng = istek.json()["data"][0]["geometry"]["location"]["lng"]
        print(yer_adi, lat, lng)
        if yer_adi not in cache:
            cache[yer_adi] = lat, lng

        # Cache File Save
        with open("cache.json", "w", encoding="utf-8", newline="\n") as dosya:
            dosya.write(dumps(cache, sort_keys=True, ensure_ascii=False, indent=2))

        return float(lat) , float(lng)
    except Exception:
        print('- ',0.0, 0.0, yer_adi)
        return 36.14207255403557, 31.208844678148807
