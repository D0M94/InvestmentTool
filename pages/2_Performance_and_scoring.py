import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
import yfinance as yf
from etf_loader import load_etfs
from factor_engine_v2 import compute_factors
from screener_engine_v2 import create_scorecard
from performance_analyzer import analyze_tickers

st.title("📊 Asset Scoring & Performance Comparison")

# RATE LIMIT FIX: Process ONE ticker at a time
col1, col2 = st.columns(2)
with col1:
    tickers_input = st.text_input("Enter tickers (comma-separated)", "SPY,QQQ")
    tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
with col2:
    benchmark_input = st.text_input("Benchmark", "SPY")
    benchmark = benchmark_input.strip().upper()

period = st.selectbox("History period", ["1y", "2y"], index=0)  # Shorter periods = less data
rf_input = st.text_input("Risk-Free Rate", "2.00%")

try:
    risk_free_rate = float(rf_input.replace("%", "")) / 100
except:
    st.error("Please enter a valid percentage, e.g., 2.00%")
    st.stop()


# **CRITICAL**: Rate limiting wrapper
@st.cache_data(ttl=1800, max_entries=20)
def safe_yf_data(tickers_list, period_data):
    """Safe yfinance calls with delays"""
    results = {}
    for i, ticker in enumerate(tickers_list):
        if ticker in results:
            continue
        try:
            st.info(f"⏳ Loading {ticker} ({i + 1}/{len(tickers_list)})")
            time.sleep(1)  # 1 second delay between requests
            results[ticker] = yf.download(ticker, period=period_data, progress=False)
        except:
            st.warning(f"Failed to load {ticker}")
    return results


def highlight_benchmark(row):
    if row.name == benchmark:
        return ['background-color: #FFC39B'] * len(row)
    return [''] * len(row)


if st.button("🚀 Analyze (Rate-Limit Safe)", type="primary"):
    if len(tickers) > 3:
        st.error("⚠️ Limit to 3 tickers max to avoid rate limits")
        st.stop()

    with st.spinner("Loading data safely..."):
        try:
            # **FIX 1**: Load tickers ONE BY ONE with delays
            all_tickers = list(set(tickers + [benchmark]))
            ticker_data = safe_yf_data(all_tickers, period)

            # Check if we got data
            valid_tickers = [t for t in all_tickers if not ticker_data[t].empty]
            if len(valid_tickers) == 0:
                st.error("❌ No data loaded. Try SPY, QQQ, AAPL")
                st.stop()

            # **FIX 2**: Pass pre-loaded data to your functions
            factor_df = compute_factors(
                pd.concat([ticker_data[t] for t in tickers if not ticker_data[t].empty]),
                period=period
            )

            # Scoring
            scorecard = create_scorecard(factor_df)
            numeric_cols = scorecard.select_dtypes(include=['number']).columns
            styled_scorecard = scorecard.style.format(
                {col: "{:.2f}" for col in numeric_cols}
            ).apply(highlight_benchmark, axis=1)

            st.subheader("🏆 Asset Scorecard")
            st.dataframe(styled_scorecard, use_container_width=True)

            # Performance charts
            st.subheader("📈 Cumulative Performance")
            fig = go.Figure()

            cum_returns = {}
            for t in tickers:
                if t in ticker_data and not ticker_data[t].empty:
                    cum_returns[t] = (1 + ticker_data[t]['Close'].pct_change()).cumprod()
                    fig.add_trace(go.Scatter(
                        x=cum_returns[t].index,
                        y=cum_returns[t],
                        mode="lines",
                        name=t,
                        line=dict(width=2)
                    ))

            if benchmark in ticker_data and not ticker_data[benchmark].empty:
                cum_bench = (1 + ticker_data[benchmark]['Close'].pct_change()).cumprod()
                fig.add_trace(go.Scatter(
                    x=cum_bench.index,
                    y=cum_bench,
                    name=f"Benchmark ({benchmark})",
                    line=dict(width=2, dash="dash", color="#ff9900")
                ))

            fig.update_layout(height=500, template="plotly_white")
            fig.update_yaxes(tickformat=".0%")
            st.plotly_chart(fig, use_container_width=True)

            # Metrics table
            st.subheader("📊 Performance Metrics")
            metrics_df = pd.DataFrame(analyze_tickers(valid_tickers, period=period, risk_free_rate=risk_free_rate)).T

            pct_cols = ["Total Return", "Annual Return", "Annual Volatility"]
            for col in pct_cols:
                if col in metrics_df.columns:
                    metrics_df[col] = metrics_df[col] * 100

            styled_metrics = metrics_df.style.format({
                "Total Return": "{:.1f}%",
                "Annual Return": "{:.1f}%",
                "Annual Volatility": "{:.1f}%",
                "Sharpe Ratio": "{:.2f}"
            }).apply(highlight_benchmark, axis=1)

            st.dataframe(styled_metrics, use_container_width=True)

        except Exception as e:
            st.error(f"❌ Analysis failed: {str(e)}")
            st.info("👉 Try fewer tickers (max 3) and shorter periods (1y, 2y)")

st.info("💡 **Tips**: Use max 3 tickers, 1y/2y periods. SPY, QQQ, AAPL always work!")
