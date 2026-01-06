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

    url = f"https://financialmodelingprep.com/api/v3/search?query={query}&limit=20&apikey={api_key}"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        # **CRITICAL FIX**: Validate data type before loop
        if not isinstance(data, list):
            st.error("Invalid API response format")
            return pd.DataFrame()

        results = []
        for item in data[:15]:
            # **CRITICAL FIX**: Check item is dict before .get()
            if not isinstance(item, dict):
                continue

            symbol = item.get("symbol", "")
            if not symbol:  # Skip empty symbols
                continue

            results.append({
                "Symbol": symbol,
                "Name": item.get("name", ""),
                "Type": item.get("type", "").replace("etf", "ETF").replace("stock", "Stock").title(),
                "Exchange": item.get("exchangeShortName") or item.get("exchange", "N/A"),
                # **FIXED**: Safe price handling
                "Price": f"${float(item.get('price', 0)):.2f}" if item.get('price') is not None else "N/A"
            })

        return pd.DataFrame(results)

    except Exception as e:
        st.error(f"Search failed: {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)  # Cache 1 hour
def load_ticker_info(symbol):
    """Cached yfinance - prevents rate limits"""
    try:
        ticker = yf.Ticker(symbol)
        return ticker.info
    except:
        return {}


def render_search_tab():
    st.header("🔍 Search Assets")

    # Initialize session state
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
            return

        with st.spinner(f"Searching for '{keyword}'..."):
            st.session_state.search_keyword = keyword
            df = search_financial_assets(keyword)

            if df.empty:
                st.info("👀 No results. Try: 'tech', 'energy ETF', 'Apple', 'SPY'")
                return

            df.set_index("Symbol", inplace=True)
            df = df.head(15)
            st.session_state.search_results_df = df
            st.rerun()

    # Show results
    if not st.session_state.search_results_df.empty:
        df = st.session_state.search_results_df
        st.subheader(f"Results for '{st.session_state.search_keyword}' ({len(df)} found)")

        # Enhanced table with styling
        styled_df = df.style.format({
            "Price": "${:.2f}"
        }).background_gradient(subset=["Price"], cmap="Greens")

        st.dataframe(styled_df, use_container_width=True, hide_index=False)

        st.subheader("Load Selected Asset")
        chosen = st.selectbox("Select ticker:", df.index.tolist())

        if st.button("📥 Load Details", type="secondary"):
            with st.spinner(f"Loading {chosen}..."):
                info = load_ticker_info(chosen)

                if not info:
                    st.error(f"Failed to load {chosen}")
                    return

                # Common fields
                asset_data = {
                    "Name": info.get("longName") or info.get("shortName") or "N/A",
                    "Ticker": chosen,
                    "Type": info.get("quoteType", "").replace("EQUITY", "Stock").replace("ETF", "ETF"),
                    "Exchange": info.get("exchange", ""),
                    "Currency": info.get("currency", "N/A"),
                    "Price": f"${info.get('currentPrice', 0):.2f}"
                }

                # Stock fields
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

                # ETF fields
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

                # Store and display
                st.session_state["selected_ticker"] = chosen
                st.session_state["asset_details"] = asset_data
                st.success(f"✅ Loaded {asset_data['Name']}")

                # Details display
                with st.expander("📋 Full Details", expanded=True):
                    col1, col2 = st.columns(2)
                    for i, (key, value) in enumerate(asset_data.items()):
                        col = col1 if i % 2 == 0 else col2
                        col.markdown(f"**{key}:** {value}")
    else:
        st.info("🔍 Search for stocks, ETFs, or themes above!")


render_search_tab()
