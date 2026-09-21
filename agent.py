import os
import json
import gspread
from google.oauth2.service_account import Credentials
import yfinance as yf
import pandas as pd
import pandas_ta as ta

def execute_trading_logic(df):
    """Executes structural rules to generate precise trade signals."""
    if len(df) < 200:
        return "INSUFFICIENT DATA", "-", "-", "-"

    close_price = round(df['Close'].iloc[-1], 2)
    volume_today = df['Volume'].iloc[-1]

    sma200 = ta.sma(df['Close'], length=200).iloc[-1]
    rsi = ta.rsi(df['Close'], length=14)
    curr_rsi = rsi.iloc[-1]
    prev_rsi = rsi.iloc[-2]

    avg_vol_20 = df['Volume'].iloc[-21:-1].mean()
    is_vol_spike = volume_today >= (avg_vol_20 * 1.5)
    highest_20 = df['High'].iloc[-21:-1].max()

    if close_price < sma200:
        return "AVOID (Under 200 SMA)", "-", "-", "-"

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
        return decision, close_price, stop_loss, target

    return decision, close_price, "-", "-"

def run_agent():
    secret_creds = os.environ.get("GOOGLE_CREDENTIALS")
    if not secret_creds:
        raise ValueError("Missing GOOGLE_CREDENTIALS secret!")

    creds_dict = json.loads(secret_creds)
    scopes = ["https://googleapis.com"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)

    # Ensure this matches your Google Sheet name exactly
    sheet = client.open("Your 5-Stock Watchlist").sheet1
    tickers = sheet.col_values(1)[1:6] 

    updates = []

    for ticker in tickers:
        try:
            formatted_ticker = f"{ticker}.NS" if not ticker.endswith(".NS") else ticker
            stock = yf.Ticker(formatted_ticker)
            hist = stock.history(period="1y")

            decision, entry, sl, target = execute_trading_logic(hist)
            updates.append([decision, entry, sl, target])

        except Exception as e:
            updates.append(["SYSTEM ERROR", "-", "-", "-"])

    # Update columns B to E for rows 2 through 6
    sheet.update("B2:E6", updates)
    print("Execution instructions successfully deployed to sheet.")

if __name__ == "__main__":
    run_agent()
