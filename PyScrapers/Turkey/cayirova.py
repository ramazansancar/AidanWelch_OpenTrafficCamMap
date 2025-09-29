# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.

from Kekik.cli import konsol
from httpx     import AsyncClient, Timeout
from parsel    import Selector
from re        import search, DOTALL
from json      import load, dumps
from helpers   import str2latlng

class Cayirova:
    def __init__(self):
        self.belediye_url = "https://kamera.cayirova.bel.tr"
        self.oturum       = AsyncClient(
            timeout=Timeout(10, connect=10, read=5*60, write=10),
            verify=False,
            follow_redirects=True
        )

    async def kameralar(self) -> list[dict]:
        try:
            istek  = await self.oturum.get(self.belediye_url)
            secici = Selector(istek.text)

            # JavaScript kodundan locations array'ini çıkar
            js_code = secici.css('script:contains("var locations")::text').get()
            if not js_code:
                return []

            # locations array'ini parse et
            locations_match = search(r'var locations = \[(.*?)\];', js_code, DOTALL)
            if not locations_match:
                return []

            kameralar = []
            location_lines = locations_match.group(1).split('\n')
            
            for line in location_lines:
                line = line.strip()
                if line.startswith('[locationData('):
                    # locationData parametrelerini çıkar - regex'i düzelt
                    params_match = search(r"\[locationData\('([^']*)', '[^']*', '([^']*)', \"([^\"]*)\", '[^']*', \"(\d+)\"", line)
                    if params_match:
                        url_part = params_match.group(1)
                        name = params_match.group(2)
                        location = params_match.group(3)
                        camera_count = int(params_match.group(4))
                        
                        # Koordinatları çıkar
                        coords_match = search(r'\), ([\d.]+), ([\d.]+), \d+ ,', line)
                        if coords_match:
                            latitude = float(coords_match.group(1))
                            longitude = float(coords_match.group(2))
                            
                            if ';' in url_part:
                                # Birden fazla kamera var
                                urls = url_part.split(';')
                                for i, url in enumerate(urls):
                                    kameralar.append({
                                        'name': f"{name} - {i+1}",
                                        'location': location,
                                        'url': url,
                                        'latitude': latitude,
                                        'longitude': longitude + (i * 0.0001)  # Aynı konumda olan kameralar için küçük offset
                                    })
                            else:
                                # Tek kamera
                                kameralar.append({
                                    'name': name,
                                    'location': location,
                                    'url': url_part,
                                    'latitude': latitude,
                                    'longitude': longitude
                                })

            return kameralar
        except Exception as e:
            konsol.log(f"[red][Kocaeli][Çayırova] Kameralar alınamadı: {str(e)}")
            return []

    async def get_stream_url(self, kamera_url: str) -> str | None:
        try:
            # URL'ye git (HTTP client otomatik olarak redirect'leri takip eder)
            istek = await self.oturum.get(kamera_url)
            secici = Selector(istek.text)
            
            # JavaScript kodundan source URL'sini çıkar
            js_code = secici.css('script:contains("source:")::text').get()
            if js_code:
                source_match = search(r"source:\s*'([^']*)'", js_code)
                if source_match:
                    return source_match.group(1)
            
            return None
        except Exception as e:
            konsol.log(f"[red][Kocaeli][Çayırova] Stream URL alınamadı: {str(e)}")
            return None

    async def getir(self) -> dict[list[dict]]:
        kameralar = await self.kameralar()
        
        if not kameralar:
            konsol.log("[red][Kocaeli][Çayırova] Kamera listesi alınamadı")
            return {"Cayirova": []}

        veri = {"Cayirova": []}
        for kamera in kameralar:
            try:
                stream_url = await self.get_stream_url(kamera['url'])
                if not stream_url:
                    konsol.log(f"[yellow][Kocaeli][Çayırova] {kamera['name']} için stream URL bulunamadı")
                    continue

                # URL'den kamera parametresini çıkar ve sadece ID'yi al
                url_param = ""
                if '?name=' in kamera['url']:
                    url_param = f" ({kamera['url'].split('?name=')[1]})"
                elif '?stream=' in kamera['url']:
                    url_param = f" ({kamera['url'].split('?stream=')[1]})"

                veri["Cayirova"].append({
                    "description" : kamera['name'] + url_param,
                    "latitude"    : kamera['latitude'],
                    "longitude"   : kamera['longitude'],
                    "url"         : stream_url,
                    "encoding"    : "H.264",
                    "format"      : "M3U8"
                })
            except Exception as e:
                konsol.log(f"[red][Kocaeli][Çayırova] {kamera['name']} kamerası işlenirken hata: {str(e)}")
                continue

        return veri

async def basla():
    belediye      = Cayirova()
    gelen_veriler = await belediye.getir()

    konsol.print(gelen_veriler)
    konsol.log(f"[yellow][Kocaeli][Çayırova] [+] {len(gelen_veriler['Cayirova'])} Adet Kamera Bulundu")

    turkey_json = "../cameras/Turkey.json"

    with open(turkey_json, "r", encoding="utf-8") as dosya:
        mevcut_veriler = load(dosya)

    if gelen_veriler["Cayirova"] == mevcut_veriler.get("Kocaeli", {}).get("Cayirova"):
        konsol.log("[red][Kocaeli][Çayırova] [!] Yeni Veri Yok")
        return

    # Kocaeli anahtarı yoksa oluştur
    if "Kocaeli" not in mevcut_veriler:
        mevcut_veriler["Kocaeli"] = {}
    
    # Çayırova verilerini doğrudan ekle/güncelle (iç içe yapı değil)
    mevcut_veriler["Kocaeli"]["Cayirova"] = gelen_veriler["Cayirova"]

    with open(turkey_json, "w", encoding="utf-8") as dosya:
        dosya.write(dumps(mevcut_veriler, sort_keys=True, ensure_ascii=False, indent=2))

    konsol.log(f"[green][Kocaeli][Çayırova] [+] {len(gelen_veriler['Cayirova'])} Adet Kamera Eklendi")
