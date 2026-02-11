"""
HLTV Match Scraper
Örnek veri oluşturur (Test için)

NOT: Gerçek HLTV scraping için Selenium ve internet bağlantısı gerekir.
Bu versiyon test amaçlı örnek veri oluşturur.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os
import logging

# Logging kurulumu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HLTVSampleDataGenerator:
    """Örnek HLTV verisi oluşturucu"""
    
    def __init__(self):
        self.teams = [
            'Liquid', 'NIP', 'NAVI', 'G2', 'FaZe', 'Vitality', 
            'Heroic', 'Astralis', 'MOUZ', 'Spirit', 'Cloud9',
            'FURIA', 'Complexity', 'ENCE', 'BIG', 'OG',
            'Outsiders', 'GamerLegion', 'PARIVISION', 'B8',
            'Aurora', 'Passion UA', 'Legacy', 'BC.Game', 'FUT',
            '3DMAX', 'paiN', 'NRG', 'Gentle Mates'
        ]
        
        self.maps = [
            'Mirage', 'Inferno', 'Nuke', 'Dust2', 
            'Ancient', 'Vertigo', 'Overpass'
        ]
        
        self.events = [
            'IEM Katowice 2026',
            'BLAST Premier Spring 2026',
            'ESL Pro League Season 19',
            'PGL Major Copenhagen',
            'IEM Dallas 2026',
            'BLAST.tv Paris Major'
        ]
    
    def generate_match_results(self, num_matches=150):
        """
        Geçmiş maç sonuçları oluştur
        
        Args:
            num_matches: Oluşturulacak maç sayısı
        
        Returns:
            pandas.DataFrame: Maç sonuçları
        """
        logger.info(f"📊 {num_matches} geçmiş maç oluşturuluyor...")
        
        matches = []
        base_date = datetime.now() - timedelta(days=90)  # 3 ay önce başla
        
        for i in range(num_matches):
            # Rastgele iki takım seç
            team1, team2 = random.sample(self.teams, 2)
            
            # Skor oluştur (BO1 için genelde 13-16 arası)
            score1 = random.randint(10, 16)
            score2 = random.randint(10, 16)
            
            # Beraberlik olmasın
            if score1 == score2:
                score1 += random.randint(1, 3)
            
            # Tarih (son 3 ay içinde rastgele)
            days_ago = random.randint(0, 90)
            match_date = base_date + timedelta(days=days_ago)
            
            # Kazananı belirle
            winner = 1 if score1 > score2 else 2
            
            matches.append({
                'scrape_date': match_date.strftime('%Y-%m-%d %H:%M:%S'),
                'team_1': team1,
                'team_2': team2,
                'score_1': score1,
                'score_2': score2,
                'winner': winner,
                'event': random.choice(self.events),
                'map': random.choice(self.maps)
            })
        
        df = pd.DataFrame(matches)
        
        # Tarihe göre sırala (eski -> yeni)
        df['match_date'] = pd.to_datetime(df['scrape_date'])
        df = df.sort_values('match_date')
        df = df.drop('match_date', axis=1)
        
        logger.info(f"✅ {len(df)} maç oluşturuldu")
        return df
    
    def generate_upcoming_matches(self, num_matches=10):
        """
        Gelecek maçlar oluştur
        
        Args:
            num_matches: Oluşturulacak maç sayısı
        
        Returns:
            pandas.DataFrame: Gelecek maçlar
        """
        logger.info(f"📅 {num_matches} gelecek maç oluşturuluyor...")
        
        matches = []
        
        for i in range(num_matches):
            # Rastgele iki takım seç
            team1, team2 = random.sample(self.teams, 2)
            
            matches.append({
                'scrape_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'team_1': team1,
                'team_2': team2,
                'event': random.choice(self.events),
                'match_time': f"{random.randint(10, 22):02d}:00",
                'format': random.choice(['BO1', 'BO3', 'BO5'])
            })
        
        df = pd.DataFrame(matches)
        logger.info(f"✅ {len(df)} gelecek maç oluşturuldu")
        return df
    
    def save_data(self, results_file='hltv_match_results.csv', 
                  upcoming_file='hltv_upcoming_matches.csv'):
        """
        Verileri CSV dosyalarına kaydet
        
        Args:
            results_file: Geçmiş maçlar dosya adı
            upcoming_file: Gelecek maçlar dosya adı
        """
        # Geçmiş maçları oluştur ve kaydet
        results_df = self.generate_match_results(150)
        results_df.to_csv(results_file, index=False, encoding='utf-8')
        logger.info(f"💾 {results_file} kaydedildi ({len(results_df)} maç)")
        
        # Gelecek maçları oluştur ve kaydet
        upcoming_df = self.generate_upcoming_matches(10)
        upcoming_df.to_csv(upcoming_file, index=False, encoding='utf-8')
        logger.info(f"💾 {upcoming_file} kaydedildi ({len(upcoming_df)} maç)")
        
        return results_df, upcoming_df
    
    def print_summary(self, results_df, upcoming_df):
        """Özet bilgi yazdır"""
        print("\n" + "="*80)
        print("📊 VERİ OLUŞTURMA ÖZETİ")
        print("="*80)
        print(f"\n✅ Geçmiş Maçlar: {len(results_df)} maç")
        print(f"   Tarih Aralığı: {results_df['scrape_date'].min()} - {results_df['scrape_date'].max()}")
        print(f"   Farklı Takım: {len(set(results_df['team_1'].tolist() + results_df['team_2'].tolist()))}")
        print(f"   Farklı Harita: {len(results_df['map'].unique())}")
        
        print(f"\n✅ Gelecek Maçlar: {len(upcoming_df)} maç")
        print(f"   Format Dağılımı:")
        for format_type in upcoming_df['format'].value_counts().items():
            print(f"      {format_type[0]}: {format_type[1]} maç")
        
        print("\n" + "="*80)
        print("📂 OLUŞTURULAN DOSYALAR")
        print("="*80)
        print("   ✓ hltv_match_results.csv    - Geçmiş maç sonuçları")
        print("   ✓ hltv_upcoming_matches.csv - Gelecek maçlar")
        
        print("\n" + "="*80)
        print("🚀 SONRAKI ADIMLAR")
        print("="*80)
        print("   1. Modelleri eğitin:")
        print("      python precise_predictor.py")
        print()
        print("   2. Tahmin yapın:")
        print("      python telegram_bot.py")
        print("="*80 + "\n")


def main():
    """Ana fonksiyon"""
    print("="*80)
    print("  HLTV VERİ OLUŞTURUCU")
    print("="*80)
    print()
    print("⚠️  NOT: Bu gerçek HLTV scraper değildir!")
    print("   Test amaçlı örnek veri oluşturur.")
    print()
    print("   Gerçek HLTV verisi için:")
    print("   - Selenium kurulumu gerekir")
    print("   - İnternet bağlantısı gerekir")
    print("   - HLTV.org'dan izin gerekir")
    print()
    print("="*80 + "\n")
    
    # Generator oluştur
    generator = HLTVSampleDataGenerator()
    
    # Veri oluştur ve kaydet
    results_df, upcoming_df = generator.save_data()
    
    # Özet yazdır
    generator.print_summary(results_df, upcoming_df)
    
    # Örnek veriler göster
    print("📋 ÖRNEK GEÇMİŞ MAÇLAR (İlk 5):")
    print("-"*80)
    print(results_df.head().to_string(index=False))
    
    print("\n📋 ÖRNEK GELECEK MAÇLAR (İlk 5):")
    print("-"*80)
    print(upcoming_df.head().to_string(index=False))
    print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  İşlem iptal edildi")
    except Exception as e:
        print(f"\n\n❌ Hata: {e}")
        import traceback
        traceback.print_exc()
