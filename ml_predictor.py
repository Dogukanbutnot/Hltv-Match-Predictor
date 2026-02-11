"""
HLTV Match Prediction Models
Implements multiple ML models to predict CS:GO match outcomes
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, roc_auc_score
import xgboost as xgb
import lightgbm as lgb
import joblib
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class MatchPredictor:
    """ML-based match outcome predictor"""
    
    def __init__(self, results_file="hltv_match_results.csv"):
        self.results_file = results_file
        self.df = None
        self.models = {}
        self.scaler = StandardScaler()
        self.team_encoder = LabelEncoder()
        self.team_stats = {}
        
    def load_data(self):
        """Load and validate match data"""
        if not os.path.exists(self.results_file):
            print(f"❌ File not found: {self.results_file}")
            return False
        
        self.df = pd.read_csv(self.results_file)
        print(f"✅ Loaded {len(self.df)} matches")
        
        # Remove matches without valid scores
        self.df = self.df[
            (self.df['score_1'] != 'N/A') & 
            (self.df['score_2'] != 'N/A')
        ].copy()
        
        # Convert scores to numeric
        self.df['score_1'] = pd.to_numeric(self.df['score_1'], errors='coerce')
        self.df['score_2'] = pd.to_numeric(self.df['score_2'], errors='coerce')
        
        # Remove any rows with NaN scores
        self.df = self.df.dropna(subset=['score_1', 'score_2'])
        
        print(f"✅ {len(self.df)} matches with valid scores")
        
        if len(self.df) < 50:
            print("⚠️  Warning: Less than 50 matches. More data recommended for accurate predictions.")
        
        return True
    
    def calculate_team_stats(self):
        """Calculate historical statistics for each team"""
        print("📊 Calculating team statistics...")
        
        teams = set(list(self.df['team_1']) + list(self.df['team_2']))
        
        for team in teams:
            # Find all matches for this team
            team_matches = self.df[
                (self.df['team_1'] == team) | (self.df['team_2'] == team)
            ]
            
            wins = 0
            total_rounds_won = 0
            total_rounds_lost = 0
            matches_played = len(team_matches)
            
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
            
            win_rate = wins / matches_played if matches_played > 0 else 0
            avg_rounds_won = total_rounds_won / matches_played if matches_played > 0 else 0
            avg_rounds_lost = total_rounds_lost / matches_played if matches_played > 0 else 0
            round_diff = avg_rounds_won - avg_rounds_lost
            
            self.team_stats[team] = {
                'matches_played': matches_played,
                'wins': wins,
                'win_rate': win_rate,
                'avg_rounds_won': avg_rounds_won,
                'avg_rounds_lost': avg_rounds_lost,
                'round_diff': round_diff
            }
        
        print(f"✅ Calculated stats for {len(self.team_stats)} teams")
    
    def create_features(self):
        """Create features for ML models"""
        print("🔧 Creating features...")
        
        features = []
        labels = []
        
        for idx, match in self.df.iterrows():
            team1 = match['team_1']
            team2 = match['team_2']
            
            # Skip if teams don't have stats
            if team1 not in self.team_stats or team2 not in self.team_stats:
                continue
            
            stats1 = self.team_stats[team1]
            stats2 = self.team_stats[team2]
            
            # Create feature vector
            feature_vector = [
                stats1['win_rate'],
                stats2['win_rate'],
                stats1['avg_rounds_won'],
                stats2['avg_rounds_won'],
                stats1['avg_rounds_lost'],
                stats2['avg_rounds_lost'],
                stats1['round_diff'],
                stats2['round_diff'],
                stats1['matches_played'],
                stats2['matches_played'],
                stats1['win_rate'] - stats2['win_rate'],  # Win rate difference
                stats1['round_diff'] - stats2['round_diff'],  # Round diff difference
            ]
            
            features.append(feature_vector)
            
            # Label: 1 if team1 wins, 0 if team2 wins
            label = 1 if match['winner'] == 1 else 0
            labels.append(label)
        
        X = np.array(features)
        y = np.array(labels)
        
        print(f"✅ Created {len(X)} feature vectors with {X.shape[1]} features each")
        
        return X, y
    
    def train_models(self, X, y):
        """Train multiple ML models"""
        print("\n🤖 Training models...")
        print("=" * 60)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # 1. Logistic Regression
        print("\n📈 Training Logistic Regression...")
        lr = LogisticRegression(random_state=42, max_iter=1000)
        lr.fit(X_train_scaled, y_train)
        self.models['logistic_regression'] = lr
        self._evaluate_model(lr, X_test_scaled, y_test, "Logistic Regression")
        
        # 2. Random Forest
        print("\n🌲 Training Random Forest...")
        rf = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        rf.fit(X_train, y_train)
        self.models['random_forest'] = rf
        self._evaluate_model(rf, X_test, y_test, "Random Forest")
        
        # 3. XGBoost
        print("\n⚡ Training XGBoost...")
        xgb_model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            eval_metric='logloss'
        )
        xgb_model.fit(X_train, y_train)
        self.models['xgboost'] = xgb_model
        self._evaluate_model(xgb_model, X_test, y_test, "XGBoost")
        
        # 4. LightGBM
        print("\n💡 Training LightGBM...")
        lgb_model = lgb.LGBMClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            verbose=-1
        )
        lgb_model.fit(X_train, y_train)
        self.models['lightgbm'] = lgb_model
        self._evaluate_model(lgb_model, X_test, y_test, "LightGBM")
        
        print("\n" + "=" * 60)
        print("✅ All models trained successfully!")
        
        return X_train, X_test, y_train, y_test
    
    def _evaluate_model(self, model, X_test, y_test, model_name):
        """Evaluate a single model"""
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        accuracy = accuracy_score(y_test, y_pred)
        
        try:
            auc = roc_auc_score(y_test, y_pred_proba)
        except:
            auc = 0.0
        
        print(f"\n{model_name} Results:")
        print(f"  Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
        print(f"  AUC-ROC: {auc:.4f}")
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        print(f"  Confusion Matrix:")
        print(f"    Team 1 Wins Predicted: {cm[1][1]} correct, {cm[1][0]} wrong")
        print(f"    Team 2 Wins Predicted: {cm[0][0]} correct, {cm[0][1]} wrong")
    
    def predict_match(self, team1, team2, model_name='xgboost'):
        """Predict outcome of a specific match"""
        if team1 not in self.team_stats or team2 not in self.team_stats:
            return {
                'error': f'Team statistics not available for {team1} or {team2}',
                'available_teams': list(self.team_stats.keys())[:20]
            }
        
        if model_name not in self.models:
            return {
                'error': f'Model {model_name} not found',
                'available_models': list(self.models.keys())
            }
        
        # Get team stats
        stats1 = self.team_stats[team1]
        stats2 = self.team_stats[team2]
        
        # Create feature vector
        features = np.array([[
            stats1['win_rate'],
            stats2['win_rate'],
            stats1['avg_rounds_won'],
            stats2['avg_rounds_won'],
            stats1['avg_rounds_lost'],
            stats2['avg_rounds_lost'],
            stats1['round_diff'],
            stats2['round_diff'],
            stats1['matches_played'],
            stats2['matches_played'],
            stats1['win_rate'] - stats2['win_rate'],
            stats1['round_diff'] - stats2['round_diff'],
        ]])
        
        # Scale features for logistic regression
        if model_name == 'logistic_regression':
            features = self.scaler.transform(features)
        
        # Get model and predict
        model = self.models[model_name]
        prediction = model.predict(features)[0]
        proba = model.predict_proba(features)[0]
        
        winner = team1 if prediction == 1 else team2
        confidence = proba[1] if prediction == 1 else proba[0]
        
        return {
            'team1': team1,
            'team2': team2,
            'predicted_winner': winner,
            'confidence': f"{confidence*100:.2f}%",
            'team1_win_probability': f"{proba[1]*100:.2f}%",
            'team2_win_probability': f"{proba[0]*100:.2f}%",
            'model_used': model_name,
            'team1_stats': stats1,
            'team2_stats': stats2
        }
    
    def predict_all_models(self, team1, team2):
        """Get predictions from all models"""
        predictions = {}
        
        for model_name in self.models.keys():
            pred = self.predict_match(team1, team2, model_name)
            if 'error' not in pred:
                predictions[model_name] = {
                    'winner': pred['predicted_winner'],
                    'confidence': pred['confidence'],
                    'team1_prob': pred['team1_win_probability'],
                    'team2_prob': pred['team2_win_probability']
                }
        
        return predictions
    
    def save_models(self, directory='models'):
        """Save trained models to disk"""
        os.makedirs(directory, exist_ok=True)
        
        # Save models
        for name, model in self.models.items():
            filename = os.path.join(directory, f'{name}_model.pkl')
            joblib.dump(model, filename)
            print(f"✅ Saved {name} to {filename}")
        
        # Save scaler
        joblib.dump(self.scaler, os.path.join(directory, 'scaler.pkl'))
        
        # Save team stats
        joblib.dump(self.team_stats, os.path.join(directory, 'team_stats.pkl'))
        
        print(f"\n✅ All models saved to {directory}/")
    
    def load_models(self, directory='models'):
        """Load trained models from disk"""
        try:
            model_names = ['logistic_regression', 'random_forest', 'xgboost', 'lightgbm']
            
            for name in model_names:
                filename = os.path.join(directory, f'{name}_model.pkl')
                if os.path.exists(filename):
                    self.models[name] = joblib.load(filename)
                    print(f"✅ Loaded {name}")
            
            # Load scaler
            self.scaler = joblib.load(os.path.join(directory, 'scaler.pkl'))
            
            # Load team stats
            self.team_stats = joblib.load(os.path.join(directory, 'team_stats.pkl'))
            
            print(f"✅ All models loaded from {directory}/")
            return True
            
        except Exception as e:
            print(f"❌ Error loading models: {e}")
            return False
    
    def get_feature_importance(self, model_name='random_forest'):
        """Get feature importance for tree-based models"""
        if model_name not in ['random_forest', 'xgboost', 'lightgbm']:
            print("Feature importance only available for tree-based models")
            return None
        
        model = self.models.get(model_name)
        if not model:
            print(f"Model {model_name} not found")
            return None
        
        feature_names = [
            'team1_win_rate', 'team2_win_rate',
            'team1_avg_rounds_won', 'team2_avg_rounds_won',
            'team1_avg_rounds_lost', 'team2_avg_rounds_lost',
            'team1_round_diff', 'team2_round_diff',
            'team1_matches', 'team2_matches',
            'win_rate_diff', 'round_diff_diff'
        ]
        
        importance = model.feature_importances_
        feature_importance = pd.DataFrame({
            'feature': feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)
        
        return feature_importance


def main():
    """Main training and prediction pipeline"""
    print("🎮 HLTV Match Prediction System")
    print("=" * 60)
    
    predictor = MatchPredictor()
    
    # Load data
    if not predictor.load_data():
        return
    
    # Calculate team statistics
    predictor.calculate_team_stats()
    
    # Create features
    X, y = predictor.create_features()
    
    if len(X) < 30:
        print("\n⚠️  Warning: Not enough data for reliable predictions")
        print("   Collect more match results and try again.")
        return
    
    # Train models
    X_train, X_test, y_train, y_test = predictor.train_models(X, y)
    
    # Save models
    predictor.save_models()
    
    # Feature importance
    print("\n📊 Feature Importance (Random Forest):")
    importance = predictor.get_feature_importance('random_forest')
    if importance is not None:
        print(importance.to_string(index=False))
    
    # Example prediction
    print("\n\n🔮 EXAMPLE PREDICTIONS")
    print("=" * 60)
    
    # Get some teams for demo
    teams = list(predictor.team_stats.keys())
    if len(teams) >= 2:
        team1, team2 = teams[0], teams[1]
        
        print(f"\nPredicting: {team1} vs {team2}")
        print("-" * 60)
        
        all_predictions = predictor.predict_all_models(team1, team2)
        
        for model_name, pred in all_predictions.items():
            print(f"\n{model_name.upper().replace('_', ' ')}:")
            print(f"  Winner: {pred['winner']}")
            print(f"  Confidence: {pred['confidence']}")
            print(f"  {team1}: {pred['team1_prob']}")
            print(f"  {team2}: {pred['team2_prob']}")
    
    # Interactive prediction
    print("\n\n🎯 INTERACTIVE PREDICTION")
    print("=" * 60)
    print(f"Available teams: {', '.join(teams[:10])}{'...' if len(teams) > 10 else ''}")
    
    team1 = input("\nEnter Team 1 name (or press Enter to skip): ").strip()
    if team1:
        team2 = input("Enter Team 2 name: ").strip()
        
        if team2:
            print(f"\n🔮 Predictions for {team1} vs {team2}:")
            print("-" * 60)
            
            all_predictions = predictor.predict_all_models(team1, team2)
            
            if all_predictions:
                for model_name, pred in all_predictions.items():
                    print(f"\n{model_name.upper().replace('_', ' ')}:")
                    print(f"  🏆 Winner: {pred['winner']}")
                    print(f"  📊 Confidence: {pred['confidence']}")
            else:
                print("❌ Could not generate predictions. Check team names.")


if __name__ == "__main__":
    main()
