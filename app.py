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

# --- 2. SIDEBAR & USER INPUTS ---
with st.sidebar:
    # Set page navigation first and default to The Manifesto
    page = st.radio(
        "Go to:",
        ["The Manifesto", "Action Dashboard", "Backtest Performance"]
    )
    st.markdown("---")

    st.header("Smart Portfolio")
    
    st.write("**1. Select Assets**")
    st.caption("Type to search (e.g., 'Q' for QQQ)")
    
    selected_tickers = st.multiselect(
        "Search Tickers", 
        options=COMMON_TICKERS, 
        default=["VOO", "QQQ"]
    )
    
    # --- CUSTOM TICKER VALIDATION LOGIC ---
    custom_add = st.text_input("Add Custom Ticker (Optional)", placeholder="e.g. MSFT")
    if custom_add:
        t_upper = custom_add.upper()
        
        if t_upper in selected_tickers:
            st.info(f"{t_upper} is already in the list.")
        else:
            with st.spinner(f"Validating {t_upper}..."):
                try:
                    test_data = yf.Ticker(t_upper).history(period="5d")
                    
                    if test_data.empty:
                        st.error(f"Ticker '{t_upper}' not found. Please check spelling.")
                    else:
                        selected_tickers.append(t_upper)
                        st.success(f"Found {t_upper}! Added to list.")
                except Exception as e:
                    st.error(f"Error validating '{t_upper}'.")

    st.write("**2. Set Allocation (%)**")
    
    if not selected_tickers:
        st.warning("Please select at least one ticker.")
        df_input = pd.DataFrame(columns=["Ticker", "Weight (%)"])
    else:
        default_weight = 100.0 / len(selected_tickers)
        df_input = pd.DataFrame({
            "Ticker": selected_tickers,
            "Weight (%)": [default_weight] * len(selected_tickers)
        })
    
    edited_df = st.data_editor(
        df_input, 
        column_config={
            "Ticker": st.column_config.TextColumn("Ticker", disabled=True),
            "Weight (%)": st.column_config.NumberColumn("Weight", min_value=0, max_value=100, format="%.1f%%")
        },
        hide_index=True,
        use_container_width=True
    )
    
    tickers = edited_df["Ticker"].astype(str).str.upper().tolist()
    raw_weights = edited_df["Weight (%)"].fillna(0).tolist()
    
    total_raw = sum(raw_weights)
    if total_raw == 0 and len(tickers) > 0:
        final_weights = [100.0 / len(tickers)] * len(tickers)
    elif abs(total_raw - 100) > 0.01:
        final_weights = [(w / total_raw) * 100 for w in raw_weights]
        if total_raw != 0:
            st.caption(f"Note: Weights summed to {total_raw:.1f}%. Auto-balanced to 100%.")
    else:
        final_weights = raw_weights

    weights_dict = dict(zip(tickers, final_weights))
    monthly_budget = st.number_input("Monthly Base Budget ($)", value=3000, step=100)
    
# --- 3. PAGE ROUTING ---
if page == "The Manifesto":
    show_manifesto_page()
elif page == "Action Dashboard":
    show_dashboard_page(tickers, weights_dict, monthly_budget)
elif page == "Backtest Performance":
    show_backtest_page(tickers, weights_dict, monthly_budget)