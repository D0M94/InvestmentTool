import streamlit as st
# 🔍 PUBLIC STATUS MONITOR (add after imports in app.py)
with st.sidebar:
    st.markdown("### 🟢 Connection Status")
    try:
        import yfinance as yf
        test_info = yf.Ticker("SPY").info
        if test_info:
            st.sidebar.success("✅ Live data: OK")
        else:
            st.sidebar.warning("⚠️ Cache mode")
    except:
        st.sidebar.info("💾 Using cached data")

st.set_page_config(page_title="Dom's Analytics Platform", layout="wide")

st.title("📊 Smart Money Tool: Find Winners & Beat Benchmarks")
col1, col2 = st.columns([4, 1])
with col1:
    st.caption("⭐ Dom's Smart Money Tools - Built for serious investors")
with col2:
    st.button("⭐ Love it?", key="love")

if st.button("💡 Quick Feedback (30 sec)"):
    st.text_area("What rocks? What sucks? Would you pay $10/mo for insights, more models, portfolio builder, etc.?")

st.markdown("""
**Unlock your investment potential with Dom's Smart Money Tool.**  
*Find the best assets to your portfolio. Invest like the pros.*

Use the sidebar to navigate:

🔍 **Search** — Find the assets you want to analyze  
📊 **Performance and scoring** — Compare and rank chosen assets  
📈 **Single asset analysis** — Deep-dive view of single assets
""")

