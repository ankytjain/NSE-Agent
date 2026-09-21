import yfinance as yf
import pandas as pd
from datetime import datetime

def calculate_rsi_native(series, period=14):
    """Calculates 14-day RSI natively using Pandas math."""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, 0.00001)
    return 100 - (100 / (1 + rs))

def execute_trading_logic(df):
    """Executes trading strategy criteria using standard Pandas dataframes."""
    if len(df) < 200:
        return "INSUFFICIENT DATA", "-", "-", "-"

    close_price = round(df['Close'].iloc[-1], 2)
    volume_today = df['Volume'].iloc[-1]
    
    sma200 = df['Close'].rolling(window=200).mean().iloc[-1]
    rsi_series = calculate_rsi_native(df['Close'], period=14)
    curr_rsi = rsi_series.iloc[-1]
    prev_rsi = rsi_series.iloc[-2]
    
    avg_vol_20 = df['Volume'].iloc[-21:-1].mean()
    is_vol_spike = volume_today >= (avg_vol_20 * 1.5)
    highest_20 = df['High'].iloc[-21:-1].max()

    if close_price < sma200:
        return "AVOID (Under 200 SMA)", f"₹{close_price}", "-", "-"

    decision = "HOLD / NO SIGNAL"
    
    if close_price > highest_20 and is_vol_spike:
        decision = "⚡ EXECUTE BUY (Breakout)"
    elif prev_rsi <= 30 and curr_rsi > 30:
        decision = "🟢 EXECUTE BUY (RSI Reversal)"
    elif curr_rsi >= 75 or (prev_rsi >= 70 and curr_rsi < 70):
        decision = "🔴 EXECUTE SELL / TAKE PROFIT"

    if "EXECUTE BUY" in decision:
        stop_loss = round(close_price * 0.97, 2)
        target = round(close_price * 1.06, 2)
        return decision, f"₹{close_price}", f"₹{stop_loss}", f"₹{target}"
    
    return decision, f"₹{close_price}", "-", "-"

def run_agent():
    tickers = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "SBIN"]
    rows = []
    
    # Generate timestamp text string
    timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M UTC')
    
    for ticker in tickers:
        try:
            stock = yf.Ticker(f"{ticker}.NS")
            hist = stock.history(period="1y")
            
            if len(hist) == 0:
                rows.append([f"**{ticker}**", "FETCH FAILED", "-", "-", "-", timestamp_str])
                continue

            decision, entry, sl, target = execute_trading_logic(hist)
            rows.append([f"**{ticker}**", decision, entry, sl, target, timestamp_str])
            print(f"Processed {ticker}: {decision}")
            
        except Exception as e:
            rows.append([f"**{ticker}**", "LOGIC ERROR", "-", "-", "-", timestamp_str])

    # Build the live visual Markdown Table structure
    markdown_content = (
        f"# 🤖 My Automated Trading Dashboard\n\n"
        f"This table updates automatically twice a day (11:30 AM & 4:00 PM IST).\n\n"
        f"| Ticker | Agent Decision | Current/Entry Price | Stop-Loss (3%) | Target Profit (6%) | Last Updated |\n"
        f"| :--- | :--- | :--- | :--- | :--- | :--- |\n"
    )
    
    for row in rows:
        markdown_content += f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} |\n"

    # Save directly as the repository landing homepage file
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(markdown_content)
    print("Markdown dashboard generated successfully!")

if __name__ == "__main__":
    run_agent()
