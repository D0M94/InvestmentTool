import streamlit as st
import plotly.graph_objects as go
from etf_loader import load_etfs
import pandas as pd
import numpy as np

st.title("🔎 Single Asset Dashboard")

ticker = st.text_input("Ticker", "SPY").upper()
period = st.selectbox("History", ["1y", "2y", "5y", "10y", "max"], index=1)
benchmark_input = st.text_input("Benchmark (optional)", "QQQ").upper()
use_benchmark = st.checkbox("Show benchmark", value=True)

if st.button("Analyze", type="primary"):
    with st.spinner("Loading data..."):
        # ✅ FIXED: Single cache call
        all_tickers = [ticker]
        if use_benchmark and benchmark_input and benchmark_input != ticker:
            all_tickers.append(benchmark_input)
            
        raw_data = load_etfs(all_tickers, period=period)
        
        if ticker not in raw_data or raw_data[ticker]["prices"].empty:
            st.error(f"No data found for {ticker}")
            st.stop()

        # Process data locally
        def process_prices(price_df):
            if price_df.empty:
                return pd.DataFrame()
            price = price_df.set_index('Date')[['Close']].dropna()
            price["Returns"] = price["Close"].pct_change()
            price["RollingVol"] = price["Returns"].rolling(63, min_periods=21).std() * (252 ** 0.5)
            price["CumReturns"] = (1 + price["Returns"].fillna(0)).cumprod() - 1
            return price

        main_price = process_prices(raw_data[ticker]["prices"])
        benchmark_price = None
        
        if use_benchmark and benchmark_input in raw_data and not raw_data[benchmark_input]["prices"].empty:
            benchmark_price = process_prices(raw_data[benchmark_input]["prices"])

    # === CUMULATIVE PERFORMANCE ===
    st.subheader("Cumulative Performance")
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=main_price.index, y=main_price["CumReturns"],
        mode="lines", name=ticker,
        line=dict(width=3, color="blue")
    ))
    
    if benchmark_price is not None and not benchmark_price.empty:
        fig1.add_trace(go.Scatter(
            x=benchmark_price.index, y=benchmark_price["CumReturns"],
            mode="lines", name=benchmark_input,
            line=dict(width=3, dash="dash", color="#FF6B35")
        ))
    
    fig1.update_yaxes(tickformat=".1%")
    fig1.update_layout(height=400, template="plotly_white",
                       legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))
    st.plotly_chart(fig1, use_container_width=True)

    # === ROLLING VOLATILITY ===
    st.subheader("3-Month Rolling Volatility")
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=main_price.index, y=main_price["RollingVol"],
        mode="lines", name=f"{ticker} Vol",
        line=dict(width=3, color="blue")
    ))
    
    if benchmark_price is not None and not benchmark_price.empty:
        fig2.add_trace(go.Scatter(
            x=benchmark_price.index, y=benchmark_price["RollingVol"],
            mode="lines", name=f"{benchmark_input} Vol",
            line=dict(width=3, dash="dash", color="#FF6B35")
        ))
    
    fig2.update_yaxes(tickformat=".1%")
    fig2.update_layout(height=400, template="plotly_white",
                       legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))
    st.plotly_chart(fig2, use_container_width=True)

    # === KEY METRICS ===
    st.subheader("Performance Metrics")
    years = (main_price.index[-1] - main_price.index[0]).days / 365.25
    total_ret = main_price["CumReturns"].iloc[-1]
    cagr = (1 + total_ret) ** (1 / years) - 1 if years > 0 else 0
    avg_vol = main_price["RollingVol"].mean()
    price_peak = main_price["Close"].cummax()
    drawdown = (price_peak - main_price["Close"]) / price_peak
    max_dd = drawdown.max()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total return", f"{total_ret:.1%}")
    col2.metric("CAGR", f"{cagr:.1%}")
    col3.metric("Avg. volatility", f"{avg_vol:.1%}")
    col4.metric("Max drawdown", f"-{max_dd:.1%}")

    if benchmark_price is not None and not benchmark_price.empty:
        bench_cum_final = benchmark_price["CumReturns"].iloc[-1]
        total_relative = total_ret - bench_cum_final
        annual_relative = total_relative / years if years > 0 else 0
        
        main_rets = main_price["Returns"].drop
