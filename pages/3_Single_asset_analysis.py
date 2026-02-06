import streamlit as st
import plotly.graph_objects as go
from etf_loader import load_etfs
import pandas as pd
import numpy as np

# Tighter spacing between titles and charts
st.markdown("""
<style>
/* Reduce gap between subheader and chart */
[data-testid="stSubheader"] h3 {
    margin-bottom: 0.3rem !important;
}
/* Reduce gap between charts */
div[data-testid="stPlotlyChart"] {
    margin-bottom: 0.5rem !important;
}
/* Reduce section padding */
.element-container {
    padding-top: 0.3rem !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🔎 Single Asset Dashboard")

ticker = st.text_input("Ticker", "SPY").upper()
period = st.selectbox("History", ["1y", "2y", "5y", "10y", "max"], index=1)
benchmark_input = st.text_input("Benchmark (optional)", "QQQ").upper()
use_benchmark = st.checkbox("Show benchmark", value=True)


@st.cache_data(ttl=3600, show_spinner=False)
def load_and_process_etf(tickers, period):
    """Cached ETF loader with processing - uses shared cache."""
    try:
        data = load_etfs(tickers, period=period)
        processed = {}
        for ticker in tickers:
            if ticker in data:
                price = data[ticker]["prices"].copy()
                if isinstance(price.columns, pd.MultiIndex):
                    price.columns = price.columns.get_level_values(0)
                price = price[["Adj Close"]].dropna()
                price["Returns"] = price["Adj Close"].pct_change()
                price["RollingVol"] = price["Returns"].rolling(63, min_periods=21).std() * (252 ** 0.5)
                price["CumReturns"] = (1 + price["Returns"].fillna(0)).cumprod() - 1
                # 1-year rolling returns (252 trading days)
                price["Rolling1YRet"] = price["Returns"].rolling(252, min_periods=63).apply(
                    lambda x: (1 + x).prod() ** (252 / len(x)) - 1 if len(x) > 0 else np.nan
                )
                # Drawdown
                price_peak = price["Adj Close"].cummax()
                price["Drawdown"] = (price["Adj Close"] - price_peak) / price_peak
                processed[ticker] = price
        return processed
    except Exception as e:
        st.error(f"Data loading failed: {str(e)}")
        return {}


if st.button("Analyze", type="primary"):
    with st.spinner("Loading data..."):
        main_data = load_and_process_etf([ticker], period)
        if ticker not in main_data or main_data[ticker].empty:
            st.error(f"No data found for {ticker}")
            st.stop()

        price = main_data[ticker]
        main_dates = price.index

        benchmark_price = None
        bench_cum_daily = None
        if use_benchmark and benchmark_input and benchmark_input != ticker:
            benchmark_data = load_and_process_etf([benchmark_input], period)
            if benchmark_input in benchmark_data:
                benchmark_price = benchmark_data[benchmark_input]

    small_height = 300
    large_height = 400
    main_vol_valid = price["RollingVol"].notna()

    # TOP CENTER LEGEND CONFIG
    legend_config = dict(yanchor="top", y=0.99, xanchor="center", x=0.5,
                         bgcolor="rgba(0,0,0,0)",  # Transparent background
                         bordercolor="rgba(0,0,0,0)"  # Transparent border
                         )

    # === 1. CUMULATIVE PERFORMANCE ===
    st.subheader("Cumulative Performance")
    fig_cum = go.Figure()
    fig_cum.add_trace(go.Scatter(
        x=price.index, y=price["CumReturns"],
        mode="lines", name=ticker,
        line=dict(width=2, color="#1ABC9C")
    ))
    if benchmark_price is not None:
        bench_cum = benchmark_price["CumReturns"]
        bench_cum_daily = bench_cum.resample('D').ffill().reindex(main_dates, method='ffill')
        bench_cum_daily = bench_cum_daily.bfill().fillna(0)
        coverage_pct = (bench_cum_daily.dropna().size / len(main_dates)) * 100
        if coverage_pct > 50:
            fig_cum.add_trace(go.Scatter(
                x=bench_cum_daily.index, y=bench_cum_daily,
                mode="lines", name=benchmark_input,
                line=dict(width=1.5, dash="dash", color="#0D3B36")
            ))
        else:
            benchmark_price = None
    fig_cum.update_yaxes(tickformat=".1%")
    fig_cum.update_layout(height=large_height, template="plotly_white",
                          legend=legend_config)
    st.plotly_chart(fig_cum, use_container_width=True)

    # === 2. ROLLING 1-YEAR RETURNS ===
    st.subheader("1-Year Rolling Returns")
    main_1y_valid = price["Rolling1YRet"].notna()
    main_1y_x = price.index[main_1y_valid]
    fig_1y = go.Figure()
    fig_1y.add_trace(go.Scatter(
        x=main_1y_x, y=price["Rolling1YRet"][main_1y_valid],
        mode="lines", name=ticker,
        line=dict(width=2, color="#1ABC9C")
    ))
    if benchmark_price is not None:
        bench_1y = benchmark_price["Rolling1YRet"].reindex(price.index, method='ffill').fillna(method='bfill')
        bench_1y_masked = bench_1y.where(main_1y_valid)
        bench_1y_valid_x = main_1y_x[bench_1y_masked[main_1y_x].notna()]
        if len(bench_1y_valid_x) / len(main_1y_x) > 0.5:
            fig_1y.add_trace(go.Scatter(
                x=bench_1y_valid_x, y=bench_1y_masked[bench_1y_valid_x],
                mode="lines", name=benchmark_input,
                line=dict(width=1.5, dash="dash", color="#0D3B36")
            ))
    fig_1y.update_xaxes(range=[main_1y_x[0], main_1y_x[-1]])
    fig_1y.update_yaxes(tickformat=".1%")
    fig_1y.update_layout(height=small_height, template="plotly_white",
                         legend=legend_config)
    st.plotly_chart(fig_1y, use_container_width=True)

    # === 3. ROLLING VOLATILITY ===
    st.subheader("3-Month Rolling Volatility")
    fig_vol = go.Figure()
    fig_vol.add_trace(go.Scatter(
        x=price.index[main_vol_valid], y=price["RollingVol"][main_vol_valid],
        mode="lines", name=f"{ticker} Vol",
        line=dict(width=2, color="#E05A4F")
    ))
    if benchmark_price is not None:
        bench_vol = benchmark_price["RollingVol"].reindex(price.index, method='ffill').fillna(method='bfill')
        bench_vol_masked = bench_vol.where(main_vol_valid)
        bench_vol_valid_x = price.index[main_vol_valid & bench_vol_masked.notna()]
        if len(bench_vol_valid_x) / len(price.index[main_vol_valid]) > 0.5:
            fig_vol.add_trace(go.Scatter(
                x=bench_vol_valid_x, y=bench_vol_masked[bench_vol_valid_x],
                mode="lines", name=f"{benchmark_input} Vol",
                line=dict(width=1.5, dash="dash", color="#B65C5C")
            ))
    fig_vol.update_yaxes(tickformat=".1%")
    fig_vol.update_layout(height=small_height, template="plotly_white",
                          legend=legend_config)
    st.plotly_chart(fig_vol, use_container_width=True)

    # === 4. 3-MONTH ROLLING CORRELATION ===
    st.subheader("3-Month Rolling Correlation")
    if benchmark_price is not None:
        main_rets = price["Returns"].dropna()
        bench_rets = benchmark_price["Returns"].dropna()
        common_idx = main_rets.index.intersection(bench_rets.index)
        if len(common_idx) > 90:
            common_main = main_rets.loc[common_idx]
            common_bench = bench_rets.loc[common_idx]
            corr_series = common_main.rolling(90, min_periods=30).corr(common_bench)
            corr_aligned = corr_series.reindex(price.index, method='ffill').fillna(method='bfill')
            corr_masked = corr_aligned.where(main_vol_valid)
            corr_valid_x = price.index[main_vol_valid & corr_masked.notna()]
            fig_corr = go.Figure()
            fig_corr.add_trace(go.Scatter(
                x=corr_valid_x, y=corr_masked[corr_valid_x],
                mode="lines", name=f"{ticker} vs {benchmark_input}",  # SPY vs QQQ legend
                line=dict(width=2, color="#F39C12")
            ))
            #fig_corr.update_yaxes(range=[-1, 1])
            fig_corr.update_layout(height=small_height, template="plotly_white",
                                   legend=legend_config)
            st.plotly_chart(fig_corr, use_container_width=True)
        else:
            st.warning("Insufficient overlapping data for correlation chart")
    else:
        st.info("ℹ️ Add benchmark for correlation")

    # === 5. DRAWDOWNS ===
    st.subheader("Drawdowns")
    fig_dd = go.Figure()
    fig_dd.add_trace(go.Scatter(
        x=price.index, y=price["Drawdown"],
        mode="lines", name=ticker,
        line=dict(width=2, color="#E05A4F"),
        fill='tozeroy'
    ))
    if benchmark_price is not None:
        bench_dd = benchmark_price["Drawdown"].reindex(price.index, method='ffill').fillna(method='bfill')
        coverage_pct = (bench_dd.dropna().size / len(price.index)) * 100
        if coverage_pct > 50:
            fig_dd.add_trace(go.Scatter(
                x=price.index, y=bench_dd,
                mode="lines", name=benchmark_input,
                line=dict(width=1.5, dash="dash", color="#B65C5C"),
                fill='tonexty'
            ))
    fig_dd.update_yaxes(tickformat=".1%")
    fig_dd.update_layout(height=small_height, template="plotly_white",
                         legend=dict(yanchor="bottom", y=0.01, xanchor="center", x=0.5, bgcolor="rgba(0,0,0,0)",  # Transparent background
                         bordercolor="rgba(0,0,0,0)"))  # Transparent border
    st.plotly_chart(fig_dd, use_container_width=True)

    # === KEY METRICS ===
    st.subheader(f"Performance metrics of {ticker}")
    years = (price.index[-1] - price.index[0]).days / 365.25
    total_ret = price["CumReturns"].iloc[-1]
    cagr = (1 + total_ret) ** (1 / years) - 1 if years > 0 else 0
    avg_vol = price["RollingVol"].mean()
    max_dd = price["Drawdown"].min()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total return", f"{total_ret:.1%}")
    col2.metric("CAGR", f"{cagr:.1%}")
    col3.metric("Avg. volatility", f"{avg_vol:.1%}")
    col4.metric("Max drawdown", f"{max_dd:.1%}")

    if benchmark_price is not None and bench_cum_daily is not None:
        bench_cum_final = bench_cum_daily.iloc[-1]
        total_relative = total_ret - bench_cum_final
        annual_relative = total_relative / years
        corr = beta = None
        main_rets = price["Returns"].dropna()
        bench_rets = benchmark_price["Returns"].dropna()
        common_idx = main_rets.index.intersection(bench_rets.index)
        if len(common_idx) > 30:
            common_main = main_rets.loc[common_idx]
            common_bench = bench_rets.loc[common_idx]
            corr = common_main.corr(common_bench)
            cov = common_main.cov(common_bench)
            beta = cov / common_bench.var()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total relative perf.", f"{total_relative:.1%}")
        col2.metric("Annual relative perf.", f"{annual_relative:.1%}")
        col3.metric("Correlation to benchmark", f"{corr:.3f}" if corr else "N/A")
        col4.metric("Beta", f"{beta:.2f}" if beta else "N/A")
    else:
        st.info("ℹ️ Add valid benchmark for relative metrics")
