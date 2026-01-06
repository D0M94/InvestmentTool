import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from urllib.parse import quote


def search_financial_assets(query):
    """FMP API - Try multiple endpoints + yfinance fallback"""
    api_key = st.secrets.get("FMP_API_KEY", "")
    if not api_key:
        st.warning("🔑 Add FMP_API_KEY to Streamlit Secrets")
        return pd.DataFrame()

    encoded_query = quote(query)

    endpoints = [
        f"https://financialmodelingprep.com/api/v3/search?query={encoded_query}&limit=20&apikey={api_key}",
        f"https://financialmodelingprep.com/api/v4/search?query={encoded_query}&limit=20&apikey={api_key}",
        f"https://financialmodelingprep.com/api/v3/stock/search?query={encoded_query}&limit=20&apikey={api_key}"
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    for i, url in enumerate(endpoints, 1):
        try:
            st.info(f"🔍 Trying endpoint {i}/3...")
            response = requests.get(url, timeout=10, headers=headers)
            st.info(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    st.success(f"✅ Endpoint {i} worked!")
                    results = []
                    for item in data[:15]:
                        if isinstance(item, dict) and item.get("symbol"):
                            price_str = "N/A"
                            price = item.get('price')
                            if price:
                                try:
                                    price_str = f"${float(price):.2f}"
                                except:
                                    pass

                            results.append({
                                "Symbol": item.get("symbol", ""),
                                "Name": item.get("name", ""),
                                "Type": item.get("type", "").replace("etf", "ETF").replace("stock", "Stock").title(),
                                "Exchange": item.get("exchangeShortName") or item.get("exchange", "N/A"),
                                "Price": price_str
                            })
                    return pd.DataFrame(results)

        except Exception as e:
            st.info(f"Endpoint {i} failed: {str(e)[:100]}")
            continue

    st.info("🔄 FMP failed - using yfinance search...")
    return yfinance_search(query)


def yfinance_search(query):
    """Fallback: Search via yfinance tickers"""
    try:
        common_tickers = {
            'aapl': 'AAPL', 'apple': 'AAPL', 'msft': 'MSFT', 'microsoft': 'MSFT',
            'googl': 'GOOGL', 'google': 'GOOGL', 'amzn': 'AMZN', 'amazon': 'AMZN',
            'tsla': 'TSLA', 'tesla': 'TSLA', 'nvda': 'NVDA', 'nvidia': 'NVDA',
            'spy': 'SPY', 'sp500': 'SPY', 'qqq': 'QQQ', 'nasdaq': 'QQQ'
        }

        results = []
        query_lower = query.lower()

        for key, symbol in common_tickers.items():
            if key in query_lower:
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    results.append({
                        "Symbol": symbol,
                        "Name": info.get("longName", symbol),
                        "Type": "ETF" if "ETF" in info.get("quoteType", "") else "Stock",
                        "Exchange": info.get("exchange", "N/A"),
                        "Price": f"${info.get('currentPrice', 0):.2f}"
                    })
                except:
                    continue

        return pd.DataFrame(results)
    except:
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_ticker_info(symbol):
    try:
        ticker = yf.Ticker(symbol)
        return ticker.info
    except:
        return {}


def render_search_tab():
    st.header("🔍 Search Assets")

    if "search_results_df" not in st.session_state:
        st.session_state.search_results_df = pd.DataFrame()
    if "search_keyword" not in st.session_state:
        st.session_state.search_keyword = ""

    keyword = st.text_input(
        "Search assets:",
        placeholder="AAPL, SPY, Tesla, tech",
        value=st.session_state.search_keyword
    )

    col1, col2 = st.columns([3, 1])
    if col1.button("🔍 Search", type="primary"):
        if keyword.strip():
            with st.spinner(f"Searching '{keyword}'..."):
                df = search_financial_assets(keyword)
                st.session_state.search_keyword = keyword
                st.session_state.search_results_df = df.head(15)
            st.rerun()

    if col2.button("Clear"):
        st.session_state.search_results_df = pd.DataFrame()
        st.session_state.search_keyword = ""
        st.rerun()

    if not st.session_state.search_results_df.empty:
        df = st.session_state.search_results_df
        st.subheader(f"✅ {len(df)} results for '{st.session_state.search_keyword}'")

        st.dataframe(df, use_container_width=True)

        if st.button("📥 Load First Result"):
            chosen = df.iloc[0]["Symbol"]
            with st.spinner(f"Loading {chosen}..."):
                info = load_ticker_info(chosen)
                if info:
                    st.session_state["asset_details"] = {
                        "Name": info.get("longName", chosen),
                        "Ticker": chosen,
                        "Price": f"${info.get('currentPrice', 0):.2f}",
                        "Exchange": info.get("exchange", ""),
                        "Sector": info.get("sector", "")
                    }
                    st.success(f"✅ Loaded {info.get('longName', chosen)}")

                    with st.expander("Details"):
                        for k, v in st.session_state["asset_details"].items():
                            st.markdown(f"**{k}:** {v}")
    else:
        st.info("🔍 Try: AAPL, SPY, Tesla, Microsoft")


render_search_tab()
