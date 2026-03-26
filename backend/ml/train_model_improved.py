import pandas as pd
import pickle
import numpy as np
import yfinance as yf
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, roc_auc_score
from feature_engineering import add_features
from data_collection import fetch_multiple_stocks

print("=" * 70)
print("OPTIMIZED MODEL: Multi-Stock Training + Stock-Specific Testing")
print("=" * 70)

# ============================================
# TRAIN on Multiple Stocks (but same prediction window)
# ============================================
print("\n📊 FETCHING MULTI-STOCK TRAINING DATA...")
symbols_train = ["AAPL", "MSFT", "GOOGL", "AMZN"]
symbols_test = ["TSLA"]

df_train = fetch_multiple_stocks(symbols=symbols_train, period="2y")

if df_train is None:
    print("❌ Failed, using fallback...")
    df_train = pd.read_csv("historical_data.csv")

# Add features - using add_features which has 1-day target
df_train = add_features(df_train)

feature_cols = [
    "EMA_10", "EMA_20", "MA_5", "MA_10", "MA_20",
    "RSI", "Body", "High_Low_Range", "Volume",
    "MACD", "MACD_Signal", "ATR", "Momentum", "Volume_Change"
]

X_train_full = df_train[feature_cols].copy()
y_train_full = df_train["Target"].copy()

valid_idx = X_train_full.notna().all(axis=1) & y_train_full.notna()
X_train_full = X_train_full[valid_idx].reset_index(drop=True)
y_train_full = y_train_full[valid_idx].reset_index(drop=True)

print(f"Training samples: {len(y_train_full)}")
print(f"Target distribution (1-day):\n{y_train_full.value_counts()}\n")

# Train/Val split
split = int(len(X_train_full) * 0.8)
X_train = X_train_full[:split]
y_train = y_train_full[:split]
X_val = X_train_full[split:]
y_val = y_train_full[split:]

print("🤖 TRAINING ON MULTI-STOCK DATA...")
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

# Find best threshold
y_val_proba = model.predict_proba(X_val)[:, 1]
best_threshold = 0.5
best_f1 = 0

for t in np.arange(0.3, 0.7, 0.05):
    y_pred_t = (y_val_proba >= t).astype(int)
    f1 = f1_score(y_val, y_pred_t, zero_division=0)
    if f1 > best_f1:
        best_f1 = f1
        best_threshold = t

print(f"Best threshold: {best_threshold:.2f}\n")

# ============================================
# TEST: AAPL (in-distribution) vs TSLA (out-of-distribution)
# ============================================

def evaluate_stock(stock_symbol, period="1y"):
    """Test model on a specific stock"""
    print(f"\n{'=' * 70}")
    print(f"Testing on {stock_symbol}")
    print(f"{'=' * 70}")
    
    try:
        stock_data = yf.Ticker(stock_symbol)
        df_test = stock_data.history(period=period)
        
        if df_test.empty:
            print(f"⚠️  No data for {stock_symbol}")
            return None
        
        df_test = df_test.reset_index()
        df_test = df_test[["Date", "Open", "High", "Low", "Close", "Volume"]]
        df_test["Symbol"] = stock_symbol
        df_test = add_features(df_test)
        
        X_test = df_test[feature_cols].copy()
        y_test = df_test["Target"].copy()
        
        valid_idx_test = X_test.notna().all(axis=1) & y_test.notna()
        X_test = X_test[valid_idx_test].reset_index(drop=True)
        y_test = y_test[valid_idx_test].reset_index(drop=True)
        
        if len(y_test) < 10:
            print(f"⚠️  Only {len(y_test)} valid samples")
            return None
        
        print(f"Test samples: {len(y_test)}")
        print(f"Target distribution:\n{y_test.value_counts()}\n")
        
        # Predict
        y_test_proba = model.predict_proba(X_test)[:, 1]
        y_test_pred = (y_test_proba >= best_threshold).astype(int)
        
        accuracy = accuracy_score(y_test, y_test_pred)
        baseline = max(y_test.value_counts(normalize=True))
        roc_auc = roc_auc_score(y_test, y_test_proba)
        
        print(f"Accuracy: {accuracy:.2%}")
        print(f"Baseline: {baseline:.2%}")
        print(f"Improvement: {accuracy - baseline:+.2%}")
        print(f"ROC-AUC: {roc_auc:.4f}\n")
        
        cm = confusion_matrix(y_test, y_test_pred)
        print("Confusion Matrix:")
        print(cm)
        print(f"True Positives (Correct UP): {cm[1,1]}")
        print(f"True Negatives (Correct DOWN): {cm[0,0]}\n")
        
        print("Classification Report:")
        print(classification_report(y_test, y_test_pred, target_names=["DOWN", "UP"]))
        
        return {
            'symbol': stock_symbol,
            'accuracy': accuracy,
            'baseline': baseline,
            'roc_auc': roc_auc,
            'cm': cm
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

# Test on multiple stocks
results = {}

# In-distribution test (AAPL - was in training)
results['AAPL'] = evaluate_stock("AAPL", period="6mo")

# Out-of-distribution test (TSLA - not in training)
results['TSLA'] = evaluate_stock("TSLA", period="1y")

# Additional unseen stock for robustness
results['NFLX'] = evaluate_stock("NFLX", period="1y")

# ============================================
# FEATURE IMPORTANCE
# ============================================
print(f"\n{'=' * 70}")
print("Feature Importance")
print(f"{'=' * 70}")

feature_imp = pd.DataFrame({
    'feature': feature_cols,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print(feature_imp.head(10).to_string(index=False))

# ============================================
# SAVE MODEL
# ============================================
model_data = {
    'model': model,
    'threshold': best_threshold,
    'features': feature_cols,
    'training_stocks': symbols_train,
    'training_samples': len(y_train_full)
}

with open("model.pkl", "wb") as f:
    pickle.dump(model_data, f)

print(f"\n{'=' * 70}")
print("✅ MODEL SAVED")
print(f"{'=' * 70}")
print(f"Training: {len(symbols_train)} stocks, ~2 years, {len(y_train_full)} samples")
print(f"Prediction: Next-day direction (1-day forward)")

if results.get('AAPL'):
    print(f"✓ AAPL Accuracy: {results['AAPL']['accuracy']:.2%} (in-distribution)")
if results.get('TSLA'):
    print(f"? TSLA Accuracy: {results['TSLA']['accuracy']:.2%} (out-of-distribution)")
if results.get('NFLX'):
    print(f"? NFLX Accuracy: {results['NFLX']['accuracy']:.2%} (unseen stock)")

print(f"{'=' * 70}\n")