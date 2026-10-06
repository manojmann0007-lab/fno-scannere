import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

st.set_page_config(page_title="F&O Signal App", layout="wide")
analyzer = SentimentIntensityAnalyzer()

FNO_STOCKS = {
    "TATASTEEL.NS": "METAL", "JINDALSTEL.NS": "METAL",
    "HDFCBANK.NS": "BANK", "ICICIBANK.NS": "BANK",
    "INFY.NS": "IT", "TCS.NS": "IT",
    "TATAMOTORS.NS": "AUTO", "M&M.NS": "AUTO",
    "RELIANCE.NS": "ENERGY", "SUNPHARMA.NS": "PHARMA"
}

def get_sentiment(ticker):
    try:
        t = yf.Ticker(ticker)
        news = t.news
        if not news: return 0.0, "न्यूट्रल"
        scores = [analyzer.polarity_scores(n.get('title',''))['compound'] for n in news[:3]]
        avg = np.mean(scores)
        headline = news[0].get('title', '')[:50]
        if avg >= 0.15: return avg, f"बुलिश: {headline}.."
        elif avg <= -0.15: return avg, f"बेयरिश: {headline}.."
        return avg, "न्यूट्रल न्यूज़"
    except:
        return 0.0, "डेटा उपलब्ध नहीं"

def check_stock(ticker, sector):
    try:
        df = yf.download(ticker, period="3mo", interval="1d", progress=False)
        if df.empty or len(df) < 25: return None
        
        close = df['Close'].iloc[-1].item()
        df['EMA20'] = df['Close'].ewm(span=20).mean()
        df['EMA50'] = df['Close'].ewm(span=50).mean()
        ema20 = df['EMA20'].iloc[-1].item()
        ema50 = df['EMA50'].iloc[-1].item()

        df['TR'] = np.maximum(df['High'] - df['Low'], np.maximum(abs(df['High'] - df['Close'].shift()), abs(df['Low'] - df['Close'].shift())))
        atr = df['TR'].rolling(14).mean().iloc[-1].item()
        
        score, news_txt = get_sentiment(ticker)
        
        sig, sl, tgt = "NEUTRAL", 0.0, 0.0
        if close > ema20 and ema20 > ema50 and score >= 0:
            sig = "🟢 BUY (CALL)"
            sl = round(close - (1.5 * atr), 2)
            tgt = round(close + (3.0 * atr), 2)
        elif close < ema20 and ema20 < ema50 and score <= 0:
            sig = "🔴 SELL (PUT)"
            sl = round(close + (1.5 * atr), 2)
            tgt = round(close - (3.0 * atr), 2)
            
        return {"Stock": ticker.replace(".NS",""), "Sector": sector, "Signal": sig, "Price": round(close,2), "SL": sl, "Target": tgt, "News": news_txt}
    except:
        return None

st.title("🎯 F&O स्टॉक स्कैनर & ट्रेड सिग्नल्स")

if st.button("🚀 आज के सिग्नल स्कैन करें"):
    with st.spinner("स्कैनिंग जारी है..."):
        data = [check_stock(k, v) for k, v in FNO_STOCKS.items()]
        valid = [d for d in data if d is not None]
        if valid:
            df = pd.DataFrame(valid)
            st.dataframe(df, use_container_width=True)
