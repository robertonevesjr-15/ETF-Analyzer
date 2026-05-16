import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(page_title="ETF 2-Year Profit Analyzer", layout="wide")
st.title("🚀 US ETF 2-Year Profit Analyzer")
st.markdown("### Analyze ETFs and project profit potential over the next 2 years")

# Sidebar
st.sidebar.header("Settings")
investment_amount = st.sidebar.number_input("Investment Amount ($)", min_value=1000, value=10000, step=1000)
period = st.sidebar.selectbox("Historical Data Period", ["1y", "2y", "5y", "max"], index=2)

etf_options = ["SPY", "QQQ", "VOO", "VTI", "SMH", "VUG", "IWM", "ARKK", "XLK", "XLF", "XLE"]
selected_etfs = st.sidebar.multiselect("Select ETFs to analyze", etf_options, default=["SPY", "QQQ", "VOO"])

if st.sidebar.button("Analyze ETFs", type="primary"):
    if not selected_etfs:
        st.error("Please select at least one ETF")
    else:
        with st.spinner("Fetching latest market data..."):
            results = {}
            for ticker in selected_etfs:
                try:
                    stock = yf.Ticker(ticker)
                    df = stock.history(period=period)
                    info = stock.info
                    
                    if df.empty:
                        continue
                    
                    # Metrics
                    closes = df['Close']
                    returns = closes.pct_change().dropna()
                    years = (closes.index[-1] - closes.index[0]).days / 365.25
                    cagr = (closes.iloc[-1] / closes.iloc[0]) ** (1 / years) - 1
                    
                    vol = returns.std() * np.sqrt(252)
                    sharpe = (returns.mean() - 0.04/252) / returns.std() * np.sqrt(252) if returns.std() != 0 else 0
                    
                    # Dividend, Expense, AUM
                    div_yield = round((info.get('dividendYield') or 0) * 100, 2)
                    expense = round((info.get('expenseRatio') or 0) * 100, 3)
                    aum = info.get('totalAssets') or info.get('netAssets')
                    aum_str = f"${aum/1e12:.2f}T" if aum and aum >= 1e12 else f"${aum/1e9:.1f}B" if aum else "N/A"
                    
                    # 2-Year Projection
                    daily_mu = cagr / 252
                    daily_sigma = vol / np.sqrt(252)
                    np.random.seed(42)
                    sim_returns = np.prod(1 + np.random.normal(daily_mu, daily_sigma, size=(10000, 504)), axis=1) - 1
                    proj = {
                        "Conservative": np.percentile(sim_returns, 25),
                        "Base": np.mean(sim_returns),
                        "Optimistic": np.percentile(sim_returns, 75)
                    }
                    
                    results[ticker] = {
                        "Current Price": round(closes.iloc[-1], 2),
                        "CAGR %": round(cagr * 100, 2),
                        "Volatility %": round(vol * 100, 2),
                        "Sharpe": round(sharpe, 2),
                        "Dividend Yield %": div_yield,
                        "Expense Ratio %": expense,
                        "AUM": aum_str,
                        "Projections": proj
                    }
                except:
                    st.warning(f"Could not load {ticker}")
            
            # Display Results
            for ticker, data in results.items():
                st.subheader(f"📊 {ticker}")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Current Price", f"${data['Current Price']}")
                    st.metric("CAGR (Historical)", f"{data['CAGR %']}%")
                with col2:
                    st.metric("Dividend Yield", f"{data['Dividend Yield %']}%")
                    st.metric("Expense Ratio", f"{data['Expense Ratio %']}%")
                with col3:
                    st.metric("AUM", data['AUM'])
                    st.metric("Sharpe Ratio", data['Sharpe'])
                
                st.write("**2-Year Profit Projection**")
                proj = data['Projections']
                cols = st.columns(3)
                for i, (scenario, ret) in enumerate(proj.items()):
                    profit = investment_amount * ret
                    with cols[i]:
                        st.metric(
                            f"{scenario} Case",
                            f"{ret*100:.1f}%",
                            f"+${profit:,.0f}"
                        )
                
                # Chart
                fig = stock.history(period=period)['Close'].plot(title=f"{ticker} Price History")
                st.pyplot(fig.figure)
                
                st.divider()

st.caption("⚠️ Educational tool only • Not financial advice • Past performance ≠ future results")
