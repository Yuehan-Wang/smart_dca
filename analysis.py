def calculate_indicators(df):
    """Calculates RSI, BB, MA50, MA200, and MACD"""
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
    # 4. MACD (Trend Corrector)
    exp12 = df['Close'].ewm(span=12, adjust=False).mean()
    exp26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD_Line'] = exp12 - exp26
    df['MACD_Signal'] = df['MACD_Line'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD_Line'] - df['MACD_Signal']
    
    return df

def get_strategy_multiplier(price, indicators, vix_val):
    """Returns (multiplier, reason) based on the Strategy Logic."""
    
    # 1. CRISIS MODE
    if vix_val > 30:
        return 2.0, "PANIC BUY (VIX > 30)"
    if price < indicators['MA200']:
        return 1.6, "DEEP VALUE (< MA200)"
    # 2. OPPORTUNITY
    if price < indicators['BB_Lower']:
        return 1.4, "OVERSOLD (Below BB)"
    if indicators['RSI'] < 30:
        return 1.4, "RSI LOW (< 30)"
    if price < indicators['MA50']:
        return 1.2, "DIP BUY (< MA50)"
    # 3. TREND CORRECTOR (MACD)
    if indicators['RSI'] > 70:
        if indicators['MACD_Hist'] > 0:
            return 1.0, "STRONG MOMENTUM (RSI > 70 but MACD+)"
        else:
            return 0.6, "MOMENTUM FADING (Top Risk)"
    # 4. EXTREME EUPHORIA
    if indicators['RSI'] > 85:
        return 0.6, "EXTREME EUPHORIA (RSI > 85)"
    # 5. STANDARD
    return 1.0, "STANDARD"