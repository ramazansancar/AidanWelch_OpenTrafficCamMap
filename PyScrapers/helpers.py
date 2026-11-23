# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from json import dumps, loads, load
from httpx import AsyncClient
from Kekik import unicode_tr
from Kekik.cli import konsol
import re

TURKEY_JSON = "../cameras/Turkey.json"

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
    yer_adi = re.sub(r"\s*\d+$", "", unicode_tr(str).title())

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
