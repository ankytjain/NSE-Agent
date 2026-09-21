import os
import json
import gspread
from google.oauth2.service_account import Credentials
import yfinance as yf
import pandas as pd

def calculate_rsi_native(series, period=14):
    """Calculates 14-day RSI natively using Pandas math."""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    # Avoid zero division errors
    rs = gain / loss.replace(0, 0.00001)
    rsi = 100 - (100 / (1 + rs))
    return rsi

def execute_trading_logic(df):
    """Executes structural rules using standard Pandas arrays."""
    if len(df) < 200:
        return "INSUFFICIENT DATA", "-", "-", "-"

    close_price = round(df['Close'].iloc[-1], 2)
    volume_today = df['Volume'].iloc[-1]
    
    # 1. Calculate Simple Moving Averages (SMA)
    sma200 = df['Close'].rolling(window=200).mean().iloc[-1]
    
    # 2. Calculate native RSI
    rsi_series = calculate_rsi_native(df['Close'], period=14)
    curr_rsi = rsi_series.iloc[-1]
    prev_rsi = rsi_series.iloc[-2]
    
    # 3. Calculate 20-Day breakout thresholds and Volume Spikes
    avg_vol_20 = df['Volume'].iloc[-21:-1].mean()
    is_vol_spike = volume_today >= (avg_vol_20 * 1.5)
    highest_20 = df['High'].iloc[-21:-1].max()

    # --- Trend Filter Rule ---
    if close_price < sma200:
        return "AVOID (Under 200 SMA)", "-", "-", "-"

    decision = "HOLD / NO SIGNAL"
    
    # Check for Volume-Confirmed Breakout
    if close_price > highest_20 and is_vol_spike:
        decision = "⚡ EXECUTE BUY (Breakout)"
    # Check for RSI Oversold Exit
    elif prev_rsi <= 30 and curr_rsi > 30:
        decision = "🟢 EXECUTE BUY (RSI Reversal)"
    # Check for Overbought Exhaustion
    elif curr_rsi >= 75 or (prev_rsi >= 70 and curr_rsi < 70):
        decision = "🔴 EXECUTE SELL / TAKE PROFIT"

    # Calculate exact Target boundaries
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
    
    # Explicitly register both the Sheets and Drive scopes to grant complete access
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    
    # Ensure this matches your Google Sheet title exactly
    sheet = client.open("Your 5-Stock Watchlist").sheet1

