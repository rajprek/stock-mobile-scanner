import streamlit as st
import yfinance as yf
import pandas_ta as ta
import pandas as pd
import matplotlib.pyplot as plt

# Page Config
st.set_page_config(page_title="Nifty Pro Mobile", layout="wide")

# Styling for Professional Mobile Look
st.markdown("""
    <style>
    .reportview-container { background: #ffffff; }
    .stMetric { border: 1px solid #f0f2f6; padding: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

SECTOR_MAP = {
    "BANK NIFTY": ["AUBANK", "AXISBANK", "BANDHANBNK", "FEDERALBNK", "HDFCBANK", "ICICIBANK", "IDFCFIRSTB", "INDUSINDBK", "KOTAKBANK", "PNB", "SBIN"],
    "IT": ["COFORGE", "HCLTECH", "INFY", "KPITTECH", "LTIM", "MPHASIS", "PERSISTENT", "TCS", "TECHM", "WIPRO", "TATAELXSI"],
    "METALS": ["HINDALCO", "HINDZINC", "JINDALSTEL", "JSWSTEEL", "NATIONALUM", "NMDC", "SAIL", "TATASTEEL"],
    "AUTOMOBILE": ["ASHOKLEY", "BAJAJ-AUTO", "EICHERMOT", "HEROMOTOCO", "M&M", "MARUTI", "TVSMOTOR", "SONACOMS", "MOTHERSON"],
    "PHARMA": ["ALKEM", "AUROPHARMA", "BIOCON", "CIPLA", "DRREDDY", "GLENMARK", "LUPIN", "MANKIND", "SUNPHARMA", "ZYDUSLIFE"]
}

STOCK_TO_SECTOR = {s: sec for sec, stocks in SECTOR_MAP.items() for s in stocks}
ALL_STOCKS = list(STOCK_TO_SECTOR.keys())

def get_stock_data(symbol):
    try:
        t = yf.Ticker(f"{symbol}.NS")
        intraday = t.history(period="2d", interval="5m")
        daily = t.history(period="5d", interval="1d")
        if intraday.empty or len(daily) < 2: return None
        
        pdh, pdl, pdc = daily['High'].iloc[-2], daily['Low'].iloc[-2], daily['Close'].iloc[-2]
        price = round(intraday['Close'].iloc[-1], 2)
        pct = round(((price - pdc) / pdc) * 100, 2)
        
        vwap = round(ta.vwap(intraday['High'], intraday['Low'], intraday['Close'], intraday['Volume']).iloc[-1], 2)
        ema9_low = round(ta.ema(intraday['Low'], length=9).iloc[-1], 2)
        rsi = round(ta.rsi(intraday['Close'], length=14).iloc[-1], 2)
        
        action = "NEUTRAL"
        bo_pct = 0.0
        if price > pdh and price > vwap and price > ema9_low and rsi > 50:
            action = "STRONG BUY"
            bo_pct = round(((price - pdh) / pdh) * 100, 2)
        elif price < pdl and price < vwap and price < ema9_low and rsi < 50:
            action = "STRONG SELL"
            bo_pct = round(((pdl - price) / pdl) * 100, 2)
            
        return {"Symbol": symbol, "Price": price, "% Chg": pct, "BO %": bo_pct, "RSI": rsi, "Action": action, "VWAP": vwap, "9EMA_L": ema9_low}
    except: return None

st.title("🚀 Nifty Intra Pro")

if st.button('REFRESH MARKET DATA'):
    data_list = []
    progress = st.progress(0)
    for i, s in enumerate(ALL_STOCKS):
        d = get_stock_data(s)
        if d: data_list.append(d)
        progress.progress((i+1)/len(ALL_STOCKS))
    
    df = pd.DataFrame(data_list)
    
    tab1, tab2 = st.tabs(["🎯 SCANNED SIGNALS", "📊 SECTOR PULSE"])
    
    with tab1:
        st.subheader("Strong Buy/Sell Alerts")
        # Filter for only actionable stocks to save scrolling on mobile
        action_df = df[df['Action'] != "NEUTRAL"]
        if not action_df.empty:
            st.dataframe(action_df.style.applymap(lambda x: 'background-color: #d4edda' if x == 'STRONG BUY' else ('background-color: #f8d7da' if x == 'STRONG SELL' else ''), subset=['Action']))
        else:
            st.write("No strong breakouts currently.")
            
        st.subheader("All Watchlist")
        st.write(df)

    with tab2:
        df['Sector'] = df['Symbol'].map(STOCK_TO_SECTOR)
        sec_perf = df.groupby('Sector')['% Chg'].mean().sort_values()
        st.bar_chart(sec_perf)