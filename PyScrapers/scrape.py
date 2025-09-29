# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from Kekik.cli import cikis_yap, hata_yakala
from asyncio   import run
from Turkey    import alanya, balikesir, caycuma, cayirova, denizli, erzurum, giresun, kahramanmaras, karacabey, konya, kutahya, marmaris, rize, sindirgi, trabzon

async def basla():
    # Her şehir için ayrı try-catch blokları
    try:
        await alanya.basla()
    except Exception as e:
        print(f"[HATA] Alanya: {e}")
    
    try:
        await balikesir.basla()
    except Exception as e:
        print(f"[HATA] Balıkesir: {e}")
    
    try:
        await caycuma.basla()
    except Exception as e:
        print(f"[HATA] Caycuma: {e}")
    
    try:
        await cayirova.basla()
    except Exception as e:
        print(f"[HATA] Çayırova: {e}")
    
    try:
        await denizli.basla()
    except Exception as e:
        print(f"[HATA] Denizli: {e}")
    
    try:
        await erzurum.basla()
    except Exception as e:
        print(f"[HATA] Erzurum: {e}")
    
    try:
        await giresun.basla()
    except Exception as e:
        print(f"[HATA] Giresun: {e}")
    
    try:
        await konya.basla()
    except Exception as e:
        print(f"[HATA] Konya: {e}")
    
    try:
        await marmaris.basla()
    except Exception as e:
        print(f"[HATA] Marmaris: {e}")
    
    try:
        await karacabey.basla()
    except Exception as e:
        print(f"[HATA] Karacabey: {e}")
    
    try:
        await kutahya.basla()
    except Exception as e:
        print(f"[HATA] Kutahya: {e}")
    
    try:
        await rize.basla()
    except Exception as e:
        print(f"[HATA] Rize: {e}")
    
    try:
        await sindirgi.basla()
    except Exception as e:
        print(f"[HATA] Sindirgi: {e}")
    
    try:
        await trabzon.basla()
    except Exception as e:
        print(f"[HATA] Trabzon: {e}")
    
    try:
        await kahramanmaras.basla()
    except Exception as e:
        print(f"[HATA] Kahramanmaras: {e}")

if __name__ == "__main__":
    try:
        run(basla())
        cikis_yap(False)
    except Exception as hata:
        hata_yakala(hata)