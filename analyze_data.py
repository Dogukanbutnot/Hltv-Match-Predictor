"""
HLTV Data Analyzer
Takım istatistikleri ve veri analizi
"""

import pandas as pd
import os
from datetime import datetime, timedelta


class HLTVAnalyzer:
    """HLTV maç verilerini analiz eder"""
    
    def __init__(self, results_file="hltv_match_results.csv"):
        self.results_file = results_file
        self.df = None
        
    def load_data(self):
        """Veriyi yükle"""
        if not os.path.exists(self.results_file):
            print(f"❌ Dosya bulunamadı: {self.results_file}")
            print(f"   Lütfen önce veri toplayın: python hltv_scraper.py")
            return False
        
        self.df = pd.read_csv(self.results_file)
        print(f"✅ {len(self.df)} maç yüklendi")
        return True
    
    def get_team_stats(self, team_name, months=3):
        """
        Belirli bir takımın istatistiklerini getir
        
        Args:
            team_name: Takım adı
            months: Son kaç ay (varsayılan 3)
        
        Returns:
            dict: Takım istatistikleri
        """
        if self.df is None:
            print("❌ Önce veri yüklenmeli")
            return None
        
        # Zaman filtresi
        if 'scrape_date' in self.df.columns:
            self.df['match_date'] = pd.to_datetime(self.df['scrape_date'], errors='coerce')
            cutoff_date = datetime.now() - timedelta(days=months * 30)
            recent_df = self.df[self.df['match_date'] >= cutoff_date]
        else:
            recent_df = self.df
        
        # Takımın maçlarını bul
        team_matches = recent_df[
            (recent_df['team_1'].str.contains(team_name, case=False, na=False)) |
            (recent_df['team_2'].str.contains(team_name, case=False, na=False))
        ]
        
        if team_matches.empty:
            print(f"❌ '{team_name}' için maç bulunamadı")
            
            # Benzer isimleri öner
            all_teams = set(list(recent_df['team_1'].dropna()) + list(recent_df['team_2'].dropna()))
            similar = [t for t in all_teams if team_name.lower() in t.lower()]
            
            if similar:
                print(f"\n💡 Belki şunlardan birini mi arıyordunuz?")
                for t in similar[:5]:
                    print(f"   - {t}")
            else:
                print(f"\n💡 Mevcut takımlardan bazıları:")
                for t in list(all_teams)[:10]:
                    print(f"   - {t}")
            
            return None
        
        # İstatistikleri hesapla
        wins = 0
        losses = 0
        total_rounds_won = 0
        total_rounds_lost = 0
        maps_played = {}
        
        for _, match in team_matches.iterrows():
            is_team1 = team_name.lower() in str(match['team_1']).lower()
            
            if is_team1:
                rounds_won = match['score_1']
                rounds_lost = match['score_2']
                if match['winner'] == 1:
                    wins += 1
                else:
                    losses += 1
            else:
                rounds_won = match['score_2']
                rounds_lost = match['score_1']
                if match['winner'] == 2:
                    wins += 1
                else:
                    losses += 1
            
            total_rounds_won += rounds_won
            total_rounds_lost += rounds_lost
            
            # Harita istatistikleri
            map_name = match.get('map', 'Unknown')
            if map_name not in maps_played:
                maps_played[map_name] = {'wins': 0, 'losses': 0, 'total': 0}
            
            maps_played[map_name]['total'] += 1
            if (is_team1 and match['winner'] == 1) or (not is_team1 and match['winner'] == 2):
                maps_played[map_name]['wins'] += 1
            else:
                maps_played[map_name]['losses'] += 1
        
        total_matches = len(team_matches)
        win_rate = wins / total_matches if total_matches > 0 else 0
        avg_rounds_won = total_rounds_won / total_matches if total_matches > 0 else 0
        avg_rounds_lost = total_rounds_lost / total_matches if total_matches > 0 else 0
        
        # En iyi ve en kötü haritalar
        best_map = max(maps_played.items(), 
                      key=lambda x: x[1]['wins'] / x[1]['total'] if x[1]['total'] > 0 else 0)[0] if maps_played else 'N/A'
        worst_map = min(maps_played.items(), 
                       key=lambda x: x[1]['wins'] / x[1]['total'] if x[1]['total'] > 0 else 1)[0] if maps_played else 'N/A'
        
        return {
            'team': team_name,
            'matches_played': total_matches,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'avg_rounds_won': avg_rounds_won,
            'avg_rounds_lost': avg_rounds_lost,
            'round_diff': avg_rounds_won - avg_rounds_lost,
            'maps_played': maps_played,
            'best_map': best_map,
            'worst_map': worst_map
        }
    
    def compare_teams(self, team1, team2):
        """İki takımı karşılaştır"""
        print(f"\n{'='*80}")
        print(f"⚔️  {team1} vs {team2} - KARŞILAŞTIRMA")
        print(f"{'='*80}\n")
        
        stats1 = self.get_team_stats(team1)
        stats2 = self.get_team_stats(team2)
        
        if not stats1 or not stats2:
            return None
        
        # Head-to-head
        h2h = self.df[
            ((self.df['team_1'].str.contains(team1, case=False, na=False)) & 
             (self.df['team_2'].str.contains(team2, case=False, na=False))) |
            ((self.df['team_1'].str.contains(team2, case=False, na=False)) & 
             (self.df['team_2'].str.contains(team1, case=False, na=False)))
        ]
        
        team1_wins = 0
        team2_wins = 0
        
        if not h2h.empty:
            for _, match in h2h.iterrows():
                is_team1_first = team1.lower() in str(match['team_1']).lower()
                
                if (is_team1_first and match['winner'] == 1) or (not is_team1_first and match['winner'] == 2):
                    team1_wins += 1
                else:
                    team2_wins += 1
        
        print("📊 GENEL İSTATİSTİKLER:")
        print("-"*80)
        print(f"{'':20s} {team1:20s} {team2:20s}")
        print(f"{'Oynanan Maç':20s} {stats1['matches_played']:<20d} {stats2['matches_played']:<20d}")
        print(f"{'Galibiyet':20s} {stats1['wins']:<20d} {stats2['wins']:<20d}")
        print(f"{'Mağlubiyet':20s} {stats1['losses']:<20d} {stats2['losses']:<20d}")
        print(f"{'Kazanma Oranı':20s} {stats1['win_rate']*100:<20.1f}% {stats2['win_rate']*100:<20.1f}%")
        print(f"{'Ort. Round Kazanma':20s} {stats1['avg_rounds_won']:<20.1f} {stats2['avg_rounds_won']:<20.1f}")
        print(f"{'Round Farkı':20s} {stats1['round_diff']:<+20.1f} {stats2['round_diff']:<+20.1f}")
        
        print(f"\n🗺️  HARITA PERFORMANSI:")
        print("-"*80)
        print(f"{team1} - En İyi: {stats1['best_map']}, En Kötü: {stats1['worst_map']}")
        print(f"{team2} - En İyi: {stats2['best_map']}, En Kötü: {stats2['worst_map']}")
        
        if not h2h.empty:
            print(f"\n🎯 HEAD-TO-HEAD:")
            print("-"*80)
            print(f"Toplam Karşılaşma: {len(h2h)} maç")
            print(f"{team1} Galibiyetleri: {team1_wins}")
            print(f"{team2} Galibiyetleri: {team2_wins}")
            
            if team1_wins > team2_wins:
                print(f"\n🏆 {team1} H2H'da üstün!")
            elif team2_wins > team1_wins:
                print(f"\n🏆 {team2} H2H'da üstün!")
            else:
                print(f"\n⚖️  H2H dengede!")
        else:
            print(f"\n❌ Head-to-head maç bulunamadı")
        
        print("="*80 + "\n")
        
        return {
            'team1_stats': stats1,
            'team2_stats': stats2,
            'h2h_matches': len(h2h),
            'team1_h2h_wins': team1_wins,
            'team2_h2h_wins': team2_wins
        }
    
    def get_top_teams(self, limit=10):
        """En iyi takımları listele"""
        print(f"\n{'='*80}")
        print(f"🏆 EN İYİ {limit} TAKIM (Son 3 Ay)")
        print(f"{'='*80}\n")
        
        # Tüm takımları bul
        teams = set()
        teams.update(self.df['team_1'].dropna().unique())
        teams.update(self.df['team_2'].dropna().unique())
        
        team_stats = []
        for team in teams:
            stats = self.get_team_stats(team)
            if stats and stats['matches_played'] >= 5:  # En az 5 maç
                team_stats.append(stats)
        
        # Win rate'e göre sırala
        team_stats.sort(key=lambda x: (x['wins'], x['win_rate']), reverse=True)
        
        print(f"{'Sıra':4s} {'Takım':20s} {'Maç':6s} {'G':4s} {'M':4s} {'WR%':6s} {'RD':7s}")
        print("-"*80)
        
        for i, stats in enumerate(team_stats[:limit], 1):
            print(f"{i:3d}. {stats['team']:20s} "
                  f"{stats['matches_played']:5d} "
                  f"{stats['wins']:3d} "
                  f"{stats['losses']:3d} "
                  f"{stats['win_rate']*100:5.1f}% "
                  f"{stats['round_diff']:+6.1f}")
        
        print("="*80 + "\n")
        
        return team_stats[:limit]
    
    def print_summary(self):
        """Veri özeti"""
        if self.df is None:
            print("❌ Veri yüklenmedi")
            return
        
        print("\n" + "="*80)
        print("📊 VERİ ÖZETİ")
        print("="*80)
        
        total_matches = len(self.df)
        teams = set(list(self.df['team_1'].dropna()) + list(self.df['team_2'].dropna()))
        
        print(f"\nToplam Maç: {total_matches}")
        print(f"Farklı Takım: {len(teams)}")
        
        if 'scrape_date' in self.df.columns:
            print(f"Tarih Aralığı: {self.df['scrape_date'].min()} - {self.df['scrape_date'].max()}")
        
        if 'map' in self.df.columns:
            print(f"\nHarita Dağılımı:")
            map_counts = self.df['map'].value_counts()
            for map_name, count in map_counts.items():
                print(f"  {map_name:15s}: {count:3d} maç ({count/total_matches*100:.1f}%)")
        
        if 'event' in self.df.columns:
            print(f"\nEn Popüler Turnuvalar:")
            event_counts = self.df['event'].value_counts().head(5)
            for event, count in event_counts.items():
                print(f"  {event:30s}: {count:3d} maç")
        
        print("="*80 + "\n")


def main():
    """Ana fonksiyon"""
    print("="*80)
    print("  HLTV VERİ ANALİZCİSİ")
    print("="*80 + "\n")
    
    analyzer = HLTVAnalyzer()
    
    if not analyzer.load_data():
        return
    
    # Veri özeti
    analyzer.print_summary()
    
    # En iyi takımlar
    analyzer.get_top_teams(limit=15)
    
    # İnteraktif mod
    print("\n" + "="*80)
    print("🔍 İNTERAKTİF ANALİZ")
    print("="*80 + "\n")
    
    while True:
        print("\nSeçenekler:")
        print("  1. Takım istatistikleri")
        print("  2. İki takımı karşılaştır")
        print("  3. Çıkış")
        
        choice = input("\nSeçiminiz (1-3): ").strip()
        
        if choice == '1':
            team = input("\nTakım adı: ").strip()
            stats = analyzer.get_team_stats(team)
            
            if stats:
                print(f"\n{'='*80}")
                print(f"📊 {stats['team'].upper()} İSTATİSTİKLERİ")
                print(f"{'='*80}\n")
                print(f"Oynanan Maç: {stats['matches_played']}")
                print(f"Galibiyet: {stats['wins']}")
                print(f"Mağlubiyet: {stats['losses']}")
                print(f"Kazanma Oranı: {stats['win_rate']*100:.1f}%")
                print(f"Ortalama Round Kazanma: {stats['avg_rounds_won']:.1f}")
                print(f"Ortalama Round Kaybetme: {stats['avg_rounds_lost']:.1f}")
                print(f"Round Farkı: {stats['round_diff']:+.1f}")
                print(f"\nEn İyi Harita: {stats['best_map']}")
                print(f"En Kötü Harita: {stats['worst_map']}")
                
                if stats['maps_played']:
                    print(f"\n🗺️  Harita Bazlı Performans:")
                    for map_name, map_stats in stats['maps_played'].items():
                        wr = map_stats['wins'] / map_stats['total'] * 100 if map_stats['total'] > 0 else 0
                        print(f"  {map_name:15s}: {map_stats['wins']:2d}W-{map_stats['losses']:2d}L ({wr:.1f}%)")
                
                print("="*80)
        
        elif choice == '2':
            team1 = input("\nİlk takım: ").strip()
            team2 = input("İkinci takım: ").strip()
            analyzer.compare_teams(team1, team2)
        
        elif choice == '3':
            print("\n👋 Görüşmek üzere!")
            break
        
        else:
            print("\n❌ Geçersiz seçim")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Çıkış yapılıyor...")
    except Exception as e:
        print(f"\n\n❌ Hata: {e}")
        import traceback
        traceback.print_exc()
