import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import timedelta
from analysis import calculate_indicators

@st.cache_data
def fetch_data(tickers, start_date, end_date):
    # Fetch extra data prior to start_date to calculate MA200 correctly
    fetch_start = start_date - timedelta(days=400)
    data_dict = {}
    
    try:
        vix = yf.download("^VIX", start=fetch_start, end=end_date, progress=False)['Close']
        if isinstance(vix, pd.DataFrame): vix = vix.iloc[:, 0] 
    except:
        vix = pd.Series(20, index=pd.date_range(start=fetch_start, periods=1))
    for t in tickers:
        try:
            df = yf.download(t, start=fetch_start, end=end_date, progress=False)
            if df.empty: continue
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
                
            df = calculate_indicators(df)
            df['VIX'] = vix.reindex(df.index).fillna(method='ffill')
            
            mask = (df.index >= pd.Timestamp(start_date)) & (df.index <= pd.Timestamp(end_date))
            data_dict[t] = df.loc[mask]
        except:
            continue
            
    return data_dict