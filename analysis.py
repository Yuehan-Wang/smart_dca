import pandas as pd
import numpy as np

def calculate_indicators(df):
    """Calculates RSI, BB, MA50, MA200, MACD, and Impulse MACD"""
    
    # 1. RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # 2. Bollinger Bands
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['STD20'] = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['MA20'] + (df['STD20'] * 2)
    df['BB_Lower'] = df['MA20'] - (df['STD20'] * 2)
    
    # 3. Moving Averages
    df['MA50'] = df['Close'].rolling(window=50).mean()
    df['MA200'] = df['Close'].rolling(window=200).mean()
    
    # 4. MACD & Impulse System
    exp12 = df['Close'].ewm(span=12, adjust=False).mean()
    exp26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD_Line'] = exp12 - exp26
    df['MACD_Signal'] = df['MACD_Line'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD_Line'] - df['MACD_Signal']
    
    # Impulse Components
    df['EMA13'] = df['Close'].ewm(span=13, adjust=False).mean()
    prev_ema = df['EMA13'].shift(1)
    prev_hist = df['MACD_Hist'].shift(1)
    
    df['Impulse'] = 'Blue' 
    mask_valid = prev_ema.notna() & prev_hist.notna()
    
    if len(df) > 1:
        mask_green = mask_valid & (df['EMA13'] > prev_ema) & (df['MACD_Hist'] > prev_hist)
        mask_red = mask_valid & (df['EMA13'] < prev_ema) & (df['MACD_Hist'] < prev_hist)
        df.loc[mask_green, 'Impulse'] = 'Green'
        df.loc[mask_red, 'Impulse'] = 'Red'
    
    return df

# --- V1: ORIGINAL BLUNT INSTRUMENT ---
def get_strategy_v1(price, indicators, vix_val):
    if vix_val > 30: return 2.0, "V1: PANIC"
    if price < indicators.get('MA200', np.inf): return 1.6, "V1: VALUE" 
    if indicators.get('RSI', 50) < 30: return 1.4, "V1: RSI"
    if price < indicators.get('MA50', np.inf): return 1.2, "V1: DIP"
    
    if indicators.get('RSI', 50) > 70:
        if indicators.get('MACD_Hist', 0) > 0: return 1.0, "V1: MOMENTUM"
        else: return 0.6, "V1: FADING" # Old MACD logic
        
    if indicators.get('RSI', 50) > 85: return 0.6, "V1: EUPHORIA"
    return 1.0, "V1: STANDARD"

# --- CURRENT: SMART IMPULSE (Aggressive Entry + Impulse Exit) ---
def get_strategy_current(price, indicators, vix_val):
    ma200 = indicators.get('MA200', np.nan)
    ma50 = indicators.get('MA50', np.nan)
    rsi = indicators.get('RSI', 50)
    impulse = indicators.get('Impulse', 'Blue')
    bb_lower = indicators.get('BB_Lower', np.nan)
    
    # 1. CRISIS & MACRO
    tnx = indicators.get('TNX', 4.0)
    tnx_ma = indicators.get('TNX_MA50', 4.0)
    easy_money = tnx < tnx_ma

    if vix_val > 30: return 2.0, "PANIC BUY (VIX > 30)"
        
    # 2. DEEP VALUE (Aggressive - Trust Quality)
    if pd.notna(ma200) and price < ma200:
        if rsi < 40: return 1.6, "DEEP VALUE (Aggressive)" 
        else: return 1.0, "BEAR TREND"

    # 3. OPPORTUNITY
    if pd.notna(bb_lower) and price < bb_lower: return 1.4, "OVERSOLD (BB)"
    if rsi < 35: return 1.4, "RSI LOW"
    
    # 4. TREND
    if pd.notna(ma50) and price < ma50: return 1.2, "DIP BUY (< MA50)"

    # 5. MOMENTUM (Impulse Exit)
    if rsi > 70:
        if impulse == 'Green': return 1.0, "STRONG MOMENTUM"
        else: return 0.6, "MOMENTUM FADING"
            
    if rsi > 85: return 0.6, "EXTREME EUPHORIA"

    # 6. MACRO TAILWIND (The ROI Boost)
    if easy_money: return 1.2, "MACRO TAILWIND"
    
    return 1.0, "STANDARD"

# Wrapper for App
def get_strategy_multiplier(price, indicators, vix_val):
    return get_strategy_current(price, indicators, vix_val)