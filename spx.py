import streamlit as st
import yfinance as yf
from yahoo_fin import options
import pandas as pd
import numpy as np
from math import log, sqrt, pi, exp
from scipy.stats import norm

# Configuration
st.set_page_config(layout="wide")
TICKERS = {"SPX": "^SPX", "SPY": "SPY", "ES": "ES=F"}
CONTRACT_SIZES = {"SPX": 100, "SPY": 100, "ES": 50}

# Black-Scholes calculations
def delta(otype, S, K, T, r, sigma):
    d1 = (log(S/K) + (r + 0.5*sigma**2)*T)/(sigma*sqrt(T))
    if otype == 'call':
        return norm.cdf(d1)
    else:
        return norm.cdf(d1) - 1

def gamma(otype, S, K, T, r, sigma):
    d1 = (log(S/K) + (r + 0.5*sigma**2)*T)/(sigma*sqrt(T))
    return norm.pdf(d1)/(S*sigma*sqrt(T))

# Data fetching functions  
@st.cache_data(ttl=60)
def get_live_data(ticker):
    data = yf.Ticker(ticker)
    hist = data.history(period="3d")
    return {
        "current": hist.iloc[-1].Close,
        "2d_high": hist.High[-3:-1].max(),
        "2d_low": hist.Low[-3:-1].min(),
        "1d_high": hist.High[-2],
        "1d_low": hist.Low[-2]
    }

@st.cache_data(ttl=300)
def get_options_chain(ticker):
    chain = options.get_options_chain(ticker)
    return pd.concat([chain["calls"], chain["puts"]])

# Metrics calculations
def calculate_gamma_exposure(df, spot):
    df["gamma_contribution"] = df.apply(lambda x: 
        x["Gamma"] * CONTRACT_SIZES["SPX"] * x["Open Interest"] * spot**2 * 0.01 
        * (-1 if x["Option Type"] == "put" else 1), axis=1)
    return df["gamma_contribution"].sum() / 1e9

def calculate_delta_exposure(df, spot):
    df["delta_contribution"] = df.apply(lambda x: 
        x["Delta"] * CONTRACT_SIZES["SPX"] * x["Open Interest"] * 
        (1 if x["Option Type"] == "call" else -1), axis=1)
    return df["delta_contribution"].sum() / 1e9

# Streamlit layout
def main():
    st.title("Real-Time SPX/SPY/ES Market Dashboard")
    
    # Price columns
    cols = st.columns(3)
    price_data = {t: get_live_data(TICKERS[t]) for t in TICKERS}
    
    for i, ticker in enumerate(TICKERS):
        with cols[i]:
            st.subheader(f"**{ticker}**")
            st.metric("Current Price", f"${price_data[ticker]['current']:,.2f}")
            st.write(f"2-Day High: {price_data[ticker]['2d_high']:,.2f}")
            st.write(f"2-Day Low: {price_data[ticker]['2d_low']:,.2f}") 
            st.write(f"Prev Day High: {price_data[ticker]['1d_high']:,.2f}")
            st.write(f"Prev Day Low: {price_data[ticker]['1d_low']:,.2f}")
    
    # Options analysis
    st.header("Options Metrics")
    for ticker in ["SPX", "SPY"]:
        df = get_options_chain(TICKERS[ticker])
        spot = price_data[ticker]["current"]
        
        # Calculate Greeks
        df["Delta"] = df.apply(lambda x: delta(x["Option Type"], spot, x.Strike, 0.0027, 0.05, 0.2), axis=1)
        df["Gamma"] = df.apply(lambda x: gamma(x["Option Type"], spot, x.Strike, 0.0027, 0.05, 0.2), axis=1)
        
        # Exposure calculations
        gamma_exposure = calculate_gamma_exposure(df, spot)
        delta_exposure = calculate_delta_exposure(df, spot)
        
        # Dynamic hedging calculation
        es_spot = price_data["ES"]["current"]
        required_move = (-delta_exposure * 1e9) / (gamma_exposure * 1e9 * es_spot) * 100
        hedge_strike = es_spot * (1 + required_move/100)
        
        # Display metrics
        cols = st.columns(4)
        cols[0].metric(f"{ticker} Gamma Exposure", f"${gamma_exposure:+.2f}Bn/1%")
        cols[1].metric(f"{ticker} Delta Exposure", f"${delta_exposure:+.2f}Bn")
        cols[2].metric("ES Hedge Points", f"{required_move:+.2f} pts")
        cols[3].metric("Equivalent Strike", f"{hedge_strike:,.2f}")

if __name__ == "__main__":
    main()
