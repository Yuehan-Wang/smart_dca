import pandas as pd
from analysis import get_strategy_multiplier

def run_portfolio_backtest(tickers_data, weights, monthly_budget, initial_investment=0, enable_rebalancing=False, contribution_frequency='monthly'):
    total_weight = sum(weights.values())
    if total_weight == 0: return None
    norm_weights = {k: v/total_weight for k,v in weights.items()}
    
    # Adjust budget for contribution frequency
    period_budget = monthly_budget if contribution_frequency == 'monthly' else monthly_budget / 4.33
    
    common_index = None
    for t, df in tickers_data.items():
        if common_index is None: common_index = df.index
        else: common_index = common_index.intersection(df.index)
    
    if common_index is None or len(common_index) == 0: return None
    
    if contribution_frequency == 'weekly':
        contrib_dates = common_index.to_series().resample('W').last().index
    else:  # monthly
        contrib_dates = common_index.to_series().resample('M').last().index
    
    std_hist, smart_hist = [], []
    std_inv, smart_inv = 0, 0
    std_holdings = {t: 0.0 for t in tickers_data.keys()}
    smart_holdings = {t: 0.0 for t in tickers_data.keys()}
    
    # Add initial investment if specified
    if initial_investment > 0:
        first_date = contrib_dates[0]
        for t in tickers_data.keys():
            if t not in tickers_data: continue
            try:
                idx = tickers_data[t].index.get_indexer([first_date], method='nearest')[0]
                price = tickers_data[t].iloc[idx]['Close']
                initial_alloc = initial_investment * norm_weights[t]
                std_holdings[t] += initial_alloc / price
                smart_holdings[t] += initial_alloc / price
                std_inv += initial_alloc
                smart_inv += initial_alloc
            except:
                continue
    
    rebalancing_events = []
    
    for i, date in enumerate(contrib_dates):
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
            std_alloc = period_budget * norm_weights[t]
            std_holdings[t] += std_alloc / price
            std_inv += std_alloc
            std_val += std_holdings[t] * price
            
            # --- Smart DCA ---
            vix_val = row['VIX']
            
            # UPDATED: Added Impulse to indicators dictionary so Analysis.py can see it
            inds = {'MA200': row['MA200'], 'MA50': row['MA50'], 
                    'BB_Lower': row['BB_Lower'], 'BB_Upper': row['BB_Upper'], 
                    'RSI': row['RSI'], 'MACD_Hist': row['MACD_Hist'],
                    'Impulse': row['Impulse']}
            
            mult, _ = get_strategy_multiplier(price, inds, vix_val)
            smart_alloc = (period_budget * norm_weights[t]) * mult
            
            smart_holdings[t] += smart_alloc / price
            smart_inv += smart_alloc
            smart_val += smart_holdings[t] * price
        
        # Rebalancing logic
        rebalanced = False
        if enable_rebalancing and i % (12 if contribution_frequency == 'monthly' else 52) == 0 and i > 0:
            total_smart_value = sum(smart_holdings[t] * tickers_data[t].iloc[tickers_data[t].index.get_indexer([date], method='nearest')[0]]['Close'] 
                                  for t in tickers_data.keys() if t in smart_holdings)
            
            if total_smart_value > 0:
                for t in tickers_data.keys():
                    if t not in tickers_data: continue
                    try:
                        idx = tickers_data[t].index.get_indexer([date], method='nearest')[0]
                        price = tickers_data[t].iloc[idx]['Close']
                        target_value = total_smart_value * norm_weights[t]
                        smart_holdings[t] = target_value / price
                        rebalanced = True
                    except:
                        continue
                        
            if rebalanced:
                rebalancing_events.append(date)
            
        std_hist.append(std_val)
        smart_hist.append(smart_val)
        
    return {
        'dates': contrib_dates,
        'std_val': std_hist, 'smart_val': smart_hist,
        'std_invested': std_inv, 'smart_invested': smart_inv,
        'rebalancing_events': rebalancing_events,
        'initial_investment': initial_investment,
        'contribution_frequency': contribution_frequency
    }