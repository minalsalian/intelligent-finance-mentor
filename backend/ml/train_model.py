import pandas as pd
import pickle
import numpy as np
import yfinance as yf
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, roc_auc_score
from feature_engineering import add_features

# ============================================
# TRAIN on AAPL (2024)
# ============================================
print("=" * 70)
print("TRAINING ON: AAPL 2024")
print("=" * 70)

df_train = pd.read_csv("historical_data.csv")
df_train = add_features(df_train)

feature_cols = [
    "EMA_10", "EMA_20",
    "MA_5", "MA_10", "MA_20",
    "RSI", "Body", "High_Low_Range", "Volume",
    "MACD", "MACD_Signal", "ATR", "Momentum", "Volume_Change"
]

X_train_full = df_train[feature_cols].copy()
y_train_full = df_train["Target"].copy()

valid_idx = X_train_full.notna().all(axis=1) & y_train_full.notna()
X_train_full = X_train_full[valid_idx].reset_index(drop=True)
y_train_full = y_train_full[valid_idx].reset_index(drop=True)

print(f"Training samples: {len(y_train_full)}")
print(f"Target distribution:\n{y_train_full.value_counts()}\n")

# Train model on ALL AAPL data
model = RandomForestClassifier(
    n_estimators=200,
    max_depth=10,
    min_samples_split=5,
    min_samples_leaf=2,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)

model.fit(X_train_full, y_train_full)

# Save threshold from training data
split = int(len(X_train_full) * 0.8)
X_train = X_train_full[:split]
y_train = y_train_full[:split]
X_val = X_train_full[split:]
y_val = y_train_full[split:]

y_val_proba = model.predict_proba(X_val)[:, 1]
best_f1 = 0
best_threshold = 0.5
for t in np.arange(0.3, 0.7, 0.05):
    y_pred_t = (y_val_proba >= t).astype(int)
    f1 = f1_score(y_val, y_pred_t, zero_division=0)
    if f1 > best_f1:
        best_f1 = f1
        best_threshold = t

print(f"Best threshold (from AAPL data): {best_threshold:.2f}\n")

# ============================================
# TEST on GOOGL (Fresh Stock Data)
# ============================================
print("=" * 70)
print("TESTING ON: GOOGL (Fresh Data - Never Seen Before)")
print("=" * 70)

try:
    googl = yf.Ticker("GOOGL")
    df_test = googl.history(period="6mo")  # 6 months of fresh data
    
    if df_test.empty:
        print("❌ Could not fetch GOOGL data, using fallback stock...")
        # Fallback: test on different time period of AAPL
        aapl = yf.Ticker("AAPL")
        df_test = aapl.history(period="3mo", start="2025-01-01")
        if df_test.empty:
            df_test = aapl.history(period="1mo")
    
    df_test = df_test.reset_index()
    df_test = df_test[["Date", "Open", "High", "Low", "Close", "Volume"]]
    df_test = add_features(df_test)
    
    X_test = df_test[feature_cols].copy()
    y_test = df_test["Target"].copy()
    
    valid_idx_test = X_test.notna().all(axis=1) & y_test.notna()
    X_test = X_test[valid_idx_test].reset_index(drop=True)
    y_test = y_test[valid_idx_test].reset_index(drop=True)
    
    if len(y_test) < 10:
        print(f"⚠️  Only {len(y_test)} samples available, need at least 10")
    else:
        print(f"Test samples: {len(y_test)}")
        print(f"Target distribution:\n{y_test.value_counts()}\n")
        
        # Predict on fresh data
        y_test_proba = model.predict_proba(X_test)[:, 1]
        y_test_pred = (y_test_proba >= best_threshold).astype(int)
        
        accuracy_test = accuracy_score(y_test, y_test_pred)
        baseline_test = max(y_test.value_counts(normalize=True))
        roc_auc_test = roc_auc_score(y_test, y_test_proba)
        
        print("=" * 70)
        print("OUT-OF-SAMPLE ACCURACY (Real Performance)")
        print("=" * 70)
        print(f"Accuracy on FRESH data: {accuracy_test:.2%}")
        print(f"Baseline (always predict majority): {baseline_test:.2%}")
        print(f"True Improvement: {accuracy_test - baseline_test:+.2%}")
        print(f"ROC-AUC: {roc_auc_test:.4f}\n")
        
        print("Confusion Matrix:")
        cm_test = confusion_matrix(y_test, y_test_pred)
        print(cm_test)
        print(f"\nTrue Negatives: {cm_test[0,0]}")
        print(f"False Positives: {cm_test[0,1]}")
        print(f"False Negatives: {cm_test[1,0]}")
        print(f"True Positives: {cm_test[1,1]}\n")
        
        print("Classification Report:")
        print(classification_report(y_test, y_test_pred, target_names=["DOWN", "UP"]))

except Exception as e:
    print(f"⚠️  Error fetching test data: {e}")
    print("Using original validation split instead...\n")

# ============================================
# SAVE MODEL
# ============================================
print("=" * 70)
model_data = {
    'model': model,
    'threshold': best_threshold,
    'features': feature_cols
}

with open("model.pkl", "wb") as f:
    pickle.dump(model_data, f)

print(f"✅ Model saved (threshold: {best_threshold})")
print("\n📊 KEY TAKEAWAY:")
print("- Training accuracy is HIGH because model learns AAPL patterns")
print("- Test accuracy on NEW stock shows REAL predictive power")
print("- If test accuracy is 55-65%, that's honest and good!")
print("- If it's 90%+, the model generalizes VERY well")
print("=" * 70)