"""
Kesin Tahmin Motoru
Tam yüzdelerle (örn: %61.3) tahmin yapar
Model performans metrikleri dahil
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, 
    f1_score, roc_auc_score, classification_report,
    confusion_matrix
)
import xgboost as xgb
import lightgbm as lgb
import joblib
import os
import warnings
warnings.filterwarnings('ignore')


class PrecisionMatchPredictor:
    """
    Kesin yüzde tahminleri yapan ML sistemi
    Model performans metrikleri ile birlikte
    """
    
    def __init__(self, results_file="hltv_match_results.csv"):
        self.results_file = results_file
        self.df = None
        self.models = {}
        self.scaler = StandardScaler()
        self.team_stats = {}
        self.map_stats = {}
        self.model_metrics = {}  # Model performans metrikleri
        self.recent_months = 3
        
    def load_data(self):
        """Veri yükle"""
        if not os.path.exists(self.results_file):
            print(f"❌ Dosya bulunamadı: {self.results_file}")
            return False
        
        self.df = pd.read_csv(self.results_file)
        
        # Tarih düzeltme
        if 'scrape_date' in self.df.columns:
            self.df['match_date'] = pd.to_datetime(self.df['scrape_date'], errors='coerce')
        
        # Temizlik
        self.df = self.df[
            (self.df['score_1'] != 'N/A') & 
            (self.df['score_2'] != 'N/A')
        ].copy()
        
        self.df['score_1'] = pd.to_numeric(self.df['score_1'], errors='coerce')
        self.df['score_2'] = pd.to_numeric(self.df['score_2'], errors='coerce')
        self.df = self.df.dropna(subset=['score_1', 'score_2'])
        
        print(f"✅ {len(self.df)} maç yüklendi")
        return True
    
    def calculate_team_stats(self, months=3):
        """Takım istatistikleri hesapla"""
        cutoff_date = datetime.now() - timedelta(days=months * 30)
        
        if 'match_date' in self.df.columns:
            recent_df = self.df[self.df['match_date'] >= cutoff_date]
        else:
            recent_df = self.df
        
        teams = set(list(recent_df['team_1']) + list(recent_df['team_2']))
        
        for team in teams:
            team_matches = recent_df[
                (recent_df['team_1'] == team) | (recent_df['team_2'] == team)
            ]
            
            wins = 0
            total_rounds_won = 0
            total_rounds_lost = 0
            matches_played = len(team_matches)
            
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
            
            for _, match in recent_5.iterrows():
                is_team1 = (match['team_1'] == team)
                if (is_team1 and match['winner'] == 1) or (not is_team1 and match['winner'] == 2):
                    recent_wins += 1
            
            win_rate = wins / matches_played if matches_played > 0 else 0
            recent_form = recent_wins / len(recent_5) if len(recent_5) > 0 else 0
            avg_rounds_won = total_rounds_won / matches_played if matches_played > 0 else 0
            avg_rounds_lost = total_rounds_lost / matches_played if matches_played > 0 else 0
            
            self.team_stats[team] = {
                'matches_played': matches_played,
                'wins': wins,
                'win_rate': win_rate,
                'recent_form': recent_form,
                'avg_rounds_won': avg_rounds_won,
                'avg_rounds_lost': avg_rounds_lost,
                'round_diff': avg_rounds_won - avg_rounds_lost,
            }
    
    def calculate_map_stats(self, months=3):
        """Harita bazlı istatistikler"""
        cutoff_date = datetime.now() - timedelta(days=months * 30)
        
        if 'match_date' in self.df.columns:
            recent_df = self.df[self.df['match_date'] >= cutoff_date]
        else:
            recent_df = self.df
        
        # Harita bilgisi yoksa örnek ata
        if 'map' not in recent_df.columns:
            maps = ['Mirage', 'Inferno', 'Dust2', 'Nuke', 'Overpass', 'Vertigo', 'Ancient']
            recent_df['map'] = np.random.choice(maps, len(recent_df))
        
        teams = set(list(recent_df['team_1']) + list(recent_df['team_2']))
        available_maps = recent_df['map'].unique()
        
        for team in teams:
            self.map_stats[team] = {}
            
            for map_name in available_maps:
                map_matches = recent_df[
                    ((recent_df['team_1'] == team) | (recent_df['team_2'] == team)) &
                    (recent_df['map'] == map_name)
                ]
                
                if len(map_matches) == 0:
                    continue
                
                wins = 0
                total_rounds = 0
                
                for _, match in map_matches.iterrows():
                    is_team1 = (match['team_1'] == team)
                    
                    if is_team1:
                        rounds_won = match['score_1']
                        if match['winner'] == 1:
                            wins += 1
                    else:
                        rounds_won = match['score_2']
                        if match['winner'] == 2:
                            wins += 1
                    
                    total_rounds += rounds_won
                
                matches_played = len(map_matches)
                win_rate = wins / matches_played if matches_played > 0 else 0
                
                self.map_stats[team][map_name] = {
                    'matches': matches_played,
                    'wins': wins,
                    'win_rate': win_rate,
                    'avg_rounds': total_rounds / matches_played if matches_played > 0 else 0
                }
    
    def create_features(self):
        """Özellik vektörleri oluştur"""
        features = []
        labels = []
        
        for idx, match in self.df.iterrows():
            team1 = match['team_1']
            team2 = match['team_2']
            
            if team1 not in self.team_stats or team2 not in self.team_stats:
                continue
            
            stats1 = self.team_stats[team1]
            stats2 = self.team_stats[team2]
            
            # Harita özellikleri ekle
            map_name = match.get('map', None)
            map_wr1 = 0
            map_wr2 = 0
            
            if map_name and team1 in self.map_stats and map_name in self.map_stats[team1]:
                map_wr1 = self.map_stats[team1][map_name]['win_rate']
            if map_name and team2 in self.map_stats and map_name in self.map_stats[team2]:
                map_wr2 = self.map_stats[team2][map_name]['win_rate']
            
            feature_vector = [
                stats1['win_rate'],
                stats2['win_rate'],
                stats1['recent_form'],
                stats2['recent_form'],
                stats1['avg_rounds_won'],
                stats2['avg_rounds_won'],
                stats1['round_diff'],
                stats2['round_diff'],
                stats1['matches_played'],
                stats2['matches_played'],
                stats1['win_rate'] - stats2['win_rate'],
                stats1['round_diff'] - stats2['round_diff'],
                map_wr1,  # Harita win rate
                map_wr2,
                map_wr1 - map_wr2,  # Harita win rate farkı
            ]
            
            features.append(feature_vector)
            labels.append(1 if match['winner'] == 1 else 0)
        
        return np.array(features), np.array(labels)
    
    def train_models_with_metrics(self, X, y):
        """Modelleri eğit ve detaylı metrikler hesapla"""
        print("\n🤖 MODELLER EĞİTİLİYOR...")
        print("="*80)
        
        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        model_configs = {
            'logistic_regression': {
                'model': LogisticRegression(random_state=42, max_iter=1000),
                'scaled': True
            },
            'random_forest': {
                'model': RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42),
                'scaled': False
            },
            'xgboost': {
                'model': xgb.XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42, eval_metric='logloss'),
                'scaled': False
            },
            'lightgbm': {
                'model': lgb.LGBMClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42, verbose=-1),
                'scaled': False
            }
        }
        
        for name, config in model_configs.items():
            print(f"\n📊 {name.upper().replace('_', ' ')}")
            print("-"*80)
            
            model = config['model']
            use_scaled = config['scaled']
            
            # Eğit
            if use_scaled:
                model.fit(X_train_scaled, y_train)
                y_pred = model.predict(X_test_scaled)
                y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
            else:
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
                y_pred_proba = model.predict_proba(X_test)[:, 1]
            
            # Metrikler
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, zero_division=0)
            recall = recall_score(y_test, y_pred, zero_division=0)
            f1 = f1_score(y_test, y_pred, zero_division=0)
            
            try:
                auc = roc_auc_score(y_test, y_pred_proba)
            except:
                auc = 0.0
            
            # Confusion matrix
            cm = confusion_matrix(y_test, y_pred)
            
            # Cross-validation
            cv_scores = cross_val_score(model, X_train if not use_scaled else X_train_scaled, 
                                       y_train, cv=5, scoring='accuracy')
            
            # Kaydet
            self.models[name] = model
            self.model_metrics[name] = {
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'auc_roc': auc,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std(),
                'confusion_matrix': cm
            }
            
            # Yazdır
            print(f"Accuracy:  {accuracy:.4f} ({accuracy*100:.2f}%)")
            print(f"Precision: {precision:.4f} ({precision*100:.2f}%)")
            print(f"Recall:    {recall:.4f} ({recall*100:.2f}%)")
            print(f"F1-Score:  {f1:.4f} ({f1*100:.2f}%)")
            print(f"AUC-ROC:   {auc:.4f}")
            print(f"CV Score:  {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
            print(f"\nConfusion Matrix:")
            print(f"  True Negatives:  {cm[0][0]:3d} | False Positives: {cm[0][1]:3d}")
            print(f"  False Negatives: {cm[1][0]:3d} | True Positives:  {cm[1][1]:3d}")
        
        print("\n" + "="*80)
        print("✅ Tüm modeller eğitildi!")
        
        return X_train, X_test, y_train, y_test
    
    def predict_match_precise(self, team1, team2, map_name=None, verbose=True):
        """
        KESIN YÜZDE TAHMİNİ
        Örnek: %61.3 kazanma şansı (aralık değil)
        """
        if team1 not in self.team_stats or team2 not in self.team_stats:
            return {
                'error': f'Takım bulunamadı',
                'available_teams': list(self.team_stats.keys())[:20]
            }
        
        if verbose:
            print(f"\n{'='*80}")
            print(f"🎯 KESIN TAHMİN: {team1} vs {team2}")
            if map_name:
                print(f"🗺️  Harita: {map_name}")
            print(f"{'='*80}")
        
        # İstatistikler
        stats1 = self.team_stats[team1]
        stats2 = self.team_stats[team2]
        
        # Harita istatistikleri
        map_wr1 = 0
        map_wr2 = 0
        if map_name:
            if team1 in self.map_stats and map_name in self.map_stats[team1]:
                map_wr1 = self.map_stats[team1][map_name]['win_rate']
            if team2 in self.map_stats and map_name in self.map_stats[team2]:
                map_wr2 = self.map_stats[team2][map_name]['win_rate']
        
        # Özellik vektörü
        features = np.array([[
            stats1['win_rate'],
            stats2['win_rate'],
            stats1['recent_form'],
            stats2['recent_form'],
            stats1['avg_rounds_won'],
            stats2['avg_rounds_won'],
            stats1['round_diff'],
            stats2['round_diff'],
            stats1['matches_played'],
            stats2['matches_played'],
            stats1['win_rate'] - stats2['win_rate'],
            stats1['round_diff'] - stats2['round_diff'],
            map_wr1,
            map_wr2,
            map_wr1 - map_wr2,
        ]])
        
        # Her modelden tahmin al
        predictions = {}
        
        for name, model in self.models.items():
            if name == 'logistic_regression':
                features_scaled = self.scaler.transform(features)
                proba = model.predict_proba(features_scaled)[0]
            else:
                proba = model.predict_proba(features)[0]
            
            # Kesin yüzdeler
            team1_prob = proba[1] * 100  # %61.347 gibi
            team2_prob = proba[0] * 100
            
            winner = team1 if team1_prob > team2_prob else team2
            confidence = max(team1_prob, team2_prob)
            
            predictions[name] = {
                'winner': winner,
                'team1_probability': team1_prob,
                'team2_probability': team2_prob,
                'confidence': confidence
            }
        
        # Ensemble (ağırlıklı ortalama)
        # En iyi performans gösteren modellere daha fazla ağırlık ver
        weights = {}
        for name in self.models.keys():
            if name in self.model_metrics:
                # F1-score ve accuracy ortalamasını kullan
                weight = (self.model_metrics[name]['f1_score'] + self.model_metrics[name]['accuracy']) / 2
                weights[name] = weight
            else:
                weights[name] = 0.25  # Default
        
        # Normalize weights
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v/total_weight for k, v in weights.items()}
        
        # Ağırlıklı ensemble
        ensemble_team1_prob = sum(predictions[name]['team1_probability'] * weights[name] for name in predictions.keys())
        ensemble_team2_prob = sum(predictions[name]['team2_probability'] * weights[name] for name in predictions.keys())
        
        ensemble_winner = team1 if ensemble_team1_prob > ensemble_team2_prob else team2
        ensemble_confidence = max(ensemble_team1_prob, ensemble_team2_prob)
        
        # Skor tahmini (BO3 için)
        # Kazanma olasılığına göre 2-0 veya 2-1 tahmini
        if ensemble_confidence > 70:
            predicted_score = "2-0"
        elif ensemble_confidence > 60:
            predicted_score = "2-1"
        else:
            predicted_score = "2-1"  # Yakın maç
        
        if verbose:
            print(f"\n📊 TAKIM İSTATİSTİKLERİ:")
            print(f"-"*80)
            print(f"{team1:20s} - Win Rate: {stats1['win_rate']*100:.1f}% | Form: {stats1['recent_form']*100:.1f}%")
            print(f"{team2:20s} - Win Rate: {stats2['win_rate']*100:.1f}% | Form: {stats2['recent_form']*100:.1f}%")
            
            if map_name:
                print(f"\n🗺️  HARITA İSTATİSTİKLERİ ({map_name}):")
                print(f"-"*80)
                if map_wr1 > 0:
                    print(f"{team1:20s} - Map Win Rate: {map_wr1*100:.1f}%")
                else:
                    print(f"{team1:20s} - Map Win Rate: Veri yok")
                    
                if map_wr2 > 0:
                    print(f"{team2:20s} - Map Win Rate: {map_wr2*100:.1f}%")
                else:
                    print(f"{team2:20s} - Map Win Rate: Veri yok")
            
            print(f"\n🤖 MODEL TAHMİNLERİ:")
            print(f"-"*80)
            for name, pred in predictions.items():
                metrics = self.model_metrics.get(name, {})
                model_acc = metrics.get('accuracy', 0) * 100
                print(f"{name:20s} (Acc: {model_acc:.1f}%)")
                print(f"  {team1}: {pred['team1_probability']:.2f}%")
                print(f"  {team2}: {pred['team2_probability']:.2f}%")
                print(f"  Kazanan: {pred['winner']}")
            
            print(f"\n{'='*80}")
            print(f"🏆 ENSEMBLE TAHMİNİ (Ağırlıklı Ortalama):")
            print(f"{'='*80}")
            print(f"Kazanan: {ensemble_winner}")
            print(f"Tahmini Skor: {predicted_score}")
            print(f"\n{team1}: {ensemble_team1_prob:.2f}%")
            print(f"{team2}: {ensemble_team2_prob:.2f}%")
            print(f"\nGüven: {ensemble_confidence:.2f}%")
            print(f"{'='*80}")
        
        return {
            'team1': team1,
            'team2': team2,
            'map': map_name,
            'ensemble': {
                'winner': ensemble_winner,
                'predicted_score': predicted_score,
                'team1_probability': round(ensemble_team1_prob, 2),
                'team2_probability': round(ensemble_team2_prob, 2),
                'confidence': round(ensemble_confidence, 2)
            },
            'individual_models': predictions,
            'model_weights': weights
        }
    
    def get_model_performance_summary(self):
        """Model performans özetini göster"""
        print("\n" + "="*80)
        print("📊 MODEL PERFORMANS ÖZETİ")
        print("="*80)
        
        # DataFrame oluştur
        metrics_data = []
        for name, metrics in self.model_metrics.items():
            metrics_data.append({
                'Model': name.replace('_', ' ').title(),
                'Accuracy': f"{metrics['accuracy']:.4f}",
                'Precision': f"{metrics['precision']:.4f}",
                'Recall': f"{metrics['recall']:.4f}",
                'F1-Score': f"{metrics['f1_score']:.4f}",
                'AUC-ROC': f"{metrics['auc_roc']:.4f}",
                'CV Mean': f"{metrics['cv_mean']:.4f}"
            })
        
        df = pd.DataFrame(metrics_data)
        print("\n" + df.to_string(index=False))
        print("\n" + "="*80)
    
    def save_models(self, directory='models'):
        """Modelleri kaydet"""
        os.makedirs(directory, exist_ok=True)
        
        for name, model in self.models.items():
            joblib.dump(model, os.path.join(directory, f'{name}_model.pkl'))
        
        joblib.dump(self.scaler, os.path.join(directory, 'scaler.pkl'))
        joblib.dump(self.team_stats, os.path.join(directory, 'team_stats.pkl'))
        joblib.dump(self.map_stats, os.path.join(directory, 'map_stats.pkl'))
        joblib.dump(self.model_metrics, os.path.join(directory, 'model_metrics.pkl'))
        
        print(f"\n✅ Modeller {directory}/ dizinine kaydedildi")
    
    def load_models(self, directory='models'):
        """Modelleri yükle"""
        try:
            model_names = ['logistic_regression', 'random_forest', 'xgboost', 'lightgbm']
            
            for name in model_names:
                filename = os.path.join(directory, f'{name}_model.pkl')
                if os.path.exists(filename):
                    self.models[name] = joblib.load(filename)
            
            self.scaler = joblib.load(os.path.join(directory, 'scaler.pkl'))
            self.team_stats = joblib.load(os.path.join(directory, 'team_stats.pkl'))
            self.map_stats = joblib.load(os.path.join(directory, 'map_stats.pkl'))
            self.model_metrics = joblib.load(os.path.join(directory, 'model_metrics.pkl'))
            
            print(f"✅ Modeller yüklendi")
            return True
        except Exception as e:
            print(f"❌ Model yükleme hatası: {e}")
            return False


def main():
    """Test"""
    predictor = PrecisionMatchPredictor()
    
    if not predictor.load_data():
        print("Önce veri toplama gerekli")
        return
    
    predictor.calculate_team_stats(months=3)
    predictor.calculate_map_stats(months=3)
    
    X, y = predictor.create_features()
    
    if len(X) < 30:
        print("Yetersiz veri")
        return
    
    # Eğit
    predictor.train_models_with_metrics(X, y)
    
    # Performans özeti
    predictor.get_model_performance_summary()
    
    # Modelleri kaydet
    predictor.save_models()
    
    # Örnek tahmin
    teams = list(predictor.team_stats.keys())
    if len(teams) >= 2:
        result = predictor.predict_match_precise(teams[0], teams[1], verbose=True)


if __name__ == "__main__":
    main()
