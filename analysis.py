def calculate_indicators(df):
    """Calculates RSI, BB, MA50, MA200, MACD, and Impulse MACD"""
    if len(df) < 200: return df 
    
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
    # We use shift(1) to compare current vs previous day
    # Green: EMA rising AND MACD Hist rising
    # Red: EMA falling AND MACD Hist falling
    # Blue: Neutral (anything else)
    
    prev_ema = df['EMA13'].shift(1)
    prev_hist = df['MACD_Hist'].shift(1)
    
    df['Impulse'] = 'Blue' # Default
    
    mask_green = (df['EMA13'] > prev_ema) & (df['MACD_Hist'] > prev_hist)
    mask_red = (df['EMA13'] < prev_ema) & (df['MACD_Hist'] < prev_hist)
    
    df.loc[mask_green, 'Impulse'] = 'Green'
    df.loc[mask_red, 'Impulse'] = 'Red'
    
    return df

def get_strategy_multiplier(price, indicators, vix_val):
    """Returns (multiplier, reason) based on the Strategy Logic."""
    
    # 1. CRISIS MODE
    # Concern A: User is fine with US-centric VIX
    if vix_val > 30:
        return 2.0, "PANIC BUY (VIX > 30)"
        
    # Concern B: Fix Falling Knife. Only buy < MA200 if RSI is also low (Deep Value confirmation)
    if price < indicators['MA200']:
        if indicators['RSI'] < 40:
            return 1.6, "DEEP VALUE (< MA200 & RSI < 40)"
        else:
            # If below MA200 but RSI is neutral/high, it might be a falling knife.
            # We treat it as standard or proceed to other checks.
            pass 

    # 2. OPPORTUNITY
    if price < indicators['BB_Lower']:
        return 1.4, "OVERSOLD (Below BB)"
        
    # Concern C: Fix Static Threshold. Raised from 30 to 35 to catch more dips.
    if indicators['RSI'] < 35:
        return 1.4, "RSI LOW (< 35)"
        
    if price < indicators['MA50']:
        return 1.2, "DIP BUY (< MA50)"

    # 3. TREND CORRECTOR (IMPULSE MACD)
    # Replaced standard MACD check with Impulse System
    if indicators['RSI'] > 70:
        if indicators['Impulse'] == 'Green':
            return 1.0, "STRONG MOMENTUM (Impulse Green)"
        else:
            # If Impulse is Red (Bearish) or Blue (Neutral/Choppy) while RSI is high => Risk
            return 0.6, "MOMENTUM FADING (Impulse Red/Blue)"
            
    # 4. EXTREME EUPHORIA
    if indicators['RSI'] > 85:
        return 0.6, "EXTREME EUPHORIA (RSI > 85)"

    # 5. STANDARD
    return 1.0, "STANDARD"