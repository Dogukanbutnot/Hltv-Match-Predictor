"""
GERÇEK HLTV Web Scraper
HLTV.org'dan canlı maç verisi çeker
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
from datetime import datetime
import logging
import re

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RealHLTVScraper:
    """HLTV.org'dan gerçek veri çeker"""
    
    def __init__(self, headless=True):
        """
        Args:
            headless: Tarayıcıyı görünmez modda çalıştır (True/False)
        """
        self.driver = None
        self.headless = headless
        self.base_url = "https://www.hltv.org"
        
    def setup_driver(self):
        """Chrome driver'ı başlat"""
        logger.info("🔧 Chrome driver başlatılıyor...")
        
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
        
        # Anti-bot önlemleri
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Reklam engelleyici (opsiyonel)
        chrome_options.add_argument("--disable-popup-blocking")
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("✅ Chrome driver başlatıldı")
            return True
        except Exception as e:
            logger.error(f"❌ Chrome driver hatası: {e}")
            return False
    
    def close(self):
        """Driver'ı kapat"""
        if self.driver:
            self.driver.quit()
            logger.info("🔒 Browser kapatıldı")
    
    def scrape_results(self, num_pages=5):
        """
        Geçmiş maç sonuçlarını çek
        
        Args:
            num_pages: Kaç sayfa çekilecek (her sayfa ~50 maç)
        
        Returns:
            pandas.DataFrame: Maç sonuçları
        """
        logger.info(f"📊 Geçmiş maçlar çekiliyor (Son {num_pages} sayfa)...")
        
        results_url = f"{self.base_url}/results"
        self.driver.get(results_url)
        
        # Sayfanın yüklenmesini bekle
        time.sleep(3)
        
        all_matches = []
        
        for page in range(num_pages):
            logger.info(f"   Sayfa {page + 1}/{num_pages} işleniyor...")
            
            try:
                # Maç elementlerini bul
                # HLTV'nin HTML yapısına göre selector'lar
                matches = self.driver.find_elements(By.CSS_SELECTOR, ".results-holder > .results-all > .result-con")
                
                for match_element in matches:
                    try:
                        match_data = self._parse_result_element(match_element)
                        if match_data:
                            all_matches.append(match_data)
                    except Exception as e:
                        logger.debug(f"Maç parse hatası: {e}")
                        continue
                
                # Sonraki sayfaya git
                if page < num_pages - 1:
                    try:
                        # "Load more" butonunu bul ve tıkla
                        load_more = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, ".load-more-button"))
                        )
                        load_more.click()
                        time.sleep(2)
                    except:
                        logger.warning("Load more butonu bulunamadı, sonraki sayfa yok")
                        break
                        
            except Exception as e:
                logger.error(f"Sayfa {page + 1} hatası: {e}")
                continue
        
        logger.info(f"✅ Toplam {len(all_matches)} maç çekildi")
        
        return pd.DataFrame(all_matches)
    
    def _parse_result_element(self, element):
        """Tek bir maç elementini parse et"""
        try:
            # Maç linkini al (detay sayfası için)
            match_link = element.find_element(By.CSS_SELECTOR, "a.a-reset").get_attribute("href")
            
            # Takım isimleri
            teams = element.find_elements(By.CSS_SELECTOR, ".team")
            if len(teams) < 2:
                return None
            
            team1 = teams[0].text.strip()
            team2 = teams[1].text.strip()
            
            # Skor
            score_element = element.find_element(By.CSS_SELECTOR, ".result-score")
            score_text = score_element.text.strip()
            
            # Skoru parse et (örn: "16 - 14" veya "2 - 1")
            score_parts = re.findall(r'\d+', score_text)
            if len(score_parts) >= 2:
                score1 = int(score_parts[0])
                score2 = int(score_parts[1])
            else:
                return None
            
            # Event
            try:
                event = element.find_element(By.CSS_SELECTOR, ".event-name").text.strip()
            except:
                event = "Unknown"
            
            # Tarih
            try:
                date_element = element.find_element(By.CSS_SELECTOR, ".date")
                date_text = date_element.text.strip()
                # Tarihi parse et (HLTV formatına göre)
                match_date = self._parse_date(date_text)
            except:
                match_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Harita (eğer BO1 ise)
            map_name = "Unknown"
            try:
                # Detay sayfasından harita bilgisi alınabilir
                map_element = element.find_element(By.CSS_SELECTOR, ".map-text")
                map_name = map_element.text.strip()
            except:
                pass
            
            # Kazananı belirle
            winner = 1 if score1 > score2 else 2
            
            return {
                'scrape_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'match_date': match_date,
                'team_1': team1,
                'team_2': team2,
                'score_1': score1,
                'score_2': score2,
                'winner': winner,
                'event': event,
                'map': map_name,
                'match_url': match_link
            }
            
        except Exception as e:
            logger.debug(f"Element parse hatası: {e}")
            return None
    
    def _parse_date(self, date_text):
        """HLTV tarih formatını parse et"""
        try:
            # HLTV formatları: "Today", "Yesterday", "16th of January"
            if "Today" in date_text:
                return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            elif "Yesterday" in date_text:
                from datetime import timedelta
                yesterday = datetime.now() - timedelta(days=1)
                return yesterday.strftime('%Y-%m-%d %H:%M:%S')
            else:
                # Diğer formatlar için basit parse
                return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        except:
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def scrape_upcoming_matches(self):
        """
        Gelecek maçları çek
        
        Returns:
            pandas.DataFrame: Gelecek maçlar
        """
        logger.info("📅 Gelecek maçlar çekiliyor...")
        
        matches_url = f"{self.base_url}/matches"
        self.driver.get(matches_url)
        
        # Sayfanın yüklenmesini bekle
        time.sleep(3)
        
        upcoming_matches = []
        
        try:
            # Gelecek maç elementleri
            match_elements = self.driver.find_elements(By.CSS_SELECTOR, ".upcomingMatch")
            
            logger.info(f"   {len(match_elements)} gelecek maç bulundu")
            
            for element in match_elements:
                try:
                    match_data = self._parse_upcoming_element(element)
                    if match_data:
                        upcoming_matches.append(match_data)
                except Exception as e:
                    logger.debug(f"Upcoming maç parse hatası: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Upcoming maçlar hatası: {e}")
        
        logger.info(f"✅ {len(upcoming_matches)} gelecek maç çekildi")
        
        return pd.DataFrame(upcoming_matches)
    
    def _parse_upcoming_element(self, element):
        """Gelecek maç elementini parse et"""
        try:
            # Takım isimleri
            team1_element = element.find_element(By.CSS_SELECTOR, ".team1 .team")
            team2_element = element.find_element(By.CSS_SELECTOR, ".team2 .team")
            
            team1 = team1_element.text.strip()
            team2 = team2_element.text.strip()
            
            if not team1 or not team2:
                return None
            
            # Event
            try:
                event = element.find_element(By.CSS_SELECTOR, ".event-name").text.strip()
            except:
                event = "Unknown"
            
            # Maç zamanı
            try:
                time_element = element.find_element(By.CSS_SELECTOR, ".time")
                match_time = time_element.text.strip()
            except:
                match_time = "TBD"
            
            # Format (BO1, BO3, BO5)
            try:
                format_element = element.find_element(By.CSS_SELECTOR, ".bestof")
                match_format = format_element.text.strip()
            except:
                match_format = "Unknown"
            
            return {
                'scrape_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'team_1': team1,
                'team_2': team2,
                'event': event,
                'match_time': match_time,
                'format': match_format
            }
            
        except Exception as e:
            logger.debug(f"Upcoming element parse hatası: {e}")
            return None
    
    def scrape_match_details(self, match_url):
        """
        Belirli bir maçın detaylarını çek (harita, oyuncu istatistikleri vs.)
        
        Args:
            match_url: Maç detay sayfası URL
        
        Returns:
            dict: Maç detayları
        """
        logger.info(f"🔍 Maç detayı çekiliyor: {match_url}")
        
        self.driver.get(match_url)
        time.sleep(3)
        
        details = {}
        
        try:
            # Harita bilgisi
            maps = self.driver.find_elements(By.CSS_SELECTOR, ".mapholder")
            
            map_results = []
            for map_element in maps:
                try:
                    map_name = map_element.find_element(By.CSS_SELECTOR, ".mapname").text.strip()
                    
                    # Skorlar
                    scores = map_element.find_elements(By.CSS_SELECTOR, ".results-team-score")
                    if len(scores) >= 2:
                        score1 = scores[0].text.strip()
                        score2 = scores[1].text.strip()
                        
                        map_results.append({
                            'map': map_name,
                            'score_1': score1,
                            'score_2': score2
                        })
                except:
                    continue
            
            details['maps'] = map_results
            
        except Exception as e:
            logger.error(f"Maç detay hatası: {e}")
        
        return details


def main():
    """Ana scraping fonksiyonu"""
    print("="*80)
    print("  GERÇEK HLTV WEB SCRAPER")
    print("="*80)
    print()
    print("⚠️  DİKKAT:")
    print("   - Bu scraper HLTV.org'dan gerçek veri çeker")
    print("   - İnternet bağlantısı gereklidir")
    print("   - Chrome/Chromium yüklü olmalıdır")
    print("   - HLTV'nin kullanım şartlarına uygun kullanın")
    print("   - Rate limiting için yavaş çalışır (2-3 saniye bekler)")
    print()
    print("="*80 + "\n")
    
    # Scraper oluştur
    scraper = RealHLTVScraper(headless=True)  # headless=False ise tarayıcıyı görebilirsiniz
    
    try:
        # Driver'ı başlat
        if not scraper.setup_driver():
            print("❌ Chrome driver başlatılamadı")
            return
        
        # 1. Geçmiş maçları çek
        print("\n" + "="*80)
        print("📊 GEÇMİŞ MAÇLAR ÇEKİLİYOR")
        print("="*80 + "\n")
        
        results_df = scraper.scrape_results(num_pages=3)  # 3 sayfa = ~150 maç
        
        if not results_df.empty:
            results_df.to_csv('hltv_match_results.csv', index=False, encoding='utf-8')
            print(f"\n✅ {len(results_df)} maç kaydedildi: hltv_match_results.csv")
            
            # Önizleme
            print("\n📋 İlk 5 maç:")
            print(results_df.head().to_string(index=False))
        else:
            print("\n❌ Maç çekilemedi")
        
        # 2. Gelecek maçları çek
        print("\n" + "="*80)
        print("📅 GELECEK MAÇLAR ÇEKİLİYOR")
        print("="*80 + "\n")
        
        upcoming_df = scraper.scrape_upcoming_matches()
        
        if not upcoming_df.empty:
            upcoming_df.to_csv('hltv_upcoming_matches.csv', index=False, encoding='utf-8')
            print(f"\n✅ {len(upcoming_df)} maç kaydedildi: hltv_upcoming_matches.csv")
            
            # Önizleme
            print("\n📋 İlk 5 gelecek maç:")
            print(upcoming_df.head().to_string(index=False))
        else:
            print("\n❌ Gelecek maç çekilemedi")
        
        # Özet
        print("\n" + "="*80)
        print("✅ SCRAPING TAMAMLANDI")
        print("="*80)
        print(f"\n📂 Oluşturulan Dosyalar:")
        print(f"   ✓ hltv_match_results.csv ({len(results_df)} maç)")
        print(f"   ✓ hltv_upcoming_matches.csv ({len(upcoming_df)} maç)")
        print()
        print("🚀 Sonraki adım:")
        print("   python precise_predictor.py")
        print("="*80 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Kullanıcı tarafından durduruldu")
        
    except Exception as e:
        print(f"\n\n❌ Hata: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Her durumda browser'ı kapat
        scraper.close()


if __name__ == '__main__':
    main()
