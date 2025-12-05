import pandas as pd
import numpy as np

def calculate_indicators(df):
    """Calculates RSI, BB, MA50, MA200, MACD, and Impulse MACD"""
    # FIX: We removed the check "if len(df) < 200: return df"
    # This ensures columns are ALWAYS created, even for new stocks (filled with NaN).
    
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
    # MACD Components
    exp12 = df['Close'].ewm(span=12, adjust=False).mean()
    exp26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD_Line'] = exp12 - exp26
    df['MACD_Signal'] = df['MACD_Line'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD_Line'] - df['MACD_Signal']
    
    # Impulse Components (EMA 13)
    df['EMA13'] = df['Close'].ewm(span=13, adjust=False).mean()
    
    # Calculate Momentum (Change in Hist) and Inertia (Change in EMA)
    prev_ema = df['EMA13'].shift(1)
    prev_hist = df['MACD_Hist'].shift(1)
    
    # Initialize Impulse column with 'Blue' (Neutral)
    df['Impulse'] = 'Blue' 
    
    # We must handle cases where previous values might be NaN (start of data)
    # This mask ensures we only compare valid numbers
    mask_valid = prev_ema.notna() & prev_hist.notna()
    
    if len(df) > 1:
        mask_green = mask_valid & (df['EMA13'] > prev_ema) & (df['MACD_Hist'] > prev_hist)
        mask_red = mask_valid & (df['EMA13'] < prev_ema) & (df['MACD_Hist'] < prev_hist)
        
        df.loc[mask_green, 'Impulse'] = 'Green'
        df.loc[mask_red, 'Impulse'] = 'Red'
    
    return df

def get_strategy_multiplier(price, indicators, vix_val):
    """Returns (multiplier, reason) based on the Strategy Logic."""
    
    # HANDLE NAN VALUES (For new stocks)
    ma200 = indicators.get('MA200', np.nan)
    rsi = indicators.get('RSI', 50)
    impulse = indicators.get('Impulse', 'Blue') # Default to Blue if missing
    
    # 1. CRISIS MODE (Global Panic)
    # We keep this: If the whole world is ending (VIX > 30), we buy everything.
    if vix_val > 30:
        return 2.0, "PANIC BUY (VIX > 30)"
        
    # 2. DEEP VALUE (Individual Stock Crash)
    # FIX: "No Falling Knives" Rule
    if pd.notna(ma200) and price < ma200:
        if rsi < 40:
            # CHECK: Is the knife still falling fast? (Impulse Red)
            if impulse == 'Red':
                return 1.0, "FALLING KNIFE (Impulse Red - Wait)"
            else:
                # Impulse is Blue (Neutral) or Green (Rebound) -> NOW we strike.
                return 1.6, "DEEP VALUE (Stabilized)"
        else:
            # Below MA200 but RSI is not oversold -> No action (Standard)
            pass 

    # 3. OPPORTUNITY
    bb_lower = indicators.get('BB_Lower', np.nan)
    if pd.notna(bb_lower) and price < bb_lower:
        return 1.4, "OVERSOLD (Below BB)"
        
    if rsi < 35:
        return 1.4, "RSI LOW (< 35)"
    
    ma50 = indicators.get('MA50', np.nan)
    if pd.notna(ma50) and price < ma50:
        return 1.2, "DIP BUY (< MA50)"

    # 4. TREND CORRECTOR (IMPULSE MACD)
    if rsi > 70:
        if impulse == 'Green':
            return 1.0, "STRONG MOMENTUM (Impulse Green)"
        else:
            return 0.6, "MOMENTUM FADING (Impulse Red/Blue)"
            
    # 5. EXTREME EUPHORIA
    if rsi > 85:
        return 0.6, "EXTREME EUPHORIA (RSI > 85)"

    # 6. STANDARD
    return 1.0, "STANDARD"