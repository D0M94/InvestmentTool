import streamlit as st
import yfinance as yf
from pathlib import Path
import os
import shutil

# 🔧 CACHE BUSTER (SIDEBAR ONLY)
def clear_all_cache():
    cache_dir = Path(".cache")
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
    st.cache_data.clear()
    st.success("🧹 Cache cleared! Refresh page.")
    st.rerun()

st.set_page_config(page_title="Dom's Analytics Platform", layout="wide")

# 🔍 STATUS + CACHE CONTROLS (SIDEBAR)
with st.sidebar:
    st.markdown("### 🟢 Connection Status")
    
    # Cache controls
    col1, col2 = st.columns(2)
    if col1.button("🗑️ Clear Cache", use_container_width=True):
        clear_all_cache()
    
    cache_mode = st.radio("Data mode:", ["📡 Live", "💾 Cached"], horizontal=True, key="cache_mode")
    st.session_state.force_fresh = (cache_mode == "📡 Live")
    
    # Test connection
    try:
        test_ticker = yf.Ticker("SPY")
        test_price = test_ticker.history(period="5d")
        if not test_price.empty:
            st.success("✅ yfinance: LIVE ✓")
            st.caption(f"Sample: {len(test_price)} days")
        else:
            st.error("❌ Empty data detected")
            st.info("👆 Clear cache above")
    except Exception as e:
        st.error(f"💥 Network: {str(e)[:50]}")
    
    st.divider()
    st.markdown("---")

st.title("📊 Smart Money Tool: Find Winners & Beat Benchmarks")
col1, col2 = st.columns([4, 1])
with col1:
    st.caption("⭐ Dom's Smart Money Tools - Built for serious investors")
with col2:
    st.button("⭐ Love it?", key="love")

if st.button("💡 Quick Feedback (30 sec)"):
    st.text_area("What rocks? What sucks? Would you pay $10/mo?")

st.markdown("""
**Unlock your investment potential with Dom's Smart Money Tool.**  
*Find the best assets to your portfolio. Invest like the pros.*

**Sidebar navigation:**
- 🔍 **Search** — Find assets  
- 📊 **Performance & scoring** — Compare portfolios  
- 📈 **Single asset** — Deep analysis
""")

# 🔧 PAGE NAVIGATION (Add your existing page logic here)
# Your existing multi-page code goes here...
