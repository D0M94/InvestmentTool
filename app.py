import streamlit as st
import yfinance as yf
from pathlib import Path
import os

# 🔧 FORCE REGENERATE CACHE BUTTON (CRITICAL)
CACHE_DIR = Path(".cache")
if st.sidebar.button("🗑️ **CLEAR ALL CACHE** (Fix empty data)"):
    if CACHE_DIR.exists():
        import shutil
        shutil.rmtree(CACHE_DIR)
    st.cache_data.clear()
    st.success("🧹 Cache cleared! Refresh page.")
    st.rerun()

# 🔧 YFINANCE CACHE DIR
CACHE_DIR.mkdir(exist_ok=True)
os.environ['YFINANCE_CACHE_DIR'] = str(CACHE_DIR / 'yfinance')

# 🔍 STATUS WITH CACHE DEBUG
with st.sidebar:
    st.markdown("### 🟢 Connection Status")
    cache_status = st.sidebar.radio("Cache mode:", ["Auto", "Force fresh data"], horizontal=True)
    force_fresh = cache_status == "Force fresh data"
    
    try:
        test_ticker = yf.Ticker("SPY")
        test_info = test_ticker.info
        test_price = test_ticker.history(period="5d")
        
        if test_price.empty:
            st.sidebar.error("❌ yfinance returning EMPTY data")
            st.sidebar.info("👆 Click CLEAR CACHE above")
        elif test_info:
            st.sidebar.success("✅ Live data: OK")
        else:
            st.sidebar.warning("⚠️ Partial data")
            
        st.sidebar.metric("Cache size", f"{len(list(CACHE_DIR.glob('**/*')))} files")
            
    except Exception as e:
        st.sidebar.error(f"💥 Network error: {str(e)[:100]}")
        st.sidebar.info("🗑️ Clear cache & retry")

# 🔧 PASS FORCE FRESH TO ALL PAGES
if "force_fresh_data" not in st.session_state:
    st.session_state.force_fresh_data = force_fresh

st.set_page_config(page_title="Dom's Analytics Platform", layout="wide")
# ... rest of your app.py unchanged ...
# Add this temporarily to test
if st.checkbox("🧪 Test yfinance NOW"):
    test_data = load_etfs(["SPY"], period="1mo")
    st.write("SPY data rows:", len(test_data["SPY"]["prices"]))
    st.dataframe(test_data["SPY"]["prices"].head())
