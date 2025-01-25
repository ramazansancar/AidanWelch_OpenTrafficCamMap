# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from Kekik.cli import cikis_yap, hata_yakala
from asyncio   import run
from Turkey    import alanya, balikesir, caycuma, erzurum, giresun, konya, marmaris, rize, trabzon

async def basla():
    await alanya.basla()
    await balikesir.basla()
    await caycuma.basla()
    await erzurum.basla()
    await giresun.basla()
    await konya.basla()
    await marmaris.basla()
    await rize.basla()
    await trabzon.basla()

if __name__ == "__main__":
    try:
        run(basla())
        cikis_yap(False)
    except Exception as hata:
        hata_yakala(hata)