# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from Kekik.cli import cikis_yap, hata_yakala
from asyncio   import run
from Turkey    import alanya, balikesir, bandirma, caycuma, cayirova, denizli, derebucak, erzurum, giresun, kahramanmaras, karacabey, konya, kutahya, marmaris, nevsehir, rize, samsun, sindirgi, trabzon

BETIKLER = {
    "Alanya"        : alanya,
    "Balıkesir"     : balikesir,
    "Bandırma"      : bandirma,
    "Çaycuma"       : caycuma,
    "Çayırova"      : cayirova,
    "Denizli"       : denizli,
    "Derebucak"     : derebucak,
    "Erzurum"       : erzurum,
    "Giresun"       : giresun,
    "Konya"         : konya,
    "Marmaris"      : marmaris,
    "Karacabey"     : karacabey,
    "Kütahya"       : kutahya,
    "Nevşehir"      : nevsehir,
    "Rize"          : rize,
    "Samsun"        : samsun,
    "Sındırgı"      : sindirgi,
    "Trabzon"       : trabzon,
    "Kahramanmaraş" : kahramanmaras,
}

async def basla():
    # Her şehir ayrı: biri hata verirse diğerleri çalışmaya devam eder
    for ad, betik in BETIKLER.items():
        try:
            await betik.basla()
        except Exception as e:
            print(f"[HATA] {ad}: {e}")

if __name__ == "__main__":
    try:
        run(basla())
        cikis_yap(False)
    except Exception as hata:
        hata_yakala(hata)
