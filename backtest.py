import pandas as pd
from analysis import get_strategy_multiplier

def run_portfolio_backtest(tickers_data, weights, monthly_budget):
    total_weight = sum(weights.values())
    if total_weight == 0: return None
    norm_weights = {k: v/total_weight for k,v in weights.items()}
    
    common_index = None
    for t, df in tickers_data.items():
        if common_index is None: common_index = df.index
        else: common_index = common_index.intersection(df.index)
    
    if common_index is None or len(common_index) == 0: return None
    # Resample to Monthly
    monthly_dates = common_index.to_series().resample('M').last().index
    
    std_hist, smart_hist = [], []
    std_inv, smart_inv = 0, 0
    std_holdings = {t: 0.0 for t in tickers_data.keys()}
    smart_holdings = {t: 0.0 for t in tickers_data.keys()}
    
    for date in monthly_dates:
        std_val, smart_val = 0, 0
        
        for t in tickers_data.keys():
            if t not in tickers_data: continue
            try:
                # Find closest date if exact EOM missing
                idx = tickers_data[t].index.get_indexer([date], method='nearest')[0]
                row = tickers_data[t].iloc[idx]
                price = row['Close']
            except:
                continue
            
            # --- Standard DCA ---
            std_alloc = monthly_budget * norm_weights[t]
            std_holdings[t] += std_alloc / price
            std_inv += std_alloc
            std_val += std_holdings[t] * price
            
            # --- Smart DCA ---
            vix_val = row['VIX']
            inds = {'MA200': row['MA200'], 'MA50': row['MA50'], 
                    'BB_Lower': row['BB_Lower'], 'BB_Upper': row['BB_Upper'], 
                    'RSI': row['RSI'], 'MACD_Hist': row['MACD_Hist']}
            
            mult, _ = get_strategy_multiplier(price, inds, vix_val)
            smart_alloc = (monthly_budget * norm_weights[t]) * mult
            
            smart_holdings[t] += smart_alloc / price
            smart_inv += smart_alloc
            smart_val += smart_holdings[t] * price
            
        std_hist.append(std_val)
        smart_hist.append(smart_val)
        
    return {
        'dates': monthly_dates,
        'std_val': std_hist, 'smart_val': smart_hist,
        'std_invested': std_inv, 'smart_invested': smart_inv
    }