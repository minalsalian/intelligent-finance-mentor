import pandas as pd
import numpy as np

def add_features(df):

    # -------- Basic Range ----------
    df["High_Low_Range"] = df["High"] - df["Low"]

    # -------- Moving Averages ----------
    df["MA_5"] = df["Close"].rolling(5).mean()
    df["MA_10"] = df["Close"].rolling(10).mean()
    df["MA_20"] = df["Close"].rolling(20).mean()

    # -------- Exponential MA ----------
    df["EMA_10"] = df["Close"].ewm(span=10, adjust=False).mean()
    df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()

    # -------- MACD ----------
    ema12 = df["Close"].ewm(span=12, adjust=False).mean()
    ema26 = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()

    # -------- RSI ----------
    delta = df["Close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))

    # -------- ATR (Volatility) ----------
    df["TR"] = np.maximum(
        df["High"] - df["Low"],
        np.maximum(
            abs(df["High"] - df["Close"].shift()),
            abs(df["Low"] - df["Close"].shift())
        )
    )
    df["ATR"] = df["TR"].rolling(14).mean()

    # -------- Momentum ----------
    df["Momentum"] = df["Close"] - df["Close"].shift(10)

    # -------- Volume Change ----------
    df["Volume_Change"] = df["Volume"].pct_change()

    # -------- Candle Body ----------
    df["Body"] = abs(df["Close"] - df["Open"])

    # -------- Trend Feature ----------
    df["Trend"] = (df["EMA_10"] > df["EMA_20"]).astype(int)

    # -------- Target: Will price go UP tomorrow? (Next-day direction) ----------
    df["Return"] = df["Close"].pct_change().shift(-1)

    # Simple: UP if return > 0, DOWN otherwise
    df["Target"] = np.where(df["Return"] > 0.001, 1, 0)  # Use 0.1% threshold to filter noise

    df.dropna(inplace=True)

    return df