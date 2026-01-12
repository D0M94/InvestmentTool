# 🔧 YFINANCE STREAMLIT CLOUD FIX (REQUIRED)
import os
from pathlib import Path

os.environ["YFINANCE_CACHE_DIR"] = ".yfinance_cache"
Path(".yfinance_cache").mkdir(exist_ok=True)

import streamlit as st
import yfinance as yf  # Test import

st.set_page_config(page_title="Dom's Analytics Platform", layout="wide")

st.title("📊 Smart Money Tool: Find Winners & Beat Benchmarks")
col1, col2 = st.columns([4, 1])
with col1:
    st.caption("⭐ Dom's Smart Money Tools - Built for serious investors")
with col2:
    st.button("⭐ Love it?", key="love")

if st.button("💡 Quick Feedback (30 sec)"):
    st.text_area("What rocks? What sucks? Would you pay $10/mo for insights, more models, portfolio builder, etc.?",
                 key="feedback")

st.markdown("""
**Unlock your investment potential with Dom's Smart Money Tool.**  
*Find the best assets to your portfolio. Invest like the pros.*

**Navigate using the sidebar 👈**
""")

# ✅ Status monitor (PUBLIC SAFE)
with st.sidebar:
    st.markdown("### 🟢 Status")
    try:
        spy_info = yf.Ticker("SPY").info
        if spy_info.get('symbol'):
            st.sidebar.success("✅ Live data: OK")
        else:
            st.sidebar.warning("⚠️ Cache mode")
    except Exception as e:
        st.sidebar.info("💾 Cached data active")
    st.markdown("---")

# Sidebar navigation (your exact spec)
page = st.sidebar.radio(
    "Select Page:",
    options=[
        "🔍 Search",
        "📊 Performance and scoring",
        "📈 Single asset analysis"
    ],
    index=0,
    label_visibility="collapsed"
)

if page == "🔍 Search":
    import search

elif page == "📊 Performance and scoring":
    import performance_scoring

elif page == "📈 Single asset analysis":
    import single_asset
