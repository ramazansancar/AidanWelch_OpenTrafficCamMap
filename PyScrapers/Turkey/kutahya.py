# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from Kekik.cli import konsol
from httpx     import AsyncClient, Timeout
from parsel    import Selector
from re        import search
from json      import load, dumps
from helpers   import str2latlng

class Kutahya:
    def __init__(self):
        self.belediye_url    = "https://kutahya.bel.tr"
        self.kamera_base_url = "https://kamera.kutahya.bel.tr"
        self.kameralar_url   = "https://kutahya.bel.tr/kamera.asp"
        self.oturum          = AsyncClient(
            timeout=Timeout(10, connect=10, read=5*60, write=10),
            verify=False
        )

    async def kameralar(self) -> dict[str, str]:
        """Ana sayfadan kamera listesini al"""
        try:
            istek  = await self.oturum.get(self.kameralar_url)
            secici = Selector(istek.text)
            kameralar = {}
            
            # Sidebar'daki kamera linklerini al
            sidebar_links = secici.css('#sidebar a[href*="kamera.asp?islem=goster&id="]')
            
            for link in sidebar_links:
                href = link.css('::attr(href)').get()
                kamera_adi = link.css('::text').get()
                
                if href and kamera_adi:
                    # ID'yi extract et
                    id_match = search(r'id=(\d+)', href)
                    if id_match:
                        full_url = self.belediye_url + '/' + href if not href.startswith('http') else href
                        kameralar[kamera_adi.strip()] = full_url

            return kameralar
        except Exception as e:
            konsol.log(f"[red][Kutahya] Kameralar alınamadı: {str(e)}")
            return {}

    async def kamera_detay(self, kamera_url: str) -> dict | None:
        """Kamera detay sayfasından stream URL'sini al"""
        try:
            istek  = await self.oturum.get(kamera_url)
            secici = Selector(istek.text)

            # mistPlay fonksiyonundan stream adını al
            script_content = secici.css('script::text').getall()
            stream_name = None
            
            for script in script_content:
                if 'mistPlay(' in script:
                    # mistPlay("laleli_kavsak", {target: ...}) formatından stream adını al
                    match = search(r'mistPlay\("([^"]+)"', script)
                    if match:
                        stream_name = match.group(1)
                        break
            
            if not stream_name:
                return None

            # HLS URL'sini oluştur
            hls_url = f"{self.kamera_base_url}/hls/{stream_name}/index.m3u8"
            
            return {
                "stream_name": stream_name,
                "hls_url": hls_url
            }
        except Exception as e:
            konsol.log(f"[red][Kutahya] Kamera detayı alınamadı: {str(e)}")
            return None

    async def getir(self) -> dict[list[dict]]:
        """Kamera verilerini topla ve işle"""
        kameralar = await self.kameralar()
        
        if not kameralar:
            konsol.log("[red][Kutahya] Kamera listesi alınamadı")
            return {"Belediye": []}

        veri = {"Belediye": []}
        for kamera_adi, kamera_url in kameralar.items():
            try:
                kamera_detay = await self.kamera_detay(kamera_url)
                if not kamera_detay:
                    continue

                # Konum bilgisini kamera adı ve stream adından çıkar
                # Stream adı daha spesifik konum bilgisi içerebilir
                stream_name = kamera_detay["stream_name"]
                
                # Stream adından konum ipuçları çıkar (underscore'ları boşlukla değiştir)
                stream_location = stream_name.replace('_', ' ').replace('-', ' ').replace('  ', ' ')
                
                # Hem kamera adı hem stream adını kullanarak daha isabetli konum ara
                search_queries = [
                    f"{kamera_adi}, {stream_location}, Kütahya, Türkiye",
                    f"{kamera_adi}, Kütahya, Türkiye",
                    f"{stream_location}, Kütahya, Türkiye",
                ]
                
                latitude, longitude = None, None
                for query in search_queries:
                    try:
                        latitude, longitude = await str2latlng(query)
                        if latitude and longitude:
                            break
                    except Exception as geo_error:
                        continue
                
                if not latitude or not longitude:
                    latitude, longitude = 0, 0

                veri["Belediye"].append({
                    "description" : kamera_adi,
                    "latitude"    : latitude,
                    "longitude"   : longitude,
                    "url"         : kamera_detay["hls_url"],
                    "encoding"    : "H.264",
                    "format"      : "M3U8"
                })
            except Exception as e:
                konsol.log(f"[red][Kutahya] {kamera_adi} kamerası işlenirken hata: {str(e)}")
                continue

        return veri

async def basla():
    belediye      = Kutahya()
    gelen_veriler = await belediye.getir()

    konsol.print(gelen_veriler)
    konsol.log(f"[yellow][Kutahya] [+] {len(gelen_veriler['Belediye'])} Adet Kamera Bulundu")

    turkey_json = "../cameras/Turkey.json"

    with open(turkey_json, "r", encoding="utf-8") as dosya:
        mevcut_veriler = load(dosya)

    if gelen_veriler == mevcut_veriler.get("Kutahya"):
        konsol.log("[red][!] [Kutahya] Yeni Veri Yok")
        return

    if mevcut_veriler.get("Kutahya"):
        del mevcut_veriler["Kutahya"]
    mevcut_veriler["Kutahya"] = {"Belediye": gelen_veriler["Belediye"]}

    with open(turkey_json, "w", encoding="utf-8") as dosya:
        dosya.write(dumps(mevcut_veriler, sort_keys=True, ensure_ascii=False, indent=2))

    konsol.log(f"[green][Kutahya] [+] {len(gelen_veriler['Belediye'])} Adet Kamera Eklendi")