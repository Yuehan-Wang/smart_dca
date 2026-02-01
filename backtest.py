import pandas as pd
from analysis import get_strategy_v1, get_strategy_current

def run_portfolio_backtest(tickers_data, weights, monthly_budget, initial_investment=0, enable_rebalancing=False, contribution_frequency='monthly'):
    total_weight = sum(weights.values())
    if total_weight == 0: return None
    norm_weights = {k: v/total_weight for k,v in weights.items()}
    
    period_budget = monthly_budget if contribution_frequency == 'monthly' else monthly_budget / 4.33
    
    common_index = None
    for t, df in tickers_data.items():
        if common_index is None: common_index = df.index
        else: common_index = common_index.intersection(df.index)
    
    if common_index is None or len(common_index) == 0: return None
    
    if contribution_frequency == 'weekly':
        contrib_dates = common_index.to_series().resample('W').last().index
    else:
        contrib_dates = common_index.to_series().resample('ME').last().index
    
    # Init Histories for STD, V1, CURRENT
    hist = {k: [] for k in ['std', 'v1', 'cur']}
    inv = {k: 0.0 for k in ['std', 'v1', 'cur']}
    holdings = {k: {t: 0.0 for t in tickers_data} for k in ['std', 'v1', 'cur']}
    
    # Initial Investment
    if initial_investment > 0:
        first_date = contrib_dates[0]
        for t in tickers_data.keys():
            if t not in tickers_data: continue
            try:
                idx = tickers_data[t].index.get_indexer([first_date], method='nearest')[0]
                price = tickers_data[t].iloc[idx]['Close']
                alloc = initial_investment * norm_weights[t]
                for k in ['std', 'v1', 'cur']:
                    holdings[k][t] += alloc / price
                    inv[k] += alloc
            except: continue
    
    rebalancing_events = []
    
    for i, date in enumerate(contrib_dates):
        vals = {k: 0.0 for k in ['std', 'v1', 'cur']}
        
        for t in tickers_data.keys():
            if t not in tickers_data: continue
            try:
                idx = tickers_data[t].index.get_indexer([date], method='nearest')[0]
                row = tickers_data[t].iloc[idx]
                price = row['Close']
            except: continue
            
            # --- Indicators ---
            vix_val = row.get('VIX', 20)
            inds = {
                'MA200': row.get('MA200', float('nan')), 
                'MA50': row.get('MA50', float('nan')), 
                'BB_Lower': row.get('BB_Lower', float('nan')), 
                'BB_Upper': row.get('BB_Upper', float('nan')),
                'BB_PctB': row.get('BB_PctB', 0.5),
                'Dist_MA200': row.get('Dist_MA200', 0),
                'RSI': row.get('RSI', 50), 
                'MACD_Hist': row.get('MACD_Hist', 0),
                'Impulse': row.get('Impulse', 'Blue'),
                'TNX': row.get('TNX', 4.0),
                'TNX_MA50': row.get('TNX_MA50', 4.0)
            }
            
            base_alloc = period_budget * norm_weights[t]
            
            # 1. Standard
            holdings['std'][t] += base_alloc / price
            inv['std'] += base_alloc
            
            # 2. V1 (Original)
            m1, _ = get_strategy_v1(price, inds, vix_val)
            holdings['v1'][t] += (base_alloc * m1) / price
            inv['v1'] += (base_alloc * m1)
            
            # 3. Current (Smart Impulse with Pro improvements)
            m_cur, _ = get_strategy_current(price, inds, vix_val, ticker=t)
            holdings['cur'][t] += (base_alloc * m_cur) / price
            inv['cur'] += (base_alloc * m_cur)

            for k in ['std', 'v1', 'cur']:
                vals[k] += holdings[k][t] * price
        
        # Rebalancing
        if enable_rebalancing and i % (12 if contribution_frequency == 'monthly' else 52) == 0 and i > 0:
            rebalanced = False
            totals = {k: sum(holdings[k][t] * tickers_data[t].iloc[tickers_data[t].index.get_indexer([date], method='nearest')[0]]['Close'] for t in tickers_data if t in holdings[k]) for k in ['std', 'v1', 'cur']}
            
            for t in tickers_data:
                try:
                    idx = tickers_data[t].index.get_indexer([date], method='nearest')[0]
                    price = tickers_data[t].iloc[idx]['Close']
                    for k in ['std', 'v1', 'cur']:
                        if totals[k] > 0:
                            holdings[k][t] = (totals[k] * norm_weights[t]) / price
                    rebalanced = True
                except: continue
            if rebalanced: rebalancing_events.append(date)
            
        for k in ['std', 'v1', 'cur']:
            hist[k].append(vals[k])
        
    return {
        'dates': contrib_dates,
        # Standard
        'std_val': hist['std'], 'std_invested': inv['std'],
        # V1
        'v1_val': hist['v1'], 'v1_invested': inv['v1'],
        # Current
        'smart_val': hist['cur'], 'smart_invested': inv['cur'], # Mapped to 'smart' for App UI
        'cur_val': hist['cur'], 'cur_invested': inv['cur'],     # Explicit key for comparison script
        'rebalancing_events': rebalancing_events
    }