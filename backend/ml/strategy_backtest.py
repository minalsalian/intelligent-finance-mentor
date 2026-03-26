import pandas as pd
import numpy as np
import yfinance as yf
from feature_engineering import add_features
import pickle

print("=" * 70)
print("STRATEGY BACKTEST: Trade Based on Model Predictions")
print("=" * 70)

# Load trained model
with open("model.pkl", "rb") as f:
    model_data = pickle.load(f)
    model = model_data['model']
    threshold = model_data.get('threshold', 0.5)
    feature_cols = model_data['features']

# Test stock
symbol = "AAPL"
print(f"\n📈 Testing strategy on {symbol}...")

# Fetch data
stock = yf.Ticker(symbol)
df = stock.history(period="1y")

if df.empty:
    print("❌ No data")
    exit(1)

df = df.reset_index()
df = df[["Date", "Open", "High", "Low", "Close", "Volume"]]
original_df = df.copy()

# Add features
df = add_features(df)

X = df[feature_cols].copy()
y_actual = df["Target"].copy()

valid_idx = X.notna().all(axis=1) & y_actual.notna()
X = X[valid_idx].reset_index(drop=True)
y_actual = y_actual[valid_idx].reset_index(drop=True)
df = df[valid_idx].reset_index(drop=True)

print(f"Valid trading days: {len(df)}")

# Generate predictions
df['pred_proba'] = model.predict_proba(X)[:, 1]
df['prediction'] = (df['pred_proba'] >= threshold).astype(int)
df['actual'] = y_actual

# Strategy: If predict UP, buy at open, sell at close
# Simulate trades
initial_capital = 10000
cash = initial_capital
position = 0
trades = []
equity_curve = [initial_capital]

for i in range(len(df) - 1):
    row = df.iloc[i]
    next_row = df.iloc[i + 1]
    
    # If predict UP and have cash
    if row['prediction'] == 1 and cash > 0:
        # Buy at next day open
        shares = cash / next_row['Open']
        position = shares
        entry_price = next_row['Open']
        cash = 0
        
        # Sell at next day close
        exit_price = next_row['Close']
        cash = position * exit_price
        pnl = cash - (position * entry_price)
        position = 0
        
        trades.append({
            'date': next_row['Date'],
            'entry': entry_price,
            'exit': exit_price,
            'pnl': pnl,
            'return_pct': (exit_price - entry_price) / entry_price * 100
        })
    
    equity_curve.append(cash if cash > 0 else initial_capital)

# Calculate metrics
df_trades = pd.DataFrame(trades)

if len(df_trades) > 0:
    total_return = (cash - initial_capital) / initial_capital * 100
    win_rate = (df_trades['pnl'] > 0).sum() / len(df_trades) * 100
    avg_win = df_trades[df_trades['pnl'] > 0]['pnl'].mean() if (df_trades['pnl'] > 0).any() else 0
    avg_loss = df_trades[df_trades['pnl'] < 0]['pnl'].mean() if (df_trades['pnl'] < 0).any() else 0
    
    # Sharpe ratio (simplified)
    returns = df_trades['return_pct'].values
    sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
    
    # Max drawdown
    equity_series = pd.Series(equity_curve)
    running_max = equity_series.expanding().max()
    drawdown = (equity_series - running_max) / running_max * 100
    max_drawdown = drawdown.min()
    
    # Buy-and-hold comparison
    buy_hold_return = (df.iloc[-1]['Close'] - df.iloc[0]['Close']) / df.iloc[0]['Close'] * 100
    
    print("\n" + "=" * 70)
    print("STRATEGY RESULTS")
    print("=" * 70)
    print(f"Initial Capital: ${initial_capital:,.2f}")
    print(f"Final Capital: ${cash:,.2f}")
    print(f"Total Return: {total_return:+.2f}%")
    print(f"Buy & Hold Return: {buy_hold_return:+.2f}%")
    print(f"Alpha (vs Buy & Hold): {total_return - buy_hold_return:+.2f}%\n")
    
    print(f"Total Trades: {len(df_trades)}")
    print(f"Win Rate: {win_rate:.1f}%")
    print(f"Average Win: ${avg_win:.2f}")
    print(f"Average Loss: ${avg_loss:.2f}")
    print(f"Sharpe Ratio: {sharpe:.2f}")
    print(f"Max Drawdown: {max_drawdown:.2f}%\n")
    
    # Save
    df_trades.to_csv("strategy_trades.csv", index=False)
    pd.DataFrame({'equity': equity_curve}).to_csv("equity_curve.csv", index=False)
    
    print("✅ Trade history saved to strategy_trades.csv")
    print("✅ Equity curve saved to equity_curve.csv")
    
    # Add to backtest endpoint results
    strategy_results = {
        "symbol": symbol,
        "period": "1 year",
        "initial_capital": initial_capital,
        "final_capital": round(cash, 2),
        "total_return_pct": round(total_return, 2),
        "buy_hold_return_pct": round(buy_hold_return, 2),
        "alpha_vs_buy_hold": round(total_return - buy_hold_return, 2),
        "total_trades": len(df_trades),
        "win_rate_pct": round(win_rate, 1),
        "sharpe_ratio": round(sharpe, 2),
        "max_drawdown_pct": round(max_drawdown, 2)
    }
    
    with open("strategy_results.json", "w") as f:
        import json
        json.dump(strategy_results, f, indent=2)
    
    print("\n✅ Strategy summary saved to strategy_results.json")
else:
    print("\n⚠️  No trades generated")

print("=" * 70)