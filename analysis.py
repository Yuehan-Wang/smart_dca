import pandas as pd
import numpy as np

def calculate_indicators_pro(df):
    """
    Enhanced indicator calculation.
    Assumes df has ['Close', 'High', 'Low'] columns.
    """
    # 1. Standard RSI
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(com=13, adjust=False).mean() # com=13 is same as alpha=1/14
    avg_loss = loss.ewm(com=13, adjust=False).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # 2. Bollinger Bands (Standard)
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['STD20'] = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['MA20'] + (df['STD20'] * 2)
    df['BB_Lower'] = df['MA20'] - (df['STD20'] * 2)
    # BB %B Indicator: Tells us where price is relative to bands (0 = Lower Band, 1 = Upper)
    df['BB_PctB'] = (df['Close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
    
    # 3. Moving Averages
    df['MA50'] = df['Close'].rolling(window=50).mean()
    df['MA200'] = df['Close'].rolling(window=200).mean()
    # Distance from MA200 (Percentage) - better than just binary Above/Below
    df['Dist_MA200'] = (df['Close'] / df['MA200']) - 1
    
    # 4. Impulse System (No change, logic is solid)
    exp12 = df['Close'].ewm(span=12, adjust=False).mean()
    exp26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD_Line'] = exp12 - exp26
    df['MACD_Signal'] = df['MACD_Line'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD_Line'] - df['MACD_Signal']
    
    df['EMA13'] = df['Close'].ewm(span=13, adjust=False).mean()
    prev_ema = df['EMA13'].shift(1)
    prev_hist = df['MACD_Hist'].shift(1)
    
    df['Impulse'] = 'Blue'
    if len(df) > 1:
        mask_valid = prev_ema.notna() & prev_hist.notna()
        mask_green = mask_valid & (df['EMA13'] > prev_ema) & (df['MACD_Hist'] > prev_hist)
        mask_red = mask_valid & (df['EMA13'] < prev_ema) & (df['MACD_Hist'] < prev_hist)
        df.loc[mask_green, 'Impulse'] = 'Green'
        df.loc[mask_red, 'Impulse'] = 'Red'
        
    return df

def get_strategy_pro(price, indicators, vix_val, ticker='VOO'):
    """
    vix_val: Current VIX index value (float)
    ticker: 'VOO' or 'QQQ' to adjust sensitivity
    """
    # Unpack indicators
    rsi = indicators.get('RSI', 50)
    bb_pct_b = indicators.get('BB_PctB', 0.5)
    dist_ma200 = indicators.get('Dist_MA200', 0) # e.g., -0.05 means 5% below MA200
    impulse = indicators.get('Impulse', 'Blue')
    
    # Base Multiplier
    multiplier = 1.0
    signals = []
    
    # Sensitivity Tuner: QQQ is wilder, so we expect deeper drops
    vol_adj = 1.2 if ticker == 'QQQ' else 1.0 
    
    # === LAYER 1: FEAR GAUGE (VIX) ===
    # Continuous scaling instead of binary >30
    # VIX 20 = 1.0x, VIX 30 = 1.25x, VIX 40 = 1.5x ...
    if vix_val > 20:
        vix_mult = 1 + (vix_val - 20) / 40 
        multiplier *= vix_mult
        if vix_val > 30: signals.append(f"VIX PANIC({vix_val:.1f})")
    
    # === LAYER 2: DEEP VALUE (Distance from MA200) ===
    # If price is below MA200, scale up based on HOW deep
    if dist_ma200 < 0:
        # e.g., if 10% below MA200 (-0.10), add 0.2 to multiplier
        # 2022 Bear market bottomed around -20% to -30% for QQQ
        depth_score = abs(dist_ma200) * 2.5 
        multiplier *= (1 + depth_score)
        signals.append(f"BELOW MA200({dist_ma200:.1%})")
        
    # === LAYER 3: OVERSOLD (RSI & Bollinger) ===
    # Dynamic thresholds based on ticker
    rsi_panic = 30 if ticker == 'QQQ' else 35
    
    if rsi < rsi_panic:
        multiplier *= 1.3
        signals.append("RSI OVERSOLD")
    elif rsi < (rsi_panic + 10): # "Buy the dip" zone
        multiplier *= 1.15
    
    # Bollinger Band Crash (Price below Lower Band)
    if bb_pct_b < 0: 
        multiplier *= 1.2
        signals.append("BB BREAKDOWN")
        
    # === LAYER 4: MOMENTUM FADE (Buying High) ===
    # Don't buy heavily at ATH (All Time Highs) if momentum is fading
    if rsi > 70:
        if impulse == 'Red': # Price high but momentum cracking
            multiplier *= 0.6 
            signals.append("TOP FADING")
        elif impulse == 'Blue':
            multiplier *= 0.8
            signals.append("HIGH NEUTRAL")
        else:
            multiplier *= 1.0 # Strong trend, keep normal DCA
            
    # Cap limits (Safety Rail)
    # Floor at 0.5 (never stop DCA entirely), Cap at 3.0 (aggressive but safe)
    multiplier = max(0.5, min(multiplier, 3.0))
    
    # Label Generation
    label = "STANDARD" if not signals else " + ".join(signals)
    
    return round(multiplier, 2), label

# --- V1: ORIGINAL BLUNT INSTRUMENT (For Backtesting Comparison) ---
def get_strategy_v1(price, indicators, vix_val):
    if vix_val > 30: return 2.0, "V1: PANIC"
    if price < indicators.get('MA200', np.inf): return 1.6, "V1: VALUE" 
    if indicators.get('RSI', 50) < 30: return 1.4, "V1: RSI"
    if price < indicators.get('MA50', np.inf): return 1.2, "V1: DIP"
    
    if indicators.get('RSI', 50) > 70:
        if indicators.get('MACD_Hist', 0) > 0: return 1.0, "V1: MOMENTUM"
        else: return 0.6, "V1: FADING"
        
    if indicators.get('RSI', 50) > 85: return 0.6, "V1: EUPHORIA"
    return 1.0, "V1: STANDARD"

# Backward compatibility - keep original function names for imports
calculate_indicators = calculate_indicators_pro
get_strategy_current = get_strategy_pro

# Wrapper for App
def get_strategy_multiplier(price, indicators, vix_val):
    return get_strategy_current(price, indicators, vix_val)