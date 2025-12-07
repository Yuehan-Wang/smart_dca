import logging
import warnings


logging.getLogger('streamlit.runtime.caching.cache_data_api').setLevel(logging.ERROR)
logging.getLogger('streamlit.runtime.scriptrunner_utils.script_run_context').setLevel(logging.ERROR)

# 2. Silence any remaining FutureWarnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import pandas as pd
import numpy as np
from backtest import run_portfolio_backtest
from data_handler import fetch_data
from datetime import datetime

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def get_metrics(values, invested):
    vals = np.array(values)
    # Max Drawdown
    peak = np.maximum.accumulate(vals)
    drawdown = (vals - peak) / peak
    mdd = drawdown.min() * 100
    
    # Profit & ROI
    final_val = vals[-1]
    profit = final_val - invested
    roi = (profit / invested) * 100
    
    return final_val, invested, profit, roi, mdd

def run_scenario(name, tickers, weights, start_date_str, end_date_str, budget=3000):
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    
    print(f"\n[ SYSTEM ] Starting Scenario: {name}")
    print(f"[ SYSTEM ] Timeframe: {start_date_str} to {end_date_str}")
    
    data_map = fetch_data(tickers, start_date, end_date)
    
    if not data_map:
        print("!! Data fetch failed.")
        return

    print(f"[ SYSTEM ] Running Backtest...")
    results = run_portfolio_backtest(
        data_map, 
        weights, 
        budget, 
        initial_investment=0, 
        contribution_frequency='monthly',
        enable_rebalancing=True
    )
    
    if not results:
        print("!! Backtest failed - no data.")
        return

    # Metrics
    m_std = get_metrics(results['std_val'], results['std_invested'])
    m_v1  = get_metrics(results['v1_val'], results['v1_invested'])
    m_cur = get_metrics(results['cur_val'], results['cur_invested'])
    
    # Comparisons
    alpha_v1 = m_v1[3] - m_std[3]
    alpha_cur = m_cur[3] - m_std[3]
    cap_v1 = (m_v1[1] / m_std[1]) * 100
    cap_cur = (m_cur[1] / m_std[1]) * 100

    # Report
    print("\n" + "="*95)
    print(f"REPORT: {name.upper()}")
    print(f"Period: {start_date_str} -> {end_date_str} | Portfolio: {tickers}")
    print("="*95)
    print(f"{'METRIC':<22} | {'STANDARD DCA':<16} | {'V1 (ORIGINAL)':<16} | {'CURRENT (IMPULSE)':<18}")
    print("-" * 95)
    
    # ROI
    print(f"{'Total Return (ROI)':<22} | {m_std[3]:>15.1f}% | {m_v1[3]:>15.1f}% | {m_cur[3]:>17.1f}% 🏆")
    
    # Alpha
    print(f"{'Alpha vs Std':<22} | {'-':>15} | {alpha_v1:>+14.1f}% | {alpha_cur:>+16.1f}%")
    
    # Invested
    print(f"{'Capital Deployed':<22} | {100.0:>15.1f}% | {cap_v1:>15.1f}% | {cap_cur:>17.1f}%")
    
    # Drawdown
    print(f"{'Max Drawdown':<22} | {m_std[4]:>15.1f}% | {m_v1[4]:>15.1f}% | {m_cur[4]:>17.1f}%")
    print("="*95)

# ==========================================
# MAIN EXECUTION
# ==========================================

# 1. THE GREAT FINANCIAL CRISIS (2007-2010)
run_scenario("The Great Financial Crisis", ["SPY", "QQQ"], {"SPY": 50.0, "QQQ": 50.0}, "2007-01-01", "2010-01-01")

# 2. THE COVID BULL RUN (2020-2021)
run_scenario("The Covid Money Printer (Bull)", ["VOO", "QQQ"], {"VOO": 50.0, "QQQ": 50.0}, "2020-03-01", "2021-12-31")

# 3. THE INFLATION CRASH (2022)
run_scenario("The Inflation Crash (Bear)", ["VOO", "QQQ"], {"VOO": 50.0, "QQQ": 50.0}, "2022-01-01", "2022-12-31")

# 4. THE TORTURE TEST (2020 - Present)
run_scenario("Torture Test (High Vol)", ["NVDA", "PYPL", "DIS"], {"NVDA": 33.3, "PYPL": 33.3, "DIS": 33.3}, "2020-01-01", datetime.now().strftime("%Y-%m-%d"))

# 5. THE STABLE TEST (2020 - Present)
run_scenario("Stable Test (Long Term)", ["VOO", "QQQ"], {"VOO": 50.0, "QQQ": 50.0}, "2020-01-01", datetime.now().strftime("%Y-%m-%d"))