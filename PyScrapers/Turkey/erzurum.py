# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from Kekik.cli import konsol
from httpx     import AsyncClient, Timeout
from json      import load, dumps
from helpers   import str2latlng
from bs4       import BeautifulSoup
import re

class Erzurum:
    def __init__(self):
        self.oturum = AsyncClient(timeout=Timeout(10, connect=10, read=5*60, write=10))

    async def kameralar(self) -> dict[str, str]:
        """Erzurum Belediye kameralarını getir"""
        istek = await self.oturum.get("https://wowza.yayin.com.tr/playlist/erzurumbeltr/playlist_erzurumbeltr.json")
        return istek.json()

    async def ejder_kameralar(self) -> dict[str, str]:
        """Ejder 3200 kameralarını getir"""
        istek = await self.oturum.get("https://wowza.yayin.com.tr/playlist/ejder3200/playlist_ejder3200.json")
        return istek.json()

    async def web_kameralar(self) -> list[dict]:
        """Belediye web sitesinden kameraları çek"""
        istek = await self.oturum.get("https://ebb.erzurum.bel.tr/canliyayin.aspx")
        soup = BeautifulSoup(istek.text, 'html.parser')
        
        kameralar = []
        
        # Tüm kamera linklerini bul
        for li in soup.find_all('li', id=re.compile(r'^kamera\d+')):
            try:
                # JavaScript linkini bul
                link_tag = li.find('a', href=re.compile(r"javascript:liste1\("))
                if link_tag:
                    href = link_tag.get('href', '')
                    # M3U8 URL'ini çıkar
                    m3u8_match = re.search(r"'([^']*\.m3u8)'", href)
                    if m3u8_match:
                        m3u8_url = m3u8_match.group(1)
                        if not m3u8_url.startswith('http'):
                            m3u8_url = "https:" + m3u8_url
                        
                        # Kamera adını bul
                        title_span = li.find('span', class_='videoBaslik')
                        if title_span:
                            title = title_span.get_text(strip=True)
                            
                            # Özel durumlar için ekstra bilgi ekle
                            kamera_id = li.get('id', '')
                            if kamera_id == 'kamera6004':
                                title += " (Mezarlik)"
                            
                            kameralar.append({
                                'title': title,
                                'url': m3u8_url,
                                'id': kamera_id
                            })
            except Exception as e:
                konsol.log(f"[red][Erzurum] Kamera parse hatası: {e}")
                continue
        
        return kameralar

    async def getir(self) -> dict[list[dict]]:
        # Belediye kameralarını getir
        belediye_kameralar = await self.kameralar()
        
        # Ejder kameralarını getir
        ejder_kameralar = await self.ejder_kameralar()
        
        # Web sitesinden kameraları getir
        web_kameralar = await self.web_kameralar()

        veri = {"Belediye": [], "Ejder": [], "Web": []}
        
        # Belediye kameralarını işle
        for kamera_veri in belediye_kameralar.get("playlist", []):
            latitude, longitude = await str2latlng(f"{kamera_veri['title']}, Erzurum, Türkiye")

            veri["Belediye"].append({
                "description" : kamera_veri["title"],
                "latitude"    : latitude,
                "longitude"   : longitude,
                "url"         : "https:" + kamera_veri["sources"][0]["file"],
                "encoding"    : "H.264",
                "format"      : "M3U8"
            })
        
        # Ejder kameralarını işle
        for kamera_veri in ejder_kameralar.get("playlist", []):
            latitude, longitude = await str2latlng(f"{kamera_veri['title']}, Palandöken, Erzurum, Türkiye")

            veri["Ejder"].append({
                "description" : kamera_veri["title"],
                "latitude"    : latitude,
                "longitude"   : longitude,
                "url"         : "https:" + kamera_veri["sources"][0]["file"],
                "encoding"    : "H.264",
                "format"      : "M3U8"
            })
        
        # Web kameralarını işle
        for kamera_veri in web_kameralar:
            # URL filtreleme - sadece benzersiz olanları al
            existing_urls = []
            for category in veri.values():
                existing_urls.extend([cam["url"] for cam in category])
            
            if kamera_veri["url"] not in existing_urls:
                latitude, longitude = await str2latlng(f"{kamera_veri['title']}, Erzurum, Türkiye")

                veri["Web"].append({
                    "description" : kamera_veri["title"],
                    "latitude"    : latitude,
                    "longitude"   : longitude,
                    "url"         : kamera_veri["url"],
                    "encoding"    : "H.264",
                    "format"      : "M3U8"
                })

        return veri

async def basla():
    belediye      = Erzurum()
    gelen_veriler = await belediye.getir()

    # Toplam kamera sayısını hesapla
    toplam_kamera = sum(len(kategori) for kategori in gelen_veriler.values())
    
    konsol.print(gelen_veriler)
    konsol.log(f"[yellow][Erzurum] [+] {toplam_kamera} Adet Kamera Bulundu")
    konsol.log(f"[cyan][Erzurum] Belediye: {len(gelen_veriler.get('Belediye', []))}, Ejder: {len(gelen_veriler.get('Ejder', []))}, Web: {len(gelen_veriler.get('Web', []))}")

    turkey_json = "../cameras/Turkey.json"

    with open(turkey_json, "r", encoding="utf-8") as dosya:
        mevcut_veriler = load(dosya)

    if gelen_veriler == mevcut_veriler.get("Erzurum"):
        konsol.log("[red][Erzurum] [!] Yeni Veri Yok")
        return

    if mevcut_veriler.get("Erzurum"):
        del mevcut_veriler["Erzurum"]
    mevcut_veriler["Erzurum"] = gelen_veriler

    with open(turkey_json, "w", encoding="utf-8") as dosya:
        dosya.write(dumps(mevcut_veriler, sort_keys=True, ensure_ascii=False, indent=2))

    konsol.log(f"[green][Erzurum] [+] {toplam_kamera} Adet Kamera Eklendi")