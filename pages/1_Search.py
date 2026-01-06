import streamlit as st
import yfinance as yf
import pandas as pd
import requests


def search_financial_assets(query):
    """FMP API - Production-grade financial search (FREE 250/day)"""
    api_key = st.secrets.get("FMP_API_KEY", "")
    if not api_key:
        st.warning("🔑 Add FMP_API_KEY to Streamlit Secrets (free at financialmodelingprep.com)")
        return pd.DataFrame()

    # **FIX**: URL encode the query parameter to prevent 403 errors
    from urllib.parse import quote
    encoded_query = quote(query)
    url = f"https://financialmodelingprep.com/api/v3/search?query={encoded_query}&limit=20&apikey={api_key}"

    try:
        # **FIX**: Add proper headers to bypass 403 restrictions
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()

        data = response.json()

        if not isinstance(data, list):
            st.error(f"Invalid API response: {data}")
            return pd.DataFrame()

        if len(data) == 0:
            return pd.DataFrame()

        results = []
        for item in data[:15]:
            if not isinstance(item, dict):
                continue

            symbol = item.get("symbol", "")
            if not symbol:
                continue

            price_val = item.get('price')
            price_str = "N/A"
            if price_val is not None:
                try:
                    price_str = f"${float(price_val):.2f}"
                except:
                    price_str = "N/A"

            results.append({
                "Symbol": symbol,
                "Name": item.get("name", ""),
                "Type": item.get("type", "").replace("etf", "ETF").replace("stock", "Stock").title(),
                "Exchange": item.get("exchangeShortName") or item.get("exchange", "N/A"),
                "Price": price_str
            })

        return pd.DataFrame(results)

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            st.error("❌ 403 Forbidden - API key blocked or IP restricted. Try:\n"
                     "1. New free API key from financialmodelingprep.com\n"
                     "2. Different search term\n"
                     "3. Wait 1 hour (rate limiting)")
            st.info(
                "**Debug**: Test your key → https://financialmodelingprep.com/api/v3/search?query=AAPL&limit=5&apikey=YOUR_KEY")
        elif e.response.status_code == 429:
            st.error("❌ API rate limit exceeded. Try again later (250/day free tier).")
        elif e.response.status_code == 401:
            st.error("❌ Invalid FMP_API_KEY. Please check your secret.")
        else:
            st.error(f"❌ HTTP {e.response.status_code}: {e.response.text[:300]}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Search failed: {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_ticker_info(symbol):
    """Cached yfinance - prevents rate limits"""
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
        "Search assets (name, sector, theme):",
        placeholder="Apple, tech ETF, Europe stocks, dividend...",
        value=st.session_state.search_keyword
    )

    col1, col2 = st.columns([3, 1])
    search_clicked = col1.button("🔍 Search Assets", type="primary")
    clear_clicked = col2.button("Clear")

    if clear_clicked:
        st.session_state.search_results_df = pd.DataFrame()
        st.session_state.search_keyword = ""
        st.rerun()

    if search_clicked:
        if not keyword.strip():
            st.warning("Please enter a search keyword.")
            st.rerun()
            return

        with st.spinner(f"Searching for '{keyword}'..."):
            st.session_state.search_keyword = keyword
            df = search_financial_assets(keyword)

            if df.empty:
                st.info("👀 No results. Try: 'tech', 'energy ETF', 'Apple', 'SPY'")
                st.rerun()
                return

            df.set_index("Symbol", inplace=True)
            df = df.head(15)
            st.session_state.search_results_df = df
            st.rerun()

    if not st.session_state.search_results_df.empty:
        df = st.session_state.search_results_df
        st.subheader(f"Results for '{st.session_state.search_keyword}' ({len(df)} found)")

        def price_formatter(val):
            if pd.isna(val):
                return "N/A"
            if isinstance(val, str) and val.startswith('$'):
                return val
            try:
                return f"${float(val):.2f}"
            except:
                return "N/A"

        styled_df = df.style.format({"Price": price_formatter})
        st.dataframe(styled_df, use_container_width=True, hide_index=False)

        st.subheader("Load Selected Asset")
        chosen = st.selectbox("Select ticker:", df.index.tolist())

        if st.button("📥 Load Details", type="secondary"):
            with st.spinner(f"Loading {chosen}..."):
                info = load_ticker_info(chosen)

                if not info:
                    st.error(f"Failed to load {chosen}")
                    st.rerun()
                    return

                asset_data = {
                    "Name": info.get("longName") or info.get("shortName") or "N/A",
                    "Ticker": chosen,
                    "Type": info.get("quoteType", "").replace("EQUITY", "Stock").replace("ETF", "ETF"),
                    "Exchange": info.get("exchange", ""),
                    "Currency": info.get("currency", "N/A"),
                    "Price": f"${info.get('currentPrice', 0):.2f}"
                }

                if asset_data["Type"] == "Stock":
                    market_cap = info.get("marketCap", 0)
                    if isinstance(market_cap, (int, float)):
                        if market_cap >= 1e12:
                            market_cap = f"${market_cap / 1e12:.1f}T"
                        elif market_cap >= 1e9:
                            market_cap = f"${market_cap / 1e9:.1f}B"
                        else:
                            market_cap = f"${market_cap / 1e6:.0f}M"
                    asset_data.update({
                        "Sector": info.get("sector", "N/A"),
                        "Industry": info.get("industry", "N/A"),
                        "Market Cap": market_cap,
                        "Country": info.get("country", "N/A"),
                    })

                elif asset_data["Type"] == "ETF":
                    aum = info.get("totalAssets", 0)
                    if isinstance(aum, (int, float)):
                        aum = f"${aum / 1e9:.1f}B" if aum >= 1e9 else f"${aum / 1e6:.0f}M"
                    expense = info.get("netExpenseRatio", "N/A")
                    if isinstance(expense, (int, float)):
                        expense = f"{expense:.2%}"
                    asset_data.update({
                        "AUM": aum,
                        "Expense Ratio": expense,
                        "Issuer": info.get("fundFamily", "N/A"),
                        "Category": info.get("category", "N/A"),
                    })

                st.session_state["selected_ticker"] = chosen
                st.session_state["asset_details"] = asset_data
                st.success(f"✅ Loaded {asset_data['Name']}")

                with st.expander("📋 Full Details", expanded=True):
                    col1, col2 = st.columns(2)
                    for i, (key, value) in enumerate(asset_data.items()):
                        col = col1 if i % 2 == 0 else col2
                        col.markdown(f"**{key}:** {value}")
    else:
        st.info("🔍 Search for stocks, ETFs, or themes above!")


render_search_tab()
