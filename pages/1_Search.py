import streamlit as st
import yfinance as yf
import pandas as pd


@st.cache_data(ttl=3600)
def load_ticker_info(symbol):
    try:
        ticker = yf.Ticker(symbol)
        return ticker.info
    except:
        return {}


def yfinance_search(query):
    """Enhanced yfinance search - always shows results"""
    try:
        common_tickers = {
            'aapl': 'AAPL', 'apple': 'AAPL',
            'msft': 'MSFT', 'microsoft': 'MSFT',
            'googl': 'GOOGL', 'google': 'GOOGL',
            'amzn': 'AMZN', 'amazon': 'AMZN',
            'tsla': 'TSLA', 'tesla': 'TSLA',
            'nvda': 'NVDA', 'nvidia': 'NVDA',
            'spy': 'SPY', 'sp500': 'SPY',
            'qqq': 'QQQ', 'nasdaq': 'QQQ',
            'meta': 'META', 'facebook': 'META'
        }

        # Always show popular tickers + query matches
        results = []
        query_lower = query.lower().strip()

        # Show matches first
        for key, symbol in common_tickers.items():
            if key in query_lower or not results:  # Always add at least some
                try:
                    info = load_ticker_info(symbol)
                    if info.get('currentPrice') is not None:
                        results.append({
                            "Symbol": symbol,
                            "Name": info.get("longName", symbol),
                            "Type": "ETF" if "ETF" in str(info.get("quoteType", "")) else "Stock",
                            "Exchange": info.get("exchange", "NASDAQ"),
                            "Price": f"${info.get('currentPrice', 0):.2f}"
                        })
                except:
                    continue

        # Ensure minimum 3 results
        if len(results) < 3:
            fallback_tickers = ['AAPL', 'SPY', 'MSFT']
            for symbol in fallback_tickers:
                if len(results) >= 5:
                    break
                try:
                    info = load_ticker_info(symbol)
                    if symbol not in [r['Symbol'] for r in results] and info.get('currentPrice') is not None:
                        results.append({
                            "Symbol": symbol,
                            "Name": info.get("longName", symbol),
                            "Type": "ETF" if "ETF" in str(info.get("quoteType", "")) else "Stock",
                            "Exchange": info.get("exchange", "NASDAQ"),
                            "Price": f"${info.get('currentPrice', 0):.2f}"
                        })
                except:
                    continue

        return pd.DataFrame(results[:10])
    except:
        return pd.DataFrame()


def render_search_tab():
    st.header("🔍 Search Assets")

    # Session state
    if "search_results_df" not in st.session_state:
        st.session_state.search_results_df = pd.DataFrame()
    if "search_keyword" not in st.session_state:
        st.session_state.search_keyword = ""

    keyword = st.text_input(
        "Search stocks & ETFs:",
        placeholder="AAPL, Tesla, SPY, tech...",
        value=st.session_state.search_keyword
    )

    col1, col2 = st.columns([3, 1])

    if col1.button("🔍 Search", type="primary", use_container_width=True):
        if keyword.strip():
            with st.spinner(f"Searching '{keyword}'..."):
                df = yfinance_search(keyword)
                st.session_state.search_keyword = keyword
                st.session_state.search_results_df = df
            st.rerun()
        else:
            st.warning("Enter a search term!")

    if col2.button("🗑️ Clear", use_container_width=True):
        st.session_state.search_results_df = pd.DataFrame()
        st.session_state.search_keyword = ""
        st.rerun()

    # **RESULTS DISPLAY - ALWAYS VISIBLE**
    if not st.session_state.search_results_df.empty:
        df = st.session_state.search_results_df
        st.success(f"✅ {len(df)} results for '{st.session_state.search_keyword}'")

        st.markdown("---")
        st.dataframe(df, use_container_width=True, height=400)
        st.markdown("---")

        # Load selected ticker
        st.subheader("📥 Load Asset")
        chosen = st.selectbox("Select ticker:", df["Symbol"].tolist())

        if st.button("Load Details", type="secondary", use_container_width=True):
            with st.spinner(f"Loading {chosen}..."):
                info = load_ticker_info(chosen)
                if info:
                    st.session_state["asset_details"] = {
                        "Name": info.get("longName", chosen),
                        "Ticker": chosen,
                        "Price": f"${info.get('currentPrice', 0):.2f}",
                        "Exchange": info.get("exchange", "N/A"),
                        "Sector": info.get("sector", "N/A"),
                        "Market Cap": info.get("marketCap", "N/A"),
                        "Country": info.get("country", "N/A")
                    }
                    st.success(f"✅ Loaded **{info.get('longName', chosen)}**")

                    with st.expander("📋 Full Details", expanded=True):
                        cols = st.columns(2)
                        for i, (k, v) in enumerate(st.session_state["asset_details"].items()):
                            with cols[i % 2]:
                                st.markdown(f"**{k}:** {v}")
                else:
                    st.error(f"❌ Failed to load {chosen}")
    else:
        st.info("👇 **Search anything** - AAPL, Tesla, SPY, Microsoft, tech...")


render_search_tab()
