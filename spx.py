import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Dashboard setup
st.set_page_config(layout="wide")
st.title("SPX/SPY/ES 0DTE Options Dashboard")

# Fetch live data
@st.cache_data(ttl=60)
def get_live_data():
    spx = yf.Ticker("^GSPC")
    spy = yf.Ticker("SPY")
    es = yf.Ticker("ES=F")
    
    hist = yf.download(["^GSPC", "SPY", "ES=F"], period="3d")["Close"]
    
    return {
        "current": {
            "SPX": spx.history(period="1d")["Close"].iloc[-1],
            "SPY": spy.history(period="1d")["Close"].iloc[-1],
            "ES": es.history(period="1d")["Close"].iloc[-1]
        },
        "history": hist
    }

data = get_live_data()

# Current prices
col1, col2, col3 = st.columns(3)
col1.markdown(f"**SPX:** ${data['current']['SPX']:.2f}")
col2.markdown(f"**SPY:** ${data['current']['SPY']:.2f}")
col3.markdown(f"**ES-Mini:** ${data['current']['ES']:.2f}")

# Historical levels
st.subheader("Historical Levels")
hist_data = {
    "Metric": ["2-Day High", "2-Day Low", "Prev Day High", "Prev Day Low"],
    "SPX": [
        data["history"]["^GSPC"].max(),
        data["history"]["^GSPC"].min(),
        data["history"]["^GSPC"].iloc[-2:].max(),
        data["history"]["^GSPC"].iloc[-2:].min()
    ],
    "SPY": [
        data["history"]["SPY"].max(),
        data["history"]["SPY"].min(),
        data["history"]["SPY"].iloc[-2:].max(),
        data["history"]["SPY"].iloc[-2:].min()
    ],
    "ES": [
        data["history"]["ES=F"].max(),
        data["history"]["ES=F"].min(),
        data["history"]["ES=F"].iloc[-2:].max(),
        data["history"]["ES=F"].iloc[-2:].min()
    ]
}
st.dataframe(pd.DataFrame(hist_data).set_index("Metric").style.format("{:.2f}"))

# Mock options data (replace with actual 0DTE options data)
st.subheader("0DTE Options Exposure")
stocks = ["SPX"]
expiry = datetime.now().strftime("%Y-%m-%d")

# Gamma Exposure Calculation
stocks = ["SPX"]
expiry = datetime.now().strftime("%Y-%m-%d")

# Gamma Exposure Calculation
@st.cache_data(ttl=60)
def calculate_gamma_exposure():
    # Mock data - replace with actual options chain data
    strikes = np.arange(data['current']['SPX']*0.95, data['current']['SPX']*1.05, 5)
    call_gamma = np.random.uniform(0, 1, len(strikes))
    put_gamma = np.random.uniform(0, 1, len(strikes))
    
    net_gamma = call_gamma - put_gamma
    return strikes, net_gamma

# Delta Exposure Calculation
@st.cache_data(ttl=60)
def calculate_delta_exposure():
    strikes = np.arange(data['current']['SPX']*0.95, data['current']['SPX']*1.05, 5)
    call_delta = np.random.uniform(0, 1, len(strikes))
    put_delta = np.random.uniform(-1, 0, len(strikes))
    
    net_delta = call_delta + put_delta
    return strikes, net_delta

# OI and Volume
@st.cache_data(ttl=60)
def get_oi_volume():
    strikes = np.arange(data['current']['SPX']*0.95, data['current']['SPX']*1.05, 5)
    call_oi = np.random.randint(100, 1000, len(strikes))
    put_oi = np.random.randint(100, 1000, len(strikes))
    call_vol = np.random.randint(10, 500, len(strikes))
    put_vol = np.random.randint(10, 500, len(strikes))
    return strikes, call_oi, put_oi, call_vol, put_vol

# Dynamic Hedge Calculation
def calculate_dynamic_hedge(gamma_exposure):
    # Simplified version based on traderade principles
    # Find strike where gamma exposure crosses zero
    strikes, net_gamma = gamma_exposure
    zero_cross_idx = np.where(np.diff(np.sign(net_gamma)))[0]
    
    if len(zero_cross_idx) > 0:
        hedge_strike = strikes[zero_cross_idx[0]]
    else:
        hedge_strike = data['current']['SPX']
    
    return hedge_strike

# Plotting
strikes, net_gamma = calculate_gamma_exposure()
strikes_d, net_delta = calculate_delta_exposure()
strikes_ov, call_oi, put_oi, call_vol, put_vol = get_oi_volume()

# Gamma Exposure Plot
fig1, ax1 = plt.subplots()
ax1.bar(strikes, np.where(net_gamma > 0, net_gamma, 0), color='green', label='Positive Gamma')
ax1.bar(strikes, np.where(net_gamma < 0, net_gamma, 0), color='red', label='Negative Gamma')
ax1.set_title("Net Gamma Exposure")
ax1.legend()

# Delta Exposure Plot
fig2, ax2 = plt.subplots()
ax2.bar(strikes_d, np.where(net_delta > 0, net_delta, 0), color='green', label='Positive Delta')
ax2.bar(strikes_d, np.where(net_delta < 0, net_delta, 0), color='red', label='Negative Delta')
ax2.set_title("Net Delta Exposure")
ax2.legend()

# OI Plot
fig3, ax3 = plt.subplots()
ax3.bar(strikes_ov, call_oi, color='green', label='Call OI')
ax3.bar(strikes_ov, put_oi, color='red', label='Put OI')
ax3.set_title("Open Interest")
ax3.legend()

# Volume Plot
fig4, ax4 = plt.subplots()
ax4.bar(strikes_ov, call_vol, color='green', label='Call Volume')
ax4.bar(strikes_ov, put_vol, color='red', label='Put Volume')
ax4.set_title("Volume")
ax4.legend()

# Display plots
col1, col2 = st.columns(2)
col1.pyplot(fig1)
col2.pyplot(fig2)

col3, col4 = st.columns(2)
col3.pyplot(fig3)
col4.pyplot(fig4)

# Dynamic Hedge Calculation
hedge_strike = calculate_dynamic_hedge((strikes, net_gamma))
st.markdown(f"**Dynamic Hedge Strike (Gamma Neutral):** ${hedge_strike:.2f}")

# Explanation
st.markdown("""
**Dynamic Hedge Explanation:**  
Based on Traderade principles, this calculates the strike price where gamma exposure crosses zero, 
indicating where market makers would need to adjust their futures hedges to remain delta neutral.
""")
