import streamlit as st
from etf_loader import load_etfs
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Dom's Analytics Platform", layout="wide")

st.title("📊 Smart Money Tool: Find Winners & Beat Benchmarks")
col1, col2 = st.columns([4, 1])
with col1:
    st.caption("⭐ Dom's Smart Money Tools - Built for serious investors")
with col2:
    st.button("⭐ Love it?", key="love")

if st.button("💡 Quick Feedback (30 sec)"):
    st.text_area("What rocks? What sucks? Would you pay $10/mo for insights, more models, portfolio builder, etc.?")
    st.success("Thanks for the feedback!")

st.markdown("""
**Unlock your investment potential with Dom's Smart Money Tool.**  
*Find the best assets to your portfolio. Invest like the pros.*

Use the sidebar to navigate:

🔍 **Search** — Find the assets you want to analyze  
📊 **Performance and scoring** — Compare and rank chosen assets  
📈 **Single asset analysis** — Deep-dive view of single assets
""")

# Sidebar for multipage navigation
page = st.sidebar.selectbox("Choose a page", [
    "🔎 Single Asset Dashboard",
    "📊 Multi-Asset Comparison",
    "🔍 Asset Search"
])

if page == "🔎 Single Asset Dashboard":
    st.header("🔎 Single Asset Dashboard")

    # Inputs
    ticker = st.text_input("Ticker", "SPY").upper()
    period = st.selectbox("History", ["1y", "2y", "5y", "10y", "max"], index=1)
    benchmark_input = st.text_input("Benchmark (optional)", "QQQ").upper()
    use_benchmark = st.checkbox("Show benchmark", value=True)


    @st.cache_data(ttl=3600)  # 1 hour cache - KEY FIX
    def load_and_process_etf(tickers, period):
        """Cached ETF loader with processing."""
        try:
            data = load_etfs(tickers, period=period)
            processed = {}
            for ticker in tickers:
                if ticker in data and not data[ticker]["prices"].empty:
                    price = data[ticker]["prices"].copy()
                    if isinstance(price.columns, pd.MultiIndex):
                        price.columns = price.columns.get_level_values(0)
                    price = price[["Adj Close"]].dropna()
                    if price.empty:
                        continue
                    price["Returns"] = price["Adj Close"].pct_change()
                    price["RollingVol"] = price["Returns"].rolling(63, min_periods=21).std() * (252 ** 0.5)
                    price["CumReturns"] = (1 + price["Returns"].fillna(0)).cumprod() - 1
                    processed[ticker] = price
            return processed
        except Exception as e:
            st.error(f"Data loading failed: {str(e)}")
            return {}


    if st.button("Analyze", type="primary"):
        with st.spinner("Loading data..."):
            # FIXED: Load ALL tickers together in SINGLE API call
            all_tickers = [ticker]
            if use_benchmark and benchmark_input and benchmark_input != ticker:
                all_tickers.append(benchmark_input)

            all_data = load_and_process_etf(all_tickers, period)

            if ticker not in all_data or all_data[ticker].empty:
                st.error(f"No data found for {ticker}")
                st.stop()

            price = all_data[ticker]
            main_dates = price.index

            # Benchmark from shared cache
            benchmark_price = all_data.get(benchmark_input) if use_benchmark and benchmark_input else None

        # === CUMULATIVE PERFORMANCE ===
        st.subheader("Cumulative Performance")
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=price.index, y=price["CumReturns"],
            mode="lines", name=ticker,
            line=dict(width=3, color="blue")
        ))

        if benchmark_price is not None:
            bench_cum = benchmark_price["CumReturns"]
            bench_cum_daily = bench_cum.resample('D').ffill().reindex(main_dates, method='ffill')
            bench_cum_daily = bench_cum_daily.bfill().fillna(0)

            coverage_pct = (bench_cum_daily.dropna().size / len(main_dates)) * 100
            if coverage_pct > 50:
                fig1.add_trace(go.Scatter(
                    x=bench_cum_daily.index, y=bench_cum_daily,
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
            x=price.index, y=price["RollingVol"],
            mode="lines", name=f"{ticker} Vol",
            line=dict(width=3, color="blue")
        ))

        if benchmark_price is not None:
            bench_vol = benchmark_price["RollingVol"]
            coverage_pct = (bench_vol.dropna().size / len(main_dates)) * 100
            if coverage_pct > 50:
                fig2.add_trace(go.Scatter(
                    x=bench_vol.index, y=bench_vol,
                    mode="lines", name=f"{benchmark_input} Vol",
                    line=dict(width=3, dash="dash", color="#FF6B35")
                ))

        fig2.update_yaxes(tickformat=".1%")
        fig2.update_layout(height=400, template="plotly_white",
                           legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))
        st.plotly_chart(fig2, use_container_width=True)

        # === KEY METRICS ===
        st.subheader("Performance Metrics")
        years = (price.index[-1] - price.index[0]).days / 365.25
        total_ret = price["CumReturns"].iloc[-1]
        cagr = (1 + total_ret) ** (1 / years) - 1 if years > 0 else 0
        avg_vol = price["RollingVol"].mean()
        price_peak = price["Adj Close"].cummax()
        drawdown = (price_peak - price["Adj Close"]) / price_peak
        max_dd = drawdown.max()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total return", f"{total_ret:.1%}")
        col2.metric("CAGR", f"{cagr:.1%}")
        col3.metric("Avg. volatility", f"{avg_vol:.1%}")
        col4.metric("Max drawdown", f"-{max_dd:.1%}")

        if benchmark_price is not None:
            bench_cum_final = price["CumReturns"].iloc[-1] - benchmark_price["CumReturns"].iloc[
                -1]  # Simplified relative
            years = (price.index[-1] - price.index[0]).days / 365.25
            annual_relative = bench_cum_final / years

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Relative perf.", f"{bench_cum_final:.1%}")
            col2.metric("Annual relative", f"{annual_relative:.1%}")
            col3.metric("Status", "✅ Loaded", "Benchmark ready")
            col4.empty()

else:
    st.info(f"🛠️ Coming soon: {page}")
