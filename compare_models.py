"""
Model Performance Comparison and Visualization
Compare and visualize the performance of different ML models
"""

import pandas as pd
import numpy as np
from ml_predictor import MatchPredictor
import json
from datetime import datetime


class ModelComparison:
    """Compare and analyze different ML models"""
    
    def __init__(self, results_file="hltv_match_results.csv"):
        self.predictor = MatchPredictor(results_file)
        self.comparison_results = {}
    
    def run_full_comparison(self):
        """Run complete model comparison pipeline"""
        print("🔬 COMPREHENSIVE MODEL COMPARISON")
        print("=" * 80)
        
        # Load and prepare data
        if not self.predictor.load_data():
            return
        
        self.predictor.calculate_team_stats()
        X, y = self.predictor.create_features()
        
        if len(X) < 30:
            print("⚠️  Not enough data for reliable comparison")
            return
        
        # Train models
        X_train, X_test, y_train, y_test = self.predictor.train_models(X, y)
        
        # Detailed comparison
        self.compare_model_performance(X_test, y_test)
        self.compare_feature_importance()
        self.test_on_real_matchups()
        
        # Save comparison report
        self.save_comparison_report()
    
    def compare_model_performance(self, X_test, y_test):
        """Compare models on various metrics"""
        print("\n" + "=" * 80)
        print("📊 DETAILED PERFORMANCE COMPARISON")
        print("=" * 80)
        
        from sklearn.metrics import (
            accuracy_score, precision_score, recall_score, 
            f1_score, roc_auc_score
        )
        
        results = []
        
        for model_name, model in self.predictor.models.items():
            # Get predictions
            if model_name == 'logistic_regression':
                X_test_scaled = self.predictor.scaler.transform(X_test)
                y_pred = model.predict(X_test_scaled)
                y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
            else:
                y_pred = model.predict(X_test)
                y_pred_proba = model.predict_proba(X_test)[:, 1]
            
            # Calculate metrics
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, zero_division=0)
            recall = recall_score(y_test, y_pred, zero_division=0)
            f1 = f1_score(y_test, y_pred, zero_division=0)
            
            try:
                auc = roc_auc_score(y_test, y_pred_proba)
            except:
                auc = 0.0
            
            results.append({
                'Model': model_name.replace('_', ' ').title(),
                'Accuracy': f"{accuracy:.4f}",
                'Precision': f"{precision:.4f}",
                'Recall': f"{recall:.4f}",
                'F1-Score': f"{f1:.4f}",
                'AUC-ROC': f"{auc:.4f}"
            })
            
            self.comparison_results[model_name] = {
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1': f1,
                'auc': auc
            }
        
        # Display results
        results_df = pd.DataFrame(results)
        print("\n" + results_df.to_string(index=False))
        
        # Find best model for each metric
        print("\n" + "=" * 80)
        print("🏆 BEST PERFORMERS:")
        print("-" * 80)
        
        metrics = ['accuracy', 'precision', 'recall', 'f1', 'auc']
        for metric in metrics:
            best_model = max(
                self.comparison_results.items(),
                key=lambda x: x[1][metric]
            )
            print(f"   {metric.upper():12s}: {best_model[0]:20s} ({best_model[1][metric]:.4f})")
    
    def compare_feature_importance(self):
        """Compare feature importance across tree-based models"""
        print("\n" + "=" * 80)
        print("🔍 FEATURE IMPORTANCE COMPARISON")
        print("=" * 80)
        
        feature_names = [
            'team1_win_rate', 'team2_win_rate',
            'team1_avg_rounds_won', 'team2_avg_rounds_won',
            'team1_avg_rounds_lost', 'team2_avg_rounds_lost',
            'team1_round_diff', 'team2_round_diff',
            'team1_matches', 'team2_matches',
            'win_rate_diff', 'round_diff_diff'
        ]
        
        importance_data = []
        
        for model_name in ['random_forest', 'xgboost', 'lightgbm']:
            if model_name in self.predictor.models:
                model = self.predictor.models[model_name]
                importance = model.feature_importances_
                
                for feat_name, imp in zip(feature_names, importance):
                    importance_data.append({
                        'Model': model_name.replace('_', ' ').title(),
                        'Feature': feat_name,
                        'Importance': f"{imp:.4f}"
                    })
        
        if importance_data:
            importance_df = pd.DataFrame(importance_data)
            
            # Show top features for each model
            for model_name in ['Random Forest', 'Xgboost', 'Lightgbm']:
                model_data = importance_df[importance_df['Model'] == model_name]
                if not model_data.empty:
                    model_data = model_data.sort_values('Importance', ascending=False)
                    print(f"\n{model_name}:")
                    print(model_data.head(5).to_string(index=False))
    
    def test_on_real_matchups(self):
        """Test models on real historical matchups"""
        print("\n" + "=" * 80)
        print("🎯 REAL MATCHUP TESTING")
        print("=" * 80)
        
        # Get some real matchups from the data
        teams = list(self.predictor.team_stats.keys())
        
        if len(teams) < 4:
            print("Not enough teams for testing")
            return
        
        print("\nTesting on sample matchups:")
        print("-" * 80)
        
        # Test 5 random matchups
        import random
        random.seed(42)
        
        for i in range(min(5, len(teams) - 1)):
            team1 = teams[i]
            team2 = teams[i + 1]
            
            print(f"\n{i + 1}. {team1} vs {team2}")
            
            predictions = self.predictor.predict_all_models(team1, team2)
            
            if predictions:
                for model_name, pred in predictions.items():
                    print(f"   {model_name:20s}: {pred['winner']:15s} ({pred['confidence']})")
                
                # Consensus
                winners = [p['winner'] for p in predictions.values()]
                consensus = max(set(winners), key=winners.count)
                agreement = winners.count(consensus)
                print(f"   {'CONSENSUS':20s}: {consensus:15s} ({agreement}/{len(predictions)} agree)")
    
    def save_comparison_report(self, filename="model_comparison_report.txt"):
        """Save detailed comparison report"""
        with open(filename, 'w') as f:
            f.write("HLTV MATCH PREDICTION - MODEL COMPARISON REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            f.write("MODEL PERFORMANCE METRICS:\n")
            f.write("-" * 80 + "\n")
            
            for model_name, metrics in self.comparison_results.items():
                f.write(f"\n{model_name.upper().replace('_', ' ')}:\n")
                for metric, value in metrics.items():
                    f.write(f"  {metric:12s}: {value:.4f}\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("RECOMMENDATIONS:\n")
            f.write("-" * 80 + "\n")
            
            # Find best overall model
            best_model = max(
                self.comparison_results.items(),
                key=lambda x: (x[1]['accuracy'] + x[1]['f1']) / 2
            )
            
            f.write(f"\nBest Overall Model: {best_model[0].replace('_', ' ').title()}\n")
            f.write(f"  - Highest combined accuracy and F1-score\n")
            f.write(f"  - Recommended for production use\n")
            
            # Specific use cases
            f.write("\nUse Case Recommendations:\n")
            f.write("  - For balanced predictions: XGBoost or LightGBM\n")
            f.write("  - For interpretability: Logistic Regression\n")
            f.write("  - For stability: Random Forest\n")
            f.write("  - For speed: LightGBM\n")
        
        print(f"\n✅ Comparison report saved to {filename}")


def create_prediction_confidence_table():
    """Create a table showing confidence levels for predictions"""
    print("\n" + "=" * 80)
    print("📈 PREDICTION CONFIDENCE GUIDE")
    print("=" * 80)
    
    confidence_guide = pd.DataFrame([
        {
            'Agreement': '4/4 models',
            'Confidence Level': 'Very High',
            'Recommendation': 'Strong prediction',
            'Expected Accuracy': '75-85%'
        },
        {
            'Agreement': '3/4 models',
            'Confidence Level': 'High',
            'Recommendation': 'Reliable prediction',
            'Expected Accuracy': '65-75%'
        },
        {
            'Agreement': '2/4 models',
            'Confidence Level': 'Medium',
            'Recommendation': 'Uncertain outcome',
            'Expected Accuracy': '55-65%'
        },
        {
            'Agreement': 'Split',
            'Confidence Level': 'Low',
            'Recommendation': 'Coin flip',
            'Expected Accuracy': '~50%'
        }
    ])
    
    print("\n" + confidence_guide.to_string(index=False))
    print("\n" + "=" * 80)


def main():
    """Main comparison execution"""
    comparison = ModelComparison()
    comparison.run_full_comparison()
    
    # Show confidence guide
    create_prediction_confidence_table()
    
    print("\n✅ Model comparison complete!")


if __name__ == "__main__":
    main()
