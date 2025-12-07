import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import timedelta
from analysis import calculate_indicators

def _streamlit_context_exists() -> bool:
    """Return True when running inside a Streamlit script context."""
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        return get_script_run_ctx() is not None
    except Exception:
        return False

def cache_data_if_available(func=None, **cache_kwargs):
    """Wrap st.cache_data when a Streamlit script context exists."""
    def decorator(target):
        if _streamlit_context_exists():
            return st.cache_data(**cache_kwargs)(target)
        return target

    if func is not None:
        return decorator(func)
    return decorator

@cache_data_if_available
def fetch_data(tickers, start_date, end_date):
    # Fetch extra data prior to start_date to calculate MA200 correctly
    fetch_start = start_date - timedelta(days=400)
    data_dict = {}
    
    # 1. FETCH MACRO DATA (VIX + TNX)
    try:
        # FIX: Added auto_adjust=False to silence FutureWarnings
        vix = yf.download("^VIX", start=fetch_start, end=end_date, progress=False, auto_adjust=False)['Close']
        if isinstance(vix, pd.DataFrame): vix = vix.iloc[:, 0]
        
        tnx = yf.download("^TNX", start=fetch_start, end=end_date, progress=False, auto_adjust=False)['Close']
        if isinstance(tnx, pd.DataFrame): tnx = tnx.iloc[:, 0]
    except:
        # Fallback if download fails
        dates = pd.date_range(start=fetch_start, periods=1)
        vix = pd.Series(20, index=dates)
        tnx = pd.Series(4.0, index=dates)

    # 2. FETCH TICKER DATA
    for t in tickers:
        try:
            # FIX: Added auto_adjust=False
            df = yf.download(t, start=fetch_start, end=end_date, progress=False, auto_adjust=False)
            if df.empty: continue
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # Merge Macro Data
            df['VIX'] = vix.reindex(df.index).ffill()
            df['TNX'] = tnx.reindex(df.index).ffill()
            
            # Calculate Indicators
            df = calculate_indicators(df)
            
            mask = (df.index >= pd.Timestamp(start_date)) & (df.index <= pd.Timestamp(end_date))
            data_dict[t] = df.loc[mask]
        except Exception as e:
            print(f"Error fetching {t}: {e}")
            continue
            
    return data_dict