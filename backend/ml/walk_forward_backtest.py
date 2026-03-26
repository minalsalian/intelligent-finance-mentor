import pandas as pd
import numpy as np
import yfinance as yf
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from feature_engineering import add_features
from data_collection import fetch_multiple_stocks
import pickle
from datetime import datetime

print("=" * 70)
print("WALK-FORWARD BACKTESTING (Professional Validation)")
print("=" * 70)

symbols = ["AAPL", "MSFT", "GOOGL", "AMZN"]

# Fetch long-term data
print("\n📊 Fetching 3-year data for walk-forward test...")
df_all = fetch_multiple_stocks(symbols=symbols, period="3y")

if df_all is None or df_all.empty:
    print("❌ Failed to fetch data")
    exit(1)

df_all = add_features(df_all)

feature_cols = [
    "EMA_10", "EMA_20", "MA_5", "MA_10", "MA_20",
    "RSI", "Body", "High_Low_Range", "Volume",
    "MACD", "MACD_Signal", "ATR", "Momentum", "Volume_Change"
]

# Add Date column if not present
if 'Date' not in df_all.columns:
    df_all.reset_index(inplace=True)

df_all = df_all.sort_values('Date').reset_index(drop=True)

print(f"Total samples: {len(df_all)}")
print(f"Date range: {df_all['Date'].min()} to {df_all['Date'].max()}\n")

# Walk-forward windows
windows = [
    ("2023-01-01", "2023-12-31", "2024-01-01", "2024-06-30"),  # Train 2023, Test H1 2024
    ("2023-06-01", "2024-05-31", "2024-06-01", "2024-12-31"),  # Train mid-2023 to mid-2024, Test H2 2024
    ("2024-01-01", "2024-09-30", "2024-10-01", "2025-03-31"),  # Train 2024, Test Q4 2024-Q1 2025
]

results = []

for i, (train_start, train_end, test_start, test_end) in enumerate(windows, 1):
    print(f"\n{'='*70}")
    print(f"WINDOW {i}: Train [{train_start} to {train_end}] → Test [{test_start} to {test_end}]")
    print(f"{'='*70}")
    
    try:
        # Split data
        train_mask = (df_all['Date'] >= train_start) & (df_all['Date'] <= train_end)
        test_mask = (df_all['Date'] >= test_start) & (df_all['Date'] <= test_end)
        
        df_train = df_all[train_mask].copy()
        df_test = df_all[test_mask].copy()
        
        if len(df_train) < 50 or len(df_test) < 10:
            print(f"⚠️  Insufficient data: train={len(df_train)}, test={len(df_test)}")
            continue
        
        X_train = df_train[feature_cols].copy()
        y_train = df_train["Target"].copy()
        X_test = df_test[feature_cols].copy()
        y_test = df_test["Target"].copy()
        
        # Remove NaN
        train_valid = X_train.notna().all(axis=1) & y_train.notna()
        X_train = X_train[train_valid].reset_index(drop=True)
        y_train = y_train[train_valid].reset_index(drop=True)
        
        test_valid = X_test.notna().all(axis=1) & y_test.notna()
        X_test = X_test[test_valid].reset_index(drop=True)
        y_test = y_test[test_valid].reset_index(drop=True)
        
        print(f"Train: {len(y_train)} samples, Test: {len(y_test)} samples")
        
        # Train model
        model = RandomForestClassifier(
            n_estimators=250,
            max_depth=12,
            min_samples_split=5,
            min_samples_leaf=2,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1
        )
        
        model.fit(X_train, y_train)
        
        # Predict
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        accuracy = accuracy_score(y_test, y_pred)
        baseline = max(y_test.value_counts(normalize=True))
        
        print(f"\n✓ Accuracy: {accuracy:.2%}")
        print(f"  Baseline: {baseline:.2%}")
        print(f"  Improvement: {accuracy - baseline:+.2%}\n")
        
        print(classification_report(y_test, y_pred, target_names=["DOWN", "UP"]))
        
        results.append({
            'window': i,
            'train_period': f"{train_start} to {train_end}",
            'test_period': f"{test_start} to {test_end}",
            'train_samples': len(y_train),
            'test_samples': len(y_test),
            'accuracy': accuracy,
            'baseline': baseline,
            'improvement': accuracy - baseline
        })
        
    except Exception as e:
        print(f"❌ Error in window {i}: {e}")
        continue

# Summary
print("\n" + "=" * 70)
print("WALK-FORWARD BACKTEST SUMMARY")
print("=" * 70)

if results:
    df_results = pd.DataFrame(results)
    print(df_results.to_string(index=False))
    
    avg_accuracy = df_results['accuracy'].mean()
    avg_improvement = df_results['improvement'].mean()
    
    print(f"\n📊 AVERAGE PERFORMANCE:")
    print(f"   Mean Accuracy: {avg_accuracy:.2%}")
    print(f"   Mean Improvement over Baseline: {avg_improvement:+.2%}")
    print(f"   Consistency: {df_results['accuracy'].std():.2%} std dev")
    
    # Save results
    df_results.to_csv("walk_forward_results.csv", index=False)
    print(f"\n✅ Results saved to walk_forward_results.csv")
else:
    print("❌ No results generated")

print("=" * 70)