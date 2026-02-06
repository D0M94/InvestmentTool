import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from etf_loader import load_etfs
from factor_engine_v2 import compute_factors
from screener_engine_v2 import create_scorecard
from performance_analyzer import analyze_tickers, compute_correlation_matrix

st.set_page_config(page_title="Asset Scoring", layout="wide")
st.title("📊 Asset Scoring & Performance Comparison")

# --- Sidebar / Inputs ---
col1, col2 = st.columns(2)
with col1:
    tickers_input = st.text_input("Enter tickers (comma-separated)", "SPY, QQQ, SMH, IGV, CIBR")
    tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
with col2:
    benchmark_input = st.text_input("Benchmark (Baseline for Z-Scores)", "SPY")
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
        return ['border: 1px solid #777; font-weight: bold'] * len(row)
    return [''] * len(row)


if st.button("Analyze"):
    if not tickers:
        st.warning("Please enter at least one ticker.")
        st.stop()

    all_tickers = list(set(tickers + [benchmark]))

    with st.spinner("🔄 Computing Framework..."):
        etf_data = load_etfs(all_tickers, period=period)
        factor_df = compute_factors(etf_data, period=period)
        cum_df, metrics = analyze_tickers(all_tickers, period=period, risk_free_rate=risk_free_rate)

        # --- SECTION 1: FACTOR DNA SCORECARD (Fixed 2 Decimals) ---
        st.subheader("🧬 Factor DNA Scorecard")
        st.caption(f"Z-Scores relative to {benchmark}.")

        scorecard = create_scorecard(factor_df, is_etf=True, benchmark_ticker=benchmark)

        # Round numeric data
        numeric_cols = scorecard.select_dtypes(include=[np.number]).columns
        scorecard[numeric_cols] = scorecard[numeric_cols].round(2)

        # Format display (subset prevents ValueError on strings)
        st.dataframe(
            scorecard.style.apply(highlight_benchmark, axis=1).format(
                subset=numeric_cols,
                formatter="{:.2f}"
            ),
            use_container_width=True
        )

        # --- SECTION 2: CUMULATIVE PERFORMANCE ---
        st.subheader("📈 Cumulative Performance")
        fig_perf = go.Figure()
        for t in tickers:
            if t in cum_df.columns:
                fig_perf.add_trace(go.Scatter(x=cum_df.index, y=cum_df[t], mode="lines", name=t))

        if benchmark in cum_df.columns:
            fig_perf.add_trace(go.Scatter(
                x=cum_df.index, y=cum_df[benchmark],
                mode="lines", name=f"Benchmark ({benchmark})",
                line=dict(dash="dash", color="white", width=2)
            ))

        fig_perf.update_layout(template="plotly_dark", height=450)
        fig_perf.update_yaxes(tickformat=".1%")
        st.plotly_chart(fig_perf, use_container_width=True)

        # --- SECTION 3: REVERSED BRANDED CORRELATION HEATMAP ---
        st.subheader("🔗 Factor Synergy: Correlation Matrix")

        price_dict = {}
        for t in all_tickers:
            if t in etf_data and not etf_data[t]["prices"].empty:
                try:
                    s = etf_data[t]["prices"]["Adj Close"].squeeze()
                    if isinstance(s, pd.DataFrame): s = s.iloc[:, 0]
                    price_dict[t] = s
                except:
                    continue

        prices_df = pd.DataFrame(price_dict).dropna()

        if not prices_df.empty and len(prices_df.columns) > 1:
            corr_matrix = compute_correlation_matrix(prices_df)

            # --- POLES REVERSED ---
            # Teal is now Negative (0.0), Red is now Positive (1.0)
            brand_colors_reversed = [
                [0.0, "#16A085"],  # Strong negative (Brand Teal)
                [0.25, "#A7D6C9"],  # Mild negative (Light sage)
                [0.5, "#F2F4F3"],  # Neutral (Warm light grey)
                [0.75, "#E6CFC8"],  # Mild positive (Soft sand)
                [1.0, "#C97A6A"]  # Strong positive (Muted clay red)
            ]

            fig_corr = px.imshow(
                corr_matrix,
                text_auto=".2f",
                aspect="auto",
                color_continuous_scale=brand_colors_reversed,
                range_color=[-1, 1],
                labels=dict(color="Correlation")
            )

            fig_corr.update_layout(
                height=600,
                font=dict(size=16),
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            fig_corr.update_traces(textfont_size=18)
            st.plotly_chart(fig_corr, use_container_width=True)
        else:
            st.info("Add more tickers to see correlation.")

        # --- SECTION 4: PERFORMANCE METRICS (2 DECIMALS) ---
        st.subheader("📋 Performance Metrics")
        metrics_df = pd.DataFrame(metrics).T

        pct_cols = ["Total Return", "Annual Return", "Annual Volatility"]
        for col in pct_cols:
            if col in metrics_df.columns:
                metrics_df[col] = (metrics_df[col] * 100)

        st.table(metrics_df.style.format({
            "Total Return": "{:.2f}%",
            "Annual Return": "{:.2f}%",
            "Annual Volatility": "{:.2f}%",
            "Sharpe Ratio": "{:.2f}"
        }, na_rep="-"))