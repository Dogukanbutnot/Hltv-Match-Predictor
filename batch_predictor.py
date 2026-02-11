"""
Batch Predictor for Upcoming Matches
Automatically predicts outcomes for all upcoming matches
"""

import pandas as pd
import os
from ml_predictor import MatchPredictor
from datetime import datetime


def predict_upcoming_matches(
    upcoming_file="hltv_upcoming_matches.csv",
    results_file="hltv_match_results.csv",
    output_file="predictions.csv"
):
    """
    Predict outcomes for all upcoming matches
    """
    print("🔮 BATCH MATCH PREDICTION SYSTEM")
    print("=" * 80)
    
    # Check if files exist
    if not os.path.exists(upcoming_file):
        print(f"❌ Upcoming matches file not found: {upcoming_file}")
        print("   Run 'python hltv_scraper.py' first to scrape upcoming matches")
        return
    
    if not os.path.exists(results_file):
        print(f"❌ Results file not found: {results_file}")
        print("   Run 'python hltv_scraper.py' first to scrape match results")
        return
    
    # Initialize predictor
    predictor = MatchPredictor(results_file)
    
    # Try to load existing models
    if os.path.exists('models'):
        print("\n📦 Loading pre-trained models...")
        if predictor.load_models():
            print("✅ Models loaded successfully")
        else:
            print("⚠️  Could not load models, training new ones...")
            train_models(predictor)
    else:
        print("\n🤖 No pre-trained models found, training new ones...")
        train_models(predictor)
    
    # Load upcoming matches
    upcoming_df = pd.read_csv(upcoming_file)
    print(f"\n📋 Found {len(upcoming_df)} upcoming matches")
    
    if upcoming_df.empty:
        print("No upcoming matches to predict")
        return
    
    # Make predictions
    predictions = []
    
    print("\n🔮 Generating predictions...\n")
    print("-" * 80)
    
    for idx, match in upcoming_df.iterrows():
        team1 = match['team_1']
        team2 = match['team_2']
        event = match.get('event', 'Unknown')
        match_time = match.get('match_time', 'TBD')
        
        print(f"\n{idx + 1}. {team1} vs {team2}")
        print(f"   Event: {event}")
        print(f"   Time: {match_time}")
        
        # Get predictions from all models
        all_preds = predictor.predict_all_models(team1, team2)
        
        if not all_preds:
            print("   ⚠️  No predictions available (teams not in database)")
            continue
        
        # Calculate consensus
        winners = [p['winner'] for p in all_preds.values()]
        consensus_winner = max(set(winners), key=winners.count)
        consensus_count = winners.count(consensus_winner)
        confidence_level = f"{consensus_count}/{len(all_preds)}"
        
        print(f"   🏆 CONSENSUS: {consensus_winner} ({confidence_level} models agree)")
        
        # Display each model's prediction
        for model_name, pred in all_preds.items():
            emoji = "✅" if pred['winner'] == consensus_winner else "❌"
            print(f"   {emoji} {model_name:20s}: {pred['winner']:15s} ({pred['confidence']})")
        
        # Store prediction
        prediction_record = {
            'match_id': idx + 1,
            'team_1': team1,
            'team_2': team2,
            'event': event,
            'match_time': match_time,
            'consensus_winner': consensus_winner,
            'consensus_strength': confidence_level,
            'prediction_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Add individual model predictions
        for model_name, pred in all_preds.items():
            prediction_record[f'{model_name}_winner'] = pred['winner']
            prediction_record[f'{model_name}_confidence'] = pred['confidence']
            prediction_record[f'{model_name}_team1_prob'] = pred['team1_prob']
            prediction_record[f'{model_name}_team2_prob'] = pred['team2_prob']
        
        predictions.append(prediction_record)
    
    # Save predictions
    if predictions:
        predictions_df = pd.DataFrame(predictions)
        predictions_df.to_csv(output_file, index=False)
        print("\n" + "=" * 80)
        print(f"✅ Predictions saved to {output_file}")
        print(f"📊 Total predictions: {len(predictions)}")
        
        # Summary
        print("\n📈 PREDICTION SUMMARY:")
        print("-" * 80)
        consensus_winners = predictions_df['consensus_winner'].value_counts()
        for team, count in consensus_winners.items():
            print(f"   {team}: {count} predicted wins")
    else:
        print("\n⚠️  No predictions could be generated")


def train_models(predictor):
    """Helper function to train models"""
    if not predictor.load_data():
        return False
    
    predictor.calculate_team_stats()
    X, y = predictor.create_features()
    
    if len(X) < 30:
        print("\n⚠️  Warning: Not enough data for reliable predictions")
        return False
    
    predictor.train_models(X, y)
    predictor.save_models()
    return True


def compare_with_actual_results(
    predictions_file="predictions.csv",
    results_file="hltv_match_results.csv"
):
    """
    Compare predictions with actual results (run after matches are complete)
    """
    print("\n📊 PREDICTION ACCURACY CHECKER")
    print("=" * 80)
    
    if not os.path.exists(predictions_file):
        print(f"❌ Predictions file not found: {predictions_file}")
        return
    
    if not os.path.exists(results_file):
        print(f"❌ Results file not found: {results_file}")
        return
    
    predictions_df = pd.read_csv(predictions_file)
    results_df = pd.read_csv(results_file)
    
    print(f"\n📋 Loaded {len(predictions_df)} predictions")
    print(f"📋 Loaded {len(results_df)} results")
    
    matches_found = 0
    consensus_correct = 0
    model_accuracy = {
        'logistic_regression': {'correct': 0, 'total': 0},
        'random_forest': {'correct': 0, 'total': 0},
        'xgboost': {'correct': 0, 'total': 0},
        'lightgbm': {'correct': 0, 'total': 0}
    }
    
    for _, pred in predictions_df.iterrows():
        team1 = pred['team_1']
        team2 = pred['team_2']
        
        # Find matching result
        result = results_df[
            ((results_df['team_1'] == team1) & (results_df['team_2'] == team2)) |
            ((results_df['team_1'] == team2) & (results_df['team_2'] == team1))
        ]
        
        if result.empty:
            continue
        
        matches_found += 1
        result = result.iloc[0]
        
        # Determine actual winner
        if result['team_1'] == team1:
            actual_winner = team1 if result['winner'] == 1 else team2
        else:
            actual_winner = team2 if result['winner'] == 1 else team1
        
        # Check consensus
        if pred['consensus_winner'] == actual_winner:
            consensus_correct += 1
            status = "✅"
        else:
            status = "❌"
        
        print(f"\n{status} {team1} vs {team2}")
        print(f"   Predicted: {pred['consensus_winner']}")
        print(f"   Actual: {actual_winner}")
        
        # Check individual models
        for model_name in model_accuracy.keys():
            col_name = f'{model_name}_winner'
            if col_name in pred:
                model_accuracy[model_name]['total'] += 1
                if pred[col_name] == actual_winner:
                    model_accuracy[model_name]['correct'] += 1
    
    if matches_found > 0:
        print("\n" + "=" * 80)
        print("📊 ACCURACY RESULTS:")
        print("-" * 80)
        
        consensus_acc = (consensus_correct / matches_found) * 100
        print(f"\n🎯 Consensus Accuracy: {consensus_correct}/{matches_found} = {consensus_acc:.2f}%")
        
        print("\n📈 Individual Model Accuracy:")
        for model_name, stats in model_accuracy.items():
            if stats['total'] > 0:
                acc = (stats['correct'] / stats['total']) * 100
                print(f"   {model_name:20s}: {stats['correct']}/{stats['total']} = {acc:.2f}%")
    else:
        print("\n⚠️  No matches found to compare")


def main():
    """Main execution"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--check-accuracy':
        compare_with_actual_results()
    else:
        predict_upcoming_matches()


if __name__ == "__main__":
    main()
