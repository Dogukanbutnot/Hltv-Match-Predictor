"""
Advanced HLTV Match Predictor with Map-Based Analysis
Includes map-specific win rates, time filtering, and detailed match predictions
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import xgboost as xgb
import lightgbm as lgb
import joblib
import os
import warnings
warnings.filterwarnings('ignore')


class AdvancedMapPredictor:
    """
    Gelişmiş harita bazlı tahmin sistemi
    - Son 3 ay filtresi
    - Harita bazında kazanma oranları
    - Takım vs takım harita performansı
    - Detaylı form analizi
    """
    
    def __init__(self, results_file="hltv_match_results.csv"):
        self.results_file = results_file
        self.df = None
        self.models = {}
        self.scaler = StandardScaler()
        self.team_stats = {}
        self.map_stats = {}  # Yeni: Harita bazlı istatistikler
        self.recent_months = 3  # Son 3 ay
        
    def load_data(self):
        """Verileri yükle ve temizle"""
        if not os.path.exists(self.results_file):
            print(f"❌ Dosya bulunamadı: {self.results_file}")
            return False
        
        self.df = pd.read_csv(self.results_file)
        
        # Tarih formatını düzelt
        if 'scrape_date' in self.df.columns:
            self.df['match_date'] = pd.to_datetime(self.df['scrape_date'], errors='coerce')
        
        # Geçersiz skorları temizle
        self.df = self.df[
            (self.df['score_1'] != 'N/A') & 
            (self.df['score_2'] != 'N/A')
        ].copy()
        
        self.df['score_1'] = pd.to_numeric(self.df['score_1'], errors='coerce')
        self.df['score_2'] = pd.to_numeric(self.df['score_2'], errors='coerce')
        self.df = self.df.dropna(subset=['score_1', 'score_2'])
        
        print(f"✅ {len(self.df)} maç yüklendi")
        return True
    
    def calculate_team_stats_with_time_filter(self, months=3):
        """
        Son X ay için takım istatistiklerini hesapla
        """
        print(f"📊 Son {months} ay için takım istatistikleri hesaplanıyor...")
        
        # Zaman filtresi
        cutoff_date = datetime.now() - timedelta(days=months * 30)
        
        if 'match_date' in self.df.columns:
            recent_df = self.df[self.df['match_date'] >= cutoff_date]
            print(f"   Son {months} ayda {len(recent_df)} maç bulundu")
        else:
            recent_df = self.df
            print(f"   ⚠️  Tarih bilgisi yok, tüm veriler kullanılıyor")
        
        teams = set(list(recent_df['team_1']) + list(recent_df['team_2']))
        
        for team in teams:
            team_matches = recent_df[
                (recent_df['team_1'] == team) | (recent_df['team_2'] == team)
            ]
            
            wins = 0
            total_rounds_won = 0
            total_rounds_lost = 0
            matches_played = len(team_matches)
            
            # Son 5 maç formu
            recent_5 = team_matches.tail(5)
            recent_wins = 0
            
            for _, match in team_matches.iterrows():
                is_team1 = (match['team_1'] == team)
                
                if is_team1:
                    rounds_won = match['score_1']
                    rounds_lost = match['score_2']
                    if match['winner'] == 1:
                        wins += 1
                else:
                    rounds_won = match['score_2']
                    rounds_lost = match['score_1']
                    if match['winner'] == 2:
                        wins += 1
                
                total_rounds_won += rounds_won
                total_rounds_lost += rounds_lost
            
            # Son 5 maç formu
            for _, match in recent_5.iterrows():
                is_team1 = (match['team_1'] == team)
                if (is_team1 and match['winner'] == 1) or (not is_team1 and match['winner'] == 2):
                    recent_wins += 1
            
            win_rate = wins / matches_played if matches_played > 0 else 0
            recent_form = recent_wins / len(recent_5) if len(recent_5) > 0 else 0
            avg_rounds_won = total_rounds_won / matches_played if matches_played > 0 else 0
            avg_rounds_lost = total_rounds_lost / matches_played if matches_played > 0 else 0
            round_diff = avg_rounds_won - avg_rounds_lost
            
            self.team_stats[team] = {
                'matches_played': matches_played,
                'wins': wins,
                'losses': matches_played - wins,
                'win_rate': win_rate,
                'recent_form': recent_form,  # Yeni: Son 5 maç formu
                'avg_rounds_won': avg_rounds_won,
                'avg_rounds_lost': avg_rounds_lost,
                'round_diff': round_diff,
                'last_updated': datetime.now()
            }
        
        print(f"✅ {len(self.team_stats)} takım için istatistikler hesaplandı")
    
    def calculate_map_based_stats(self, months=3):
        """
        🗺️ HARITA BAZLI İSTATİSTİKLER
        Her takım için her haritada kazanma oranı
        """
        print(f"\n🗺️  Son {months} ay için harita bazlı istatistikler hesaplanıyor...")
        
        # Zaman filtresi
        cutoff_date = datetime.now() - timedelta(days=months * 30)
        
        if 'match_date' in self.df.columns:
            recent_df = self.df[self.df['match_date'] >= cutoff_date]
        else:
            recent_df = self.df
        
        # Harita sütunu yoksa ekle (örnek veri için)
        if 'map' not in recent_df.columns:
            # Eğer harita bilgisi yoksa, popüler haritaları rastgele ata (gerçek veriler için bu kısım gerekli olmayacak)
            maps = ['Mirage', 'Inferno', 'Dust2', 'Nuke', 'Overpass', 'Vertigo', 'Ancient']
            recent_df['map'] = np.random.choice(maps, len(recent_df))
            print("   ⚠️  Harita bilgisi bulunamadı, örnek haritalar atandı")
        
        teams = set(list(recent_df['team_1']) + list(recent_df['team_2']))
        available_maps = recent_df['map'].unique()
        
        for team in teams:
            self.map_stats[team] = {}
            
            for map_name in available_maps:
                # Bu takımın bu haritada oynadığı maçlar
                map_matches = recent_df[
                    ((recent_df['team_1'] == team) | (recent_df['team_2'] == team)) &
                    (recent_df['map'] == map_name)
                ]
                
                if len(map_matches) == 0:
                    continue
                
                wins = 0
                total_rounds_won = 0
                total_rounds_lost = 0
                
                for _, match in map_matches.iterrows():
                    is_team1 = (match['team_1'] == team)
                    
                    if is_team1:
                        rounds_won = match['score_1']
                        rounds_lost = match['score_2']
                        if match['winner'] == 1:
                            wins += 1
                    else:
                        rounds_won = match['score_2']
                        rounds_lost = match['score_1']
                        if match['winner'] == 2:
                            wins += 1
                    
                    total_rounds_won += rounds_won
                    total_rounds_lost += rounds_lost
                
                matches_played = len(map_matches)
                win_rate = wins / matches_played if matches_played > 0 else 0
                avg_rounds = total_rounds_won / matches_played if matches_played > 0 else 0
                
                self.map_stats[team][map_name] = {
                    'matches': matches_played,
                    'wins': wins,
                    'losses': matches_played - wins,
                    'win_rate': win_rate,
                    'avg_rounds_won': avg_rounds,
                    'avg_rounds_lost': total_rounds_lost / matches_played if matches_played > 0 else 0,
                    'round_diff': avg_rounds - (total_rounds_lost / matches_played if matches_played > 0 else 0)
                }
        
        print(f"✅ {len(self.map_stats)} takım için harita istatistikleri hesaplandı")
        print(f"   Toplam {len(available_maps)} farklı harita bulundu: {', '.join(available_maps)}")
    
    def predict_map_matchup(self, team1, team2, map_name):
        """
        Belirli bir harita için iki takımın karşılaşmasını tahmin et
        Liquid vs NIP - Nuke örneği
        """
        print(f"\n{'='*80}")
        print(f"🎯 HARITA BAZLI TAHMİN: {team1} vs {team2} - {map_name}")
        print(f"{'='*80}")
        
        # Takım kontrolü
        if team1 not in self.team_stats or team2 not in self.team_stats:
            return {
                'error': f'Takım istatistikleri bulunamadı',
                'available_teams': list(self.team_stats.keys())[:20]
            }
        
        # Genel takım istatistikleri
        stats1 = self.team_stats[team1]
        stats2 = self.team_stats[team2]
        
        print(f"\n📊 GENEL TAKIM İSTATİSTİKLERİ (Son {self.recent_months} Ay):")
        print(f"-" * 80)
        print(f"{team1:20s} - Win Rate: {stats1['win_rate']*100:.1f}% | Form: {stats1['recent_form']*100:.1f}% | Maçlar: {stats1['matches_played']}")
        print(f"{team2:20s} - Win Rate: {stats2['win_rate']*100:.1f}% | Form: {stats2['recent_form']*100:.1f}% | Maçlar: {stats2['matches_played']}")
        
        # Harita bazlı istatistikler
        map_stats1 = self.map_stats.get(team1, {}).get(map_name, None)
        map_stats2 = self.map_stats.get(team2, {}).get(map_name, None)
        
        print(f"\n🗺️  HARITA İSTATİSTİKLERİ - {map_name.upper()}:")
        print(f"-" * 80)
        
        if map_stats1:
            print(f"{team1:20s} - Win Rate: {map_stats1['win_rate']*100:.1f}% | Maçlar: {map_stats1['matches']} | Avg Rounds: {map_stats1['avg_rounds_won']:.1f}")
        else:
            print(f"{team1:20s} - ⚠️  Bu haritada veri yok")
        
        if map_stats2:
            print(f"{team2:20s} - Win Rate: {map_stats2['win_rate']*100:.1f}% | Maçlar: {map_stats2['matches']} | Avg Rounds: {map_stats2['avg_rounds_won']:.1f}")
        else:
            print(f"{team2:20s} - ⚠️  Bu haritada veri yok")
        
        # TAHMİN HESAPLAMA
        print(f"\n🔮 TAHMİN ANALİZİ:")
        print(f"-" * 80)
        
        # Skorlama sistemi
        team1_score = 0
        team2_score = 0
        factors = []
        
        # 1. Harita bazlı kazanma oranı (En önemli - %40)
        if map_stats1 and map_stats2:
            map_advantage = (map_stats1['win_rate'] - map_stats2['win_rate']) * 100
            if map_advantage > 10:
                team1_score += 40
                factors.append(f"✅ {team1} haritada {map_advantage:.1f}% daha iyi (+40 puan)")
            elif map_advantage < -10:
                team2_score += 40
                factors.append(f"✅ {team2} haritada {abs(map_advantage):.1f}% daha iyi (+40 puan)")
            else:
                team1_score += 20
                team2_score += 20
                factors.append(f"⚖️  Haritada dengeli performans (her takıma +20 puan)")
        elif map_stats1:
            team1_score += 30
            factors.append(f"✅ {team1} haritada deneyimli ({map_stats1['matches']} maç) (+30 puan)")
        elif map_stats2:
            team2_score += 30
            factors.append(f"✅ {team2} haritada deneyimli ({map_stats2['matches']} maç) (+30 puan)")
        else:
            factors.append(f"⚠️  Her iki takım için de harita verisi yok")
        
        # 2. Genel form (Son 5 maç - %25)
        form_diff = (stats1['recent_form'] - stats2['recent_form']) * 100
        if form_diff > 20:
            team1_score += 25
            factors.append(f"✅ {team1} daha iyi formda ({stats1['recent_form']*100:.0f}% vs {stats2['recent_form']*100:.0f}%) (+25 puan)")
        elif form_diff < -20:
            team2_score += 25
            factors.append(f"✅ {team2} daha iyi formda ({stats2['recent_form']*100:.0f}% vs {stats1['recent_form']*100:.0f}%) (+25 puan)")
        else:
            team1_score += 12
            team2_score += 13
            factors.append(f"⚖️  Benzer form seviyesi (her takıma ~12 puan)")
        
        # 3. Genel kazanma oranı (%20)
        overall_diff = (stats1['win_rate'] - stats2['win_rate']) * 100
        if overall_diff > 15:
            team1_score += 20
            factors.append(f"✅ {team1} genel olarak daha başarılı ({stats1['win_rate']*100:.1f}% vs {stats2['win_rate']*100:.1f}%) (+20 puan)")
        elif overall_diff < -15:
            team2_score += 20
            factors.append(f"✅ {team2} genel olarak daha başarılı ({stats2['win_rate']*100:.1f}% vs {stats1['win_rate']*100:.1f}%) (+20 puan)")
        else:
            team1_score += 10
            team2_score += 10
            factors.append(f"⚖️  Benzer genel performans (her takıma +10 puan)")
        
        # 4. Round differential (Haritada - %15)
        if map_stats1 and map_stats2:
            rd_diff = map_stats1['round_diff'] - map_stats2['round_diff']
            if rd_diff > 2:
                team1_score += 15
                factors.append(f"✅ {team1} haritada daha iyi round farkı (+{map_stats1['round_diff']:.1f}) (+15 puan)")
            elif rd_diff < -2:
                team2_score += 15
                factors.append(f"✅ {team2} haritada daha iyi round farkı (+{map_stats2['round_diff']:.1f}) (+15 puan)")
            else:
                team1_score += 7
                team2_score += 8
                factors.append(f"⚖️  Benzer round farkı (her takıma ~7 puan)")
        
        # Toplam skorları normalize et (100 puan üzerinden)
        total = team1_score + team2_score
        if total > 0:
            team1_prob = team1_score / total
            team2_prob = team2_score / total
        else:
            team1_prob = 0.5
            team2_prob = 0.5
        
        # Kazanan belirle
        winner = team1 if team1_prob > team2_prob else team2
        confidence = max(team1_prob, team2_prob) * 100
        
        # Güven seviyesi
        if confidence >= 70:
            confidence_level = "Çok Yüksek"
        elif confidence >= 60:
            confidence_level = "Yüksek"
        elif confidence >= 55:
            confidence_level = "Orta"
        else:
            confidence_level = "Düşük"
        
        print("\n" + "=" * 80)
        print("📈 FAKTÖR ANALİZİ:")
        print("-" * 80)
        for factor in factors:
            print(f"   {factor}")
        
        print("\n" + "=" * 80)
        print("🏆 SONUÇ:")
        print("-" * 80)
        print(f"   Kazanan Tahmini: {winner}")
        print(f"   {team1}: {team1_prob*100:.1f}% ({team1_score} puan)")
        print(f"   {team2}: {team2_prob*100:.1f}% ({team2_score} puan)")
        print(f"   Güven Seviyesi: {confidence_level} ({confidence:.1f}%)")
        print("=" * 80)
        
        return {
            'team1': team1,
            'team2': team2,
            'map': map_name,
            'predicted_winner': winner,
            'team1_probability': f"{team1_prob*100:.1f}%",
            'team2_probability': f"{team2_prob*100:.1f}%",
            'confidence': f"{confidence:.1f}%",
            'confidence_level': confidence_level,
            'team1_score': team1_score,
            'team2_score': team2_score,
            'factors': factors,
            'team1_general_stats': stats1,
            'team2_general_stats': stats2,
            'team1_map_stats': map_stats1,
            'team2_map_stats': map_stats2
        }
    
    def predict_bo3_match(self, team1, team2, map_pool=None):
        """
        BO3 (Best of 3) maç tahmini
        3 harita için ayrı ayrı tahmin yapar
        """
        if map_pool is None or len(map_pool) != 3:
            print("⚠️  BO3 için 3 harita gerekli (örnek: ['Mirage', 'Nuke', 'Inferno'])")
            map_pool = ['Mirage', 'Nuke', 'Inferno']  # Varsayılan
        
        print(f"\n{'='*80}")
        print(f"🎮 BO3 TAHMİNİ: {team1} vs {team2}")
        print(f"   Harita Havuzu: {', '.join(map_pool)}")
        print(f"{'='*80}")
        
        predictions = []
        team1_wins = 0
        team2_wins = 0
        
        for i, map_name in enumerate(map_pool, 1):
            print(f"\n{'='*80}")
            print(f"HARITA {i}: {map_name}")
            print(f"{'='*80}")
            
            pred = self.predict_map_matchup(team1, team2, map_name)
            predictions.append(pred)
            
            if pred['predicted_winner'] == team1:
                team1_wins += 1
            else:
                team2_wins += 1
        
        # BO3 kazananı
        bo3_winner = team1 if team1_wins > team2_wins else team2
        final_score = f"{team1_wins}-{team2_wins}" if bo3_winner == team1 else f"{team2_wins}-{team1_wins}"
        
        print(f"\n{'='*80}")
        print(f"🏆 BO3 SONUÇ TAHMİNİ")
        print(f"{'='*80}")
        print(f"   Kazanan: {bo3_winner}")
        print(f"   Skor: {final_score}")
        print(f"   {team1}: {team1_wins} harita")
        print(f"   {team2}: {team2_wins} harita")
        print(f"{'='*80}")
        
        return {
            'match_type': 'BO3',
            'team1': team1,
            'team2': team2,
            'map_pool': map_pool,
            'predicted_winner': bo3_winner,
            'predicted_score': final_score,
            'team1_map_wins': team1_wins,
            'team2_map_wins': team2_wins,
            'map_predictions': predictions
        }


def main():
    """Ana çalıştırma fonksiyonu"""
    print("🎮 GELİŞMİŞ HARITA BAZLI TAHMİN SİSTEMİ")
    print("=" * 80)
    print("✓ Harita bazlı win rate analizi")
    print("✓ Son 3 ay filtresi")
    print("✓ Detaylı form analizi")
    print("✓ BO3 maç tahminleri")
    print("=" * 80)
    
    predictor = AdvancedMapPredictor()
    
    # Veri yükle
    if not predictor.load_data():
        print("\n⚠️  Önce veri toplamak gerekiyor:")
        print("   python hltv_scraper.py")
        return
    
    # İstatistikleri hesapla
    predictor.calculate_team_stats_with_time_filter(months=3)
    predictor.calculate_map_based_stats(months=3)
    
    # Örnek tahmin: Liquid vs NIP - Nuke
    print("\n" + "="*80)
    print("ÖRNEK TAHMİN: Liquid vs NIP - Nuke Haritası")
    print("="*80)
    
    # Gerçek takım isimlerini kontrol et
    available_teams = list(predictor.team_stats.keys())
    if len(available_teams) >= 2:
        # İlk iki takımı örnek olarak kullan
        team1, team2 = available_teams[0], available_teams[1]
        available_maps = list(set([
            map_name 
            for team_maps in predictor.map_stats.values() 
            for map_name in team_maps.keys()
        ]))
        
        if available_maps:
            map_name = available_maps[0]
            result = predictor.predict_map_matchup(team1, team2, map_name)


if __name__ == "__main__":
    main()
