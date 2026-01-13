import streamlit as st
import yfinance as yf
import pandas as pd
import time

def cached_yf_search(keyword: str) -> list:
    """Cached yfinance search."""
    time.sleep(0.2)
    try:
        return yf.Search(keyword, max_results=20).search().quotes
    except:
        return []

def cached_ticker_info(ticker: str) -> dict:
    """Cached ticker info."""
    time.sleep(0.2)
    try:
        return yf.Ticker(ticker).info
    except:
        return {}

def render_search_tab():
    st.header("🔍 Search for Assets")

    if "search_results_df" not in st.session_state:
        st.session_state.search_results_df = pd.DataFrame()
    if "search_keyword" not in st.session_state:
        st.session_state.search_keyword = ""

    keyword = st.text_input(
        "Enter asset name or ticker:",
        placeholder="Tesla, Apple, QQQ, Europe, Energy...",
        value=st.session_state.search_keyword
    )

    col1, col2 = st.columns([3, 1])
    search_clicked = col1.button("Search")
    clear_clicked = col2.button("Clear")

    if clear_clicked:
        st.session_state.search_results_df = pd.DataFrame()
        st.session_state.search_keyword = ""
        st.rerun()

    if search_clicked:
        if not keyword.strip():
            st.warning("Please enter a search keyword.")
            return

        try:
            st.session_state.search_keyword = keyword
            search_results = cached_yf_search(keyword)
        except Exception as e:
            st.error(f"Search failed: {e}")
            return

        if not search_results:
            st.info("No assets found. Try broader terms like 'Europe ETF' or exact tickers.")
            return

        df = pd.DataFrame([{
            "Symbol": q.get("symbol"),
            "Name": q.get("shortname") or q.get("longname", ""),
            "Type": q.get("quoteType", "").replace("EQUITY", "Stock").replace("ETF", "ETF"),
            "Exchange": q.get("exchange", ""),
        } for q in search_results])

        df.set_index("Symbol", inplace=True)
        df = df.head(15)
        st.session_state.search_results_df = df
        st.rerun()

    if not st.session_state.search_results_df.empty:
        df = st.session_state.search_results_df
        st.subheader(f"Search Results for '{st.session_state.search_keyword}' ({len(df)} found)")
        st.dataframe(df, use_container_width=True, hide_index=False)

        st.subheader("Load Selected Asset")
        chosen = st.selectbox("Select ticker to load:", df.index.tolist())

        if st.button("Load Ticker"):
            with st.spinner(f"Loading details for {chosen}..."):
                try:
                    info = cached_ticker_info(chosen)

                    asset_data = {
                        "Name": info.get("longName") or info.get("shortName") or "N/A",
                        "Ticker": chosen,
                        "Type": info.get("quoteType", "").replace("EQUITY", "Stock").replace("ETF", "ETF"),
                        "Exchange": info.get("exchange", ""),
                        "Currency": info.get("currency", "N/A"),
                    }

                    if asset_data["Type"] == "Stock":
                        market_cap = info.get("marketCap", "N/A")
                        if isinstance(market_cap, (int, float)):
                            if market_cap >= 1e12:
                                market_cap = f"${market_cap / 1e12:.1f}T"
                            elif market_cap >= 1e9:
                                market_cap = f"${market_cap / 1e9:.1f}B"
                            elif market_cap >= 1e6:
                                market_cap = f"${market_cap / 1e6:.1f}M"
                            else:
                                market_cap = f"${market_cap / 1e3:.0f}K"
                        asset_data.update({
                            "Sector": info.get("sector", "N/A"),
                            "Industry": info.get("industry", "N/A"),
                            "Market Cap": market_cap,
                            "Country": info.get("country", "N/A"),
                        })
                    elif asset_data["Type"] == "ETF":
                        market_cap = info.get("totalAssets", "N/A")
                        if isinstance(market_cap, (int, float)):
                            if market_cap >= 1e9:
                                market_cap = f"${market_cap / 1e9:.1f}B"
                            elif market_cap >= 1e6:
                                market_cap = f"${market_cap / 1e6:.1f}M"
                            else:
                                market_cap = f"${market_cap / 1e3:.0f}K"
                        expense_ratio = info.get("netExpenseRatio", "N/A")
                        if isinstance(expense_ratio, (int, float)):
                            expense_ratio = f"{(expense_ratio/100):.2%}"
                        asset_data.update({
                            "Expense Ratio": expense_ratio,
                            "Issuer": info.get("fundFamily", "N/A"),
                            "Category": info.get("category", "N/A"),
                            "AUM": market_cap,
                        })

                    st.session_state["selected_ticker"] = chosen
                    st.session_state["asset_details"] = asset_data

                    with st.expander("📋 Asset info", expanded=True):
                        col1, col2 = st.columns(2)
                        for i, (key, value) in enumerate(asset_data.items()):
                            col = col1 if i % 2 == 0 else col2
                            col.markdown(f"**{key}:** {value}")

                except Exception as e:
                    st.error(f"Failed to load details for {chosen}: {str(e)}")
                    st.session_state["selected_ticker"] = chosen
    else:
        st.info("👆 Search for assets above to get started")

render_search_tab()
