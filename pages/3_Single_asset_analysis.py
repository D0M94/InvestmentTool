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

def load_and_process_etf(tickers, period):
"""Cached ETF loader with processing - uses shared cache."""
try:
data = load_etfs(tickers, period=period) # Shared cached loader
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
if use_benchmark and benchmark_input and benchmark_input != ticker:
benchmark_data = load_and_process_etf([benchmark_input], period)
if benchmark_input in benchmark_data:
benchmark_price = benchmark_data[benchmark_input]

# === CUMULATIVE PERFORMANCE ===
st.subheader("Cumulative Performance")
fig1 = go.Figure()
fig1.add_trace(go.Scatter(
x=price.index, y=price["CumReturns"],
mode="lines", name=ticker,
line=dict(width=3, color="blue")
))

bench_cum_daily = None
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
else:
benchmark_price = None

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

if benchmark_price is not None and bench_cum_daily is not None:
bench_cum_final = bench_cum_daily.iloc[-1]
total_relative = total_ret - bench_cum_final
annual_relative = total_relative / years
main_rets = price["Returns"].dropna()
bench_rets = benchmark_price["Returns"].dropna()
common_idx = main_rets.index.intersection(bench_rets.index)
corr = beta = None
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
