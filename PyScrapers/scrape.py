# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from asyncio   import run
from traceback import print_exc
from helpers   import konsol
from Turkey    import alanya, balikesir, bandirma, caycuma, cayirova, denizli, derebucak, erzurum, giresun, golyayla, istanbul, kahramanmaras, karacabey, konya, kutahya, marmaris, nevsehir, rize, salda, samsun, sindirgi, trabzon, uchisar, youtube, zara

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
    "Gölyayla"      : golyayla,
    "İstanbul"      : istanbul,
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
    "Salda Gölü"    : salda,
    "Uçhisar"       : uchisar,
    "Zara"          : zara,
    "YouTube"       : youtube,
}

async def basla():
    # Her şehir ayrı: biri hata verirse diğerleri çalışmaya devam eder
    for ad, betik in BETIKLER.items():
        try:
            await betik.basla()
        except Exception as e:
            konsol.log(f"[red][HATA] {ad}: {e}")

if __name__ == "__main__":
    try:
        run(basla())
    except KeyboardInterrupt:
        konsol.log("[bold purple]Çıkış Yapıldı..")
    except Exception:
        print_exc()
        raise SystemExit(1)
