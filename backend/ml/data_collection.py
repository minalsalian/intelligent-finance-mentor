import yfinance as yf
import pandas as pd

def fetch_stock_data(symbol="AAPL", period="1y"):
    """Fetch data for a single stock"""
    try:
        stock = yf.Ticker(symbol)
        df = stock.history(period=period)
        
        if df.empty:
            print(f"⚠️  No data for {symbol}")
            return None
        
        df = df.reset_index()
        df = df[["Date", "Open", "High", "Low", "Close", "Volume"]]
        df["Symbol"] = symbol  # Track which stock
        
        print(f"✓ Fetched {len(df)} rows for {symbol}")
        return df
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None


def fetch_multiple_stocks(symbols=["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"], period="1y"):
    """Fetch data for multiple stocks and combine"""
    all_data = []
    
    for symbol in symbols:
        df = fetch_stock_data(symbol, period)
        if df is not None:
            all_data.append(df)
    
    if not all_data:
        print("❌ No data fetched")
        return None
    
    combined_df = pd.concat(all_data, ignore_index=True)
    combined_df = combined_df.drop_duplicates()  # Remove any duplicates
    
    print(f"\n✓ Combined {len(combined_df)} total rows from {len(symbols)} stocks")
    return combined_df


if __name__ == "__main__":
    # Fetch 5 major stocks for better generalization
    data = fetch_multiple_stocks(
        symbols=["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
        period="1y"
    )
    
    if data is not None:
        data.to_csv("historical_data_multi.csv", index=False)
        print(f"\n✅ Data saved to historical_data_multi.csv ({len(data)} rows)")