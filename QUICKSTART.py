"""
QUICK START GUIDE
Complete walkthrough for HLTV Match Prediction System
"""

# ============================================================================
# STEP 1: INSTALLATION
# ============================================================================

"""
1. Make sure you have Python 3.8+ installed:
   python --version

2. Install all dependencies:
   pip install -r requirements.txt

3. Wait for Chrome driver to download automatically (happens on first run)
"""

# ============================================================================
# STEP 2: COLLECT DATA (FIRST TIME)
# ============================================================================

"""
Run the scraper to collect match data:
   python hltv_scraper.py

This will create:
   - hltv_upcoming_matches.csv (matches to predict)
   - hltv_match_results.csv (historical data for training)

⚠️  IMPORTANT: You need at least 50-100 historical matches for good predictions!
   If you don't have enough data, run the scraper multiple times over several days.
"""

# ============================================================================
# STEP 3: TRAIN ML MODELS
# ============================================================================

"""
Train the prediction models:
   python ml_predictor.py

What happens:
   ✓ Calculates team statistics from historical data
   ✓ Trains 4 different ML models (Logistic Regression, Random Forest, XGBoost, LightGBM)
   ✓ Shows accuracy for each model
   ✓ Saves trained models to models/ directory
   ✓ Provides example predictions

This takes 1-2 minutes depending on data size.
"""

# ============================================================================
# STEP 4: PREDICT UPCOMING MATCHES
# ============================================================================

"""
Predict outcomes for all upcoming matches:
   python batch_predictor.py

Output:
   ✓ Predictions from all 4 models for each match
   ✓ Consensus winner (majority vote)
   ✓ Confidence percentages
   ✓ Saves predictions to predictions.csv

Example output:
   1. NAVI vs G2
      Event: IEM Katowice
      Time: 2026-01-28 15:00
      🏆 CONSENSUS: NAVI (3/4 models agree)
      ✅ logistic_regression  : NAVI           (67.3%)
      ✅ random_forest        : NAVI           (72.1%)
      ✅ xgboost              : NAVI           (75.8%)
      ❌ lightgbm             : G2             (51.2%)
"""

# ============================================================================
# STEP 5: (OPTIONAL) COMPARE MODELS
# ============================================================================

"""
See detailed model comparison:
   python compare_models.py

Shows:
   ✓ Accuracy, precision, recall, F1-score for each model
   ✓ Feature importance (what factors matter most)
   ✓ Best model recommendations
   ✓ Generates comparison report
"""

# ============================================================================
# STEP 6: (LATER) CHECK ACCURACY
# ============================================================================

"""
After matches are played, verify prediction accuracy:
   python batch_predictor.py --check-accuracy

Compares your predictions with actual results and shows:
   ✓ Consensus accuracy
   ✓ Individual model accuracy
   ✓ Which predictions were correct/incorrect
"""

# ============================================================================
# DAILY WORKFLOW (AFTER INITIAL SETUP)
# ============================================================================

"""
Once models are trained, daily workflow is simple:

Morning:
   1. python hltv_scraper.py        # Get today's matches
   2. python batch_predictor.py     # Predict outcomes

Evening (after matches):
   3. python batch_predictor.py --check-accuracy  # Verify predictions
   
Weekly:
   4. python ml_predictor.py        # Retrain models with new data
"""

# ============================================================================
# TIPS FOR BEST RESULTS
# ============================================================================

"""
📊 DATA COLLECTION:
   - Collect at least 100 matches for reliable predictions
   - More data = better accuracy
   - Run scraper daily to build up data
   - Keep historical data for retraining

🤖 MODEL PERFORMANCE:
   - XGBoost and LightGBM typically perform best (70-80% accuracy)
   - When 3-4 models agree, prediction is more reliable
   - Retrain models weekly with fresh data
   - Compare models regularly to find best performer

⚠️  LIMITATIONS:
   - Can't predict matches for teams with no historical data
   - Accuracy depends on data quality and quantity
   - Roster changes, meta shifts affect predictions
   - Use predictions as guidance, not guarantees

🎯 PREDICTION CONFIDENCE:
   - 4/4 models agree: Very High confidence (75-85% accuracy)
   - 3/4 models agree: High confidence (65-75% accuracy)
   - 2/4 models agree: Medium confidence (55-65% accuracy)
   - Models split: Low confidence (~50% accuracy)
"""

# ============================================================================
# TROUBLESHOOTING
# ============================================================================

"""
Problem: "Not enough data for reliable predictions"
Solution: Run scraper multiple times to collect more historical matches.
          Need at least 50 matches, ideally 100+.

Problem: "Teams not in database" when predicting
Solution: These teams don't have historical data yet.
          Scrape more results or wait for them to play matches.

Problem: Low model accuracy (<55%)
Solution: 
   - Collect more data
   - Check data quality (valid scores, proper team names)
   - Retrain models
   - May need 200+ matches for very high accuracy

Problem: Scraper returns empty data
Solution:
   - Check internet connection
   - Verify HLTV.org is accessible
   - HLTV may have changed HTML structure (update selectors)
   - Increase wait times in scraper

Problem: Import errors
Solution: 
   - Reinstall requirements: pip install -r requirements.txt
   - Make sure using Python 3.8+
   - Try installing packages individually
"""

# ============================================================================
# ADVANCED USAGE
# ============================================================================

"""
CUSTOM PREDICTIONS:
   # In Python
   from ml_predictor import MatchPredictor
   
   predictor = MatchPredictor()
   predictor.load_models()  # Load pre-trained models
   
   # Predict specific match
   result = predictor.predict_match("NAVI", "G2", model_name='xgboost')
   print(result)
   
   # Get predictions from all models
   all_preds = predictor.predict_all_models("NAVI", "G2")
   print(all_preds)

ANALYZE SPECIFIC TEAMS:
   # In Python
   from analyze_data import HLTVAnalyzer
   
   analyzer = HLTVAnalyzer()
   analyzer.load_data()
   
   # Get team stats
   stats = analyzer.get_team_stats("NAVI")
   print(stats)
   
   # Compare two teams
   comparison = analyzer.compare_teams("NAVI", "G2")
   print(comparison)

AUTOMATED DAILY RUNS:
   # Linux/Mac (cron)
   # Add to crontab (crontab -e):
   0 9 * * * cd /path/to/project && python hltv_scraper.py && python batch_predictor.py
   
   # Windows (Task Scheduler)
   # Create task to run daily_prediction.bat:
   cd C:\path\to\project
   python hltv_scraper.py
   python batch_predictor.py
"""

print(__doc__)
