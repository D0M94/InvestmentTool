import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from etf_loader import load_etfs
from factor_engine_v2 import compute_factors
from screener_engine_v2 import create_scorecard

# 🔧 BUILT-IN PERFORMANCE ANALYZER (No external dependency)
def analyze_tickers(tickers: list, period: str, risk_free_rate: float = 0.02):
    """Compute performance metrics + cumulative returns from price data"""
    cum_returns = pd.DataFrame()
    metrics = {}
    
    for ticker in tickers:
        try:
            # Load fresh data for this ticker
            data = load_etfs([ticker], period=period)
            if ticker in data and not data[ticker]["prices"].empty:
                prices = data[ticker]["prices"].set_index('Date')['Close']
                prices = prices.dropna()
                
                if len(prices) > 1:
                    returns = prices.pct_change().dropna()
                    cum_ret = (1 + returns).cumprod() - 1
                    years = (prices.index[-1] - prices.index[0]).days / 365.25
                    
                    cum_returns[ticker] = cum_ret
                    
                    # Performance metrics
                    total_return = cum_ret.iloc[-1]
                    annual_return = (1 + total_return) ** (1/years) - 1 if years > 0 else 0
                    annual_vol = returns.std() * np.sqrt(252)
                    sharpe = (annual_return - risk_free_rate) / annual_vol if annual_vol > 0 else 0
                    
                    metrics[ticker] = {
                        'Total Return': total_return,
                        'Annual Return': annual_return,
                        'Annual Volatility': annual_vol,
                        'Sharpe Ratio': sharpe
                    }
        except:
            pass  # Skip failed tickers
    
    return cum_returns, metrics

st.title("📊 Asset Scoring & Performance Comparison")

col1, col2 = st.columns(2)
with col1:
    tickers_input = st.text_input("Enter tickers (comma-separated)", "SPY, URTH, QQQ, EEM")
    tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
with col2:
    benchmark_input = st.text_input("Benchmark", "SPY")
    benchmark = benchmark_input.strip().upper()

period = st.selectbox("History period", ["1y", "2y", "5y", "10y", "max"], index=2)
rf_input = st.text_input("Risk-Free Rate", "2.00%")

try:
    risk_free_rate = float(rf_input.replace("%", "")) / 100
except:
    st.error("Please enter a valid percentage, e.g., 2.00%")
    st.stop()

def highlight_benchmark(row):
    if row.name == benchmark:
        return ['background-color: #FFC39B'] * len(row)
    return [''] * len(row)

if st.button("Analyze", type="primary"):
    with st.spinner("🔄 Computing scores & performance..."):
        # ✅ FIXED: Single cached load for ALL analysis
        all_tickers = tickers + ([benchmark] if benchmark not in tickers else [])
        etf_data = load_etfs(all_tickers, period=period)

        # Scoring (tickers only - exclude benchmark)
        scoring_data = {t: etf_data[t] for t in tickers if t in etf_data}
        factor_df = compute_factors(scoring_data, period=period)
        scorecard = create_scorecard(factor
