import streamlit as st
import yfinance as yf
import pandas as pd
import openai
from openai import OpenAI

# Initialize OpenAI (add your key to Streamlit secrets)
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", "your-key-here"))


def ai_ticker_search(query):
    """AI-powered ticker search - understands natural language"""
    system_prompt = """You are a financial search expert. Given a query, return EXACTLY 15 valid stock/ETF tickers 
    with their full names and type. Format each result as: TICKER|Name|Type|Exchange

    Examples:
    AAPL|Apple Inc|Stock|NASDAQ
    QQQ|Invesco QQQ Trust|ETF|NASDAQ
    SPY|SPDR S&P 500 ETF|ETF|NYSE

    Rules:
    - Only real, traded tickers (no made-up symbols)
    - Prefer US-listed ETFs/Stocks
    - For "Europe ETF" → VGK, IEUR, etc.
    - For "tech" → QQQ, VGT, FTEC, etc.
    - Always include major names (SPY, QQQ, AAPL, etc.)
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Cheap + fast
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Search: '{query}'. Return 15 results."}
            ],
            max_tokens=1000,
            temperature=0.1  # Precise results
        )

        # Parse AI response
        results = []
        lines = response.choices[0].message.content.strip().split('\n')
        for line in lines[:15]:
            if '|' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 3:
                    results.append({
                        "Symbol": parts[0],
                        "Name": parts[1],
                        "Type": parts[2],
                        "Exchange": parts[3] if len(parts) > 3 else "N/A"
                    })

        return pd.DataFrame(results)

    except Exception as e:
        st.error(f"AI search failed: {e}")
        return pd.DataFrame()


def render_search_tab():
    st.header("🔍 AI-Powered Asset Search")

    # Initialize session state for search results
    if "search_results_df" not in st.session_state:
        st.session_state.search_results_df = pd.DataFrame()
    if "search_keyword" not in st.session_state:
        st.session_state.search_keyword = ""

    # Better placeholder - AI understands natural language
    keyword = st.text_input(
        "Enter asset name, theme, or description:",
        placeholder="Tesla, tech ETFs, Europe stocks, dividend aristocrats, gold...",
        value=st.session_state.search_keyword
    )

    col1, col2 = st.columns([3, 1])
    search_clicked = col1.button("🔍 AI Search", type="primary")
    clear_clicked = col2.button("Clear")

    if clear_clicked:
        st.session_state.search_results_df = pd.DataFrame()
        st.session_state.search_keyword = ""
        st.rerun()

    if search_clicked:
        if not keyword.strip():
            st.warning("Please enter a search keyword.")
            return

        with st.spinner(f"🤖 AI searching for '{keyword}'..."):
            try:
                st.session_state.search_keyword = keyword
                df = ai_ticker_search(keyword)

                if df.empty:
                    st.info("🤔 AI couldn't find matches. Try: 'tech ETF', 'dividend stocks', exact tickers.")
                    return

                df.set_index("Symbol", inplace=True)
                st.session_state.search_results_df = df.head(15)
                st.rerun()

            except Exception as e:
                st.error(f"Search failed: {e}")
                return

    # Show search results if available
    if not st.session_state.search_results_df.empty:
        df = st.session_state.search_results_df
        st.subheader(f"🤖 AI Results for '{st.session_state.search_keyword}' ({len(df)} found)")
        st.dataframe(df, use_container_width=True, hide_index=False)

        st.subheader("Load Selected Asset")
        chosen = st.selectbox("Select ticker to load:", df.index.tolist())

        if st.button("📥 Load Ticker", type="secondary"):
            with st.spinner(f"Loading details for {chosen}..."):
                try:
                    ticker = yf.Ticker(chosen)
                    info = ticker.info

                    # Common fields for all assets
                    asset_data = {
                        "Name": info.get("longName") or info.get("shortName") or "N/A",
                        "Ticker": chosen,
                        "Type": info.get("quoteType", "").replace("EQUITY", "Stock").replace("ETF", "ETF"),
                        "Exchange": info.get("exchange", ""),
                        "Currency": info.get("currency", "N/A"),
                    }

                    # Stock-specific fields - FORMATTED Market Cap
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

                    # ETF-specific fields
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
                            expense_ratio = f"{(expense_ratio / 100):.2%}"

                        asset_data.update({
                            "Expense Ratio": expense_ratio,
                            "Issuer": info.get("fundFamily", "N/A"),
                            "Category": info.get("category", "N/A"),
                            "AUM": market_cap,
                        })

                    # Store in session state
                    st.session_state["selected_ticker"] = chosen
                    st.session_state["asset_details"] = asset_data

                    st.success(f"✅ Loaded {asset_data['Name']} ({chosen})")

                    # Compact table solution
                    with st.expander("📋 Asset Details", expanded=True):
                        col1, col2 = st.columns(2)
                        for i, (key, value) in enumerate(asset_data.items()):
                            col = col1 if i % 2 == 0 else col2
                            col.markdown(f"**{key}:** {value}")

                except Exception as e:
                    st.error(f"Failed to load details for {chosen}: {str(e)}")
                    st.session_state["selected_ticker"] = chosen
    else:
        st.info("👆 Enter natural language search like 'tech ETFs' or 'dividend stocks' to get started!")


render_search_tab()
