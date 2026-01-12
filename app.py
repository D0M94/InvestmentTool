# 🔥 BULLETPROOF YFINANCE + CACHE RESET (Jan 2026)
import os
import shutil
from pathlib import Path

# NUCLEAR CACHE RESET
if Path(".streamlit").exists():
    shutil.rmtree(".streamlit", ignore_errors=True)
if Path(".yfinance_cache").exists():
    shutil.rmtree(".yfinance_cache", ignore_errors=True)
if Path(".cache").exists():
    shutil.rmtree(".cache", ignore_errors=True)

# YFINANCE STREAMLIT CLOUD FIX
os.environ["YFINANCE_CACHE_DIR"] = ".yfinance_cache"
Path(".yfinance_cache").mkdir(exist_ok=True)

# Import AFTER reset
import streamlit as st
import yfinance as yf
import time

st.set_page_config(page_title="Dom's Analytics Platform", layout="wide")

# FORCE RELOAD TEST (runs once)
@st.cache_data(ttl=300, show_spinner="🔄 Testing yfinance...")
def test_yfinance():
    time.sleep(0.5)  # Rate limit
    spy = yf.Ticker("SPY")
    data = spy.history(period="5d")
    info = spy.info
    return {"data_shape": data.shape, "info_keys": list(info.keys())}

test_result = test_yfinance()
st.sidebar.markdown("### 🧪 Diagnostics")
st.sidebar.json(test_result)

st.title("📊 Smart Money Tool: Find Winners & Beat Benchmarks")
# ... rest of your UI code exactly the same
