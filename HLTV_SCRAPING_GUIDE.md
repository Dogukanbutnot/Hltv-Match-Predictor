# 🌐 HLTV'DEN GERÇEK VERİ ÇEKME REHBERİ

## 📋 İÇİNDEKİLER
1. [Gereksinimler](#gereksinimler)
2. [Kurulum](#kurulum)
3. [Temel Kullanım](#temel-kullanım)
4. [Gelişmiş Özellikler](#gelişmiş-özellikler)
5. [Sorun Giderme](#sorun-giderme)
6. [Etik ve Yasal](#etik-ve-yasal)

---

## 🔧 GEREKSİNİMLER

### Yazılım Gereksinimleri

1. **Python 3.8+**
   ```bash
   python --version
   # Python 3.8 veya üzeri
   ```

2. **Chrome veya Chromium**
   ```bash
   # Chrome yüklü mü kontrol et
   google-chrome --version  # Linux
   # veya
   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --version  # Mac
   ```

3. **Python Paketleri**
   ```bash
   pip install selenium webdriver-manager pandas
   ```

### İnternet Bağlantısı
- ✅ Stabil internet bağlantısı gerekli
- ✅ HLTV.org'a erişim gerekli
- ⚠️  VPN kullanıyorsanız, bazı ülkelerden erişim kısıtlı olabilir

---

## 💻 KURULUM

### Adım 1: Paketleri Yükle

```bash
pip install selenium==4.15.2
pip install webdriver-manager==4.0.1
pip install pandas==2.1.3
```

### Adım 2: Chrome Yükle (Eğer yoksa)

**Ubuntu/Debian:**
```bash
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt-get install -f
```

**Mac:**
```bash
brew install --cask google-chrome
```

**Windows:**
- https://www.google.com/chrome/ adresinden indirin

### Adım 3: Scraper'ı Test Et

```bash
python real_hltv_scraper.py
```

---

## 🚀 TEMEL KULLANIM

### Basit Scraping

```python
from real_hltv_scraper import RealHLTVScraper

# Scraper oluştur
scraper = RealHLTVScraper(headless=True)

# Driver başlat
scraper.setup_driver()

try:
    # Geçmiş maçları çek (3 sayfa = ~150 maç)
    results = scraper.scrape_results(num_pages=3)
    results.to_csv('results.csv', index=False)
    
    # Gelecek maçları çek
    upcoming = scraper.scrape_upcoming_matches()
    upcoming.to_csv('upcoming.csv', index=False)
    
finally:
    scraper.close()
```

### Komut Satırından

```bash
# Basit kullanım
python real_hltv_scraper.py

# Tarayıcıyı görerek (debugging)
# Script içinde headless=False yapın
```

---

## 🔥 GELİŞMİŞ ÖZELLİKLER

### 1. Daha Fazla Sayfa Çekme

```python
# 10 sayfa = ~500 maç
results = scraper.scrape_results(num_pages=10)
```

⚠️  **Dikkat**: Çok fazla sayfa çekerken:
- Rate limiting olabilir
- IP ban riski artar
- İşlem süresi uzar (sayfa başı ~5 saniye)

### 2. Maç Detaylarını Çekme

```python
# Belirli bir maçın detayını çek
match_url = "https://www.hltv.org/matches/2369161/liquid-vs-nip-iem-katowice-2026"
details = scraper.scrape_match_details(match_url)

print(details['maps'])  # Harita bazlı sonuçlar
```

### 3. Otomatik Günlük Scraping

**daily_scraper.py** oluşturun:

```python
"""
Günlük otomatik HLTV scraper
Her gün belirlenen saatte çalışır
"""

import schedule
import time
from real_hltv_scraper import RealHLTVScraper
from datetime import datetime

def daily_scrape():
    """Günlük scraping fonksiyonu"""
    print(f"\n🕐 {datetime.now()} - Günlük scraping başlıyor...\n")
    
    scraper = RealHLTVScraper(headless=True)
    
    try:
        scraper.setup_driver()
        
        # Geçmiş maçları güncelle (son 1 sayfa = son 50 maç)
        results = scraper.scrape_results(num_pages=1)
        
        # Mevcut veriyle birleştir
        try:
            existing = pd.read_csv('hltv_match_results.csv')
            combined = pd.concat([existing, results]).drop_duplicates(
                subset=['team_1', 'team_2', 'match_date'], 
                keep='last'
            )
            combined.to_csv('hltv_match_results.csv', index=False)
        except:
            results.to_csv('hltv_match_results.csv', index=False)
        
        # Gelecek maçları güncelle
        upcoming = scraper.scrape_upcoming_matches()
        upcoming.to_csv('hltv_upcoming_matches.csv', index=False)
        
        print(f"✅ Günlük scraping tamamlandı!")
        
    finally:
        scraper.close()

# Her gün 09:00'da çalıştır
schedule.every().day.at("09:00").do(daily_scrape)

print("⏰ Günlük scraper başlatıldı (09:00)")
print("   Durdurmak için: Ctrl+C")

while True:
    schedule.run_pending()
    time.sleep(60)
```

Çalıştır:
```bash
python daily_scraper.py
```

### 4. Proxy Kullanımı (IP Ban Önleme)

```python
from selenium.webdriver.common.proxy import Proxy, ProxyType

def setup_driver_with_proxy(self, proxy_address):
    """Proxy ile driver başlat"""
    chrome_options = Options()
    
    # Proxy ayarla
    chrome_options.add_argument(f'--proxy-server={proxy_address}')
    
    # ... diğer ayarlar ...
    
    self.driver = webdriver.Chrome(service=service, options=chrome_options)

# Kullanım
scraper = RealHLTVScraper()
scraper.setup_driver_with_proxy('http://proxy-server:port')
```

### 5. Hata Toleransı ve Yeniden Deneme

```python
def scrape_with_retry(self, max_retries=3):
    """Hata durumunda yeniden dene"""
    for attempt in range(max_retries):
        try:
            results = self.scrape_results()
            return results
        except Exception as e:
            logger.warning(f"Deneme {attempt + 1}/{max_retries} başarısız: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)  # 5 saniye bekle
            else:
                raise
```

---

## 🐛 SORUN GİDERME

### Hata 1: "ChromeDriver executable not found"

**Çözüm:**
```bash
# Otomatik çözüm (webdriver-manager kullanıyor)
pip install webdriver-manager --upgrade

# Manuel çözüm
# ChromeDriver'ı indirin: https://chromedriver.chromium.org/
# PATH'e ekleyin veya kodda belirtin
```

### Hata 2: "Element not found" / "NoSuchElementException"

**Sebep:** HLTV HTML yapısı değişmiş olabilir

**Çözüm:**
```python
# 1. Tarayıcıyı görünür modda açın
scraper = RealHLTVScraper(headless=False)

# 2. Sayfayı inspect edin
# 3. CSS selector'ları güncelleyin

# Örnek: Eski selector çalışmıyorsa
# Eski: ".result-con"
# Yeni: ".results-holder .result-con"
```

**Güncel selector'ları bulma:**
```python
# Chrome DevTools (F12) kullanın
# 1. Element'i seçin
# 2. Sağ tık → Copy → Copy selector
# 3. Kodda değiştirin
```

### Hata 3: "TimeoutException"

**Çözüm:**
```python
# Bekleme süresini artırın
wait = WebDriverWait(self.driver, 20)  # 10'dan 20'ye

# Veya daha fazla bekleyin
time.sleep(5)  # 3'ten 5'e
```

### Hata 4: "403 Forbidden" / "Cloudflare"

**Sebep:** HLTV bot algılıyor

**Çözüm:**
```python
# 1. User agent güncelle
chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

# 2. Daha yavaş scrape et
time.sleep(random.randint(3, 7))  # Rastgele bekleme

# 3. Cookies kabul et
try:
    cookie_button = driver.find_element(By.ID, "cookie-accept")
    cookie_button.click()
except:
    pass
```

### Hata 5: Çok Yavaş Çalışıyor

**Optimizasyon:**
```python
# 1. Sadece gerekli sayfaları yükle
chrome_options.add_argument("--blink-settings=imagesEnabled=false")  # Resimleri devre dışı bırak

# 2. CSS/JS yüklemesini engelle
prefs = {"profile.managed_default_content_settings.images": 2}
chrome_options.add_experimental_option("prefs", prefs)

# 3. Paralel scraping (dikkatli kullanın!)
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(scrape_page, page_numbers))
```

---

## ⚖️ ETİK VE YASAL

### ✅ İZİN VERİLEN KULLANIM

- 📚 **Araştırma amaçlı**: Akademik veya kişisel projeler
- 📊 **Analiz**: Takım performans analizi
- 🎓 **Eğitim**: Öğrenme ve pratik yapma

### ❌ İZİN VERİLMEYEN KULLANIM

- 🚫 **Ticari kullanım** olmadan izin
- 🚫 **Aşırı yük** oluşturma (DDoS benzeri)
- 🚫 **Veri satışı**
- 🚫 **HLTV'ye rakip site** oluşturma

### 📜 robots.txt Kontrolü

```bash
# HLTV'nin robots.txt'ini kontrol edin
curl https://www.hltv.org/robots.txt
```

**robots.txt içeriğine uyun!**

### 🤝 İyi Pratikler

1. **Rate Limiting**: Sayfa başı en az 2-3 saniye bekle
   ```python
   time.sleep(random.uniform(2, 5))
   ```

2. **Makul Kullanım**: Günde en fazla 500-1000 maç çek

3. **Hata Durumunda Dur**: Sürekli hata alıyorsanız çekmekten vazgeçin

4. **Verileri Önbellekle**: Aynı veriyi tekrar çekmeyin
   ```python
   # CSV'ye kaydet, sonra oradan oku
   if os.path.exists('cache.csv'):
       df = pd.read_csv('cache.csv')
   ```

5. **User-Agent Bildir**: Kimliğinizi belli edin
   ```python
   headers = {
       'User-Agent': 'Your-Bot-Name/1.0 (your-email@example.com)'
   }
   ```

---

## 📊 VERİ KALİTESİ

### Kontrol Listesi

```python
def validate_data(df):
    """Çekilen veriyi doğrula"""
    
    # 1. Boş değerler
    print("Boş değerler:")
    print(df.isnull().sum())
    
    # 2. Duplikatlar
    duplicates = df.duplicated().sum()
    print(f"\nDuplikat satırlar: {duplicates}")
    
    # 3. Geçersiz skorlar
    invalid_scores = df[(df['score_1'] < 0) | (df['score_2'] < 0)]
    print(f"Geçersiz skorlar: {len(invalid_scores)}")
    
    # 4. Tarih aralığı
    df['match_date'] = pd.to_datetime(df['match_date'])
    print(f"\nTarih aralığı: {df['match_date'].min()} - {df['match_date'].max()}")
    
    return df

# Kullanım
results = scraper.scrape_results()
results = validate_data(results)
```

---

## 🔄 GÜNCELLEME STRATEJİSİ

### Strateji 1: Tam Güncelleme (Haftalık)

```bash
# Tüm veriyi yeniden çek
python real_hltv_scraper.py --full
```

### Strateji 2: Artımlı Güncelleme (Günlük)

```python
# Sadece son 1 günün maçlarını çek
# Mevcut veriyle birleştir
```

### Strateji 3: Hibrit (Önerilen)

```
- Her gün: Son 1 sayfa (~50 maç)
- Her hafta: Son 5 sayfa (~250 maç) 
- Her ay: Tüm veri (~1000+ maç)
```

---

## 💡 İPUÇLARI

1. **İlk defa çalıştırırken**:
   ```bash
   # Headless=False ile test edin
   # Tarayıcıyı görerek ne olduğunu anlayın
   ```

2. **Selector bulamıyorsanız**:
   - HLTV HTML'i değişmiş olabilir
   - Chrome DevTools ile yeni selector'ları bulun
   - XPath kullanmayı deneyin

3. **Veri çok büyükse**:
   ```python
   # Chunking kullanın
   for chunk in pd.read_csv('big_file.csv', chunksize=1000):
       process(chunk)
   ```

4. **Scraping engellenirse**:
   - VPN kullanın
   - Proxy servis kullanın (örn: ScraperAPI, Bright Data)
   - Headless browser yerine gerçek browser kullanın

---

## 📞 YARDIM

Sorun yaşıyorsanız:

1. **Log'ları kontrol edin**:
   ```bash
   python real_hltv_scraper.py 2>&1 | tee scraper.log
   ```

2. **Verbose mode açın**:
   ```python
   logging.basicConfig(level=logging.DEBUG)
   ```

3. **Screenshot alın**:
   ```python
   driver.save_screenshot('error.png')
   ```

---

## ✅ ÖZET: HIZLI BAŞLANGIÇ

```bash
# 1. Kurulum
pip install selenium webdriver-manager pandas

# 2. Scraper'ı çalıştır
python real_hltv_scraper.py

# 3. Verileri kontrol et
ls -lh hltv_*.csv

# 4. Modelleri eğit
python precise_predictor.py

# 5. Başarı! 🎉
```

---

**Not**: Bu rehber HLTV.org'un mevcut (2026) yapısına göre hazırlanmıştır. Site yapısı değişirse scraper güncellenmesi gerekebilir.
