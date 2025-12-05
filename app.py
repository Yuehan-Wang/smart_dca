import streamlit as st
import yfinance as yf
import pandas as pd
from config import COMMON_TICKERS, APP_STYLE
from ui_pages import show_manifesto_page, show_dashboard_page, show_backtest_page

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(
    page_title="Smart Portfolio Manager", 
    page_icon="📈",
    layout="wide"
)
st.markdown(APP_STYLE, unsafe_allow_html=True)

# --- 2. HELPER FUNCTIONS ---
def validate_ticker(ticker):
    """Checks if a ticker exists on Yahoo Finance."""
    t = ticker.upper().strip()
    if not t: return False, t
    try:
        # We fetch 5 days of history. If it's empty, the ticker likely doesn't exist.
        hist = yf.Ticker(t).history(period="5d")
        if hist.empty:
            return False, t
        return True, t
    except Exception:
        return False, t

def add_ticker_to_portfolio():
    """Callback to add the typed ticker from text input."""
    t_raw = st.session_state.ticker_input_bar
    if not t_raw: return

    # 1. Validate
    with st.spinner(f"Validating '{t_raw}'..."):
        is_valid, t_clean = validate_ticker(t_raw)
    
    if not is_valid:
        st.error(f"Ticker '{t_raw}' not found or invalid.")
        return

    # 2. Add to Session State
    current_df = st.session_state['portfolio_df']
    
    if t_clean in current_df['Ticker'].values:
        st.warning(f"'{t_clean}' is already in your portfolio.")
    else:
        # Create new row (Weight 0.0 initially, but Auto-Equalize will fix it if enabled)
        new_row = pd.DataFrame([{"Ticker": t_clean, "Weight (%)": 0.0, "Remove": False}])
        st.session_state['portfolio_df'] = pd.concat([current_df, new_row], ignore_index=True)
        st.toast(f"Added {t_clean}", icon="✅")

    # 3. Clear Input
    st.session_state.ticker_input_bar = ""

# --- 3. SIDEBAR & NAVIGATION ---
with st.sidebar:
    page = st.radio(
        "Go to:",
        ["The Manifesto", "Action Dashboard", "Backtest Performance"]
    )
    st.markdown("---")
    st.header("Smart Portfolio")

    # --- INITIALIZE SESSION STATE ---
    if 'portfolio_df' not in st.session_state:
        st.session_state['portfolio_df'] = pd.DataFrame({
            "Ticker": ["VOO", "QQQ"],
            "Weight (%)": [50.0, 50.0],
            "Remove": [False, False]
        })
    
    if "Remove" not in st.session_state['portfolio_df'].columns:
        st.session_state['portfolio_df']["Remove"] = False

    # --- 1. SINGLE SEARCH BAR ---
    st.write("**1. Add Assets**")
    st.caption("Type any ticker (e.g. **VOO**, **NVDA**, **BTC-USD**) and hit Enter.")
    
    st.text_input(
        "Add Ticker", 
        key="ticker_input_bar",
        placeholder="Type ticker symbol here...",
        label_visibility="collapsed",
        on_change=add_ticker_to_portfolio
    )

    # --- 2. WEIGHTING LOGIC ---
    st.write("**2. Portfolio Weights**")
    use_equal_weights = st.checkbox("Force Equal Weights (1/N)", value=True, help="Automatically splits 100% evenly across all assets.")
    
    # Logic: If Equal Weights is ON, recalculate immediately
    if use_equal_weights:
        count = len(st.session_state['portfolio_df'])
        if count > 0:
            st.session_state['portfolio_df']["Weight (%)"] = 100.0 / count
        # Disable editing if auto-calculated
        weight_column_config = st.column_config.NumberColumn("Weight", format="%.1f%%", disabled=True)
    else:
        # Allow editing
        weight_column_config = st.column_config.NumberColumn("Weight", min_value=0, max_value=100, format="%.1f%%")

    # --- 3. EDITABLE TABLE ---
    # We use a temporary DF to capture edits
    edited_df = st.data_editor(
        st.session_state['portfolio_df'],
        column_config={
            "Ticker": st.column_config.TextColumn("Ticker", disabled=True),
            "Weight (%)": weight_column_config,
            "Remove": st.column_config.CheckboxColumn("Remove?", width="small")
        },
        hide_index=True,
        use_container_width=True,
        num_rows="fixed", 
        key="portfolio_editor" 
    )
    
    # --- DELETE / UPDATE LOGIC ---
    if edited_df["Remove"].any():
        # Remove checked rows
        cleaned_df = edited_df[~edited_df["Remove"]].copy()
        cleaned_df["Remove"] = False
        st.session_state['portfolio_df'] = cleaned_df
        st.rerun()
    else:
        # Update weights (only matters if Force Equal Weights is OFF)
        st.session_state['portfolio_df'] = edited_df

    # --- PREPARE DATA FOR APP ---
    final_df = st.session_state['portfolio_df']
    tickers = final_df["Ticker"].astype(str).str.upper().tolist()
    raw_weights = final_df["Weight (%)"].fillna(0).tolist()
    
    # Normalize weights (Safety check for Manual Mode)
    total_raw = sum(raw_weights)
    if total_raw == 0 and len(tickers) > 0:
        final_weights = [100.0 / len(tickers)] * len(tickers)
    elif not use_equal_weights and abs(total_raw - 100) > 0.01:
        if total_raw != 0:
            final_weights = [(w / total_raw) * 100 for w in raw_weights]
            st.caption(f"Weights summed to {total_raw:.1f}%. Auto-balanced to 100%.")
        else:
            final_weights = raw_weights
    else:
        final_weights = raw_weights

    weights_dict = dict(zip(tickers, final_weights))
    
# --- 4. PAGE ROUTING ---
if page == "The Manifesto":
    show_manifesto_page()
elif page == "Action Dashboard":
    show_dashboard_page(tickers, weights_dict)
elif page == "Backtest Performance":
    show_backtest_page(tickers, weights_dict)