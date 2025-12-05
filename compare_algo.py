import pandas as pd
import numpy as np
from backtest import run_portfolio_backtest
from data_handler import fetch_data
from datetime import datetime, timedelta

# 1. SETUP
tickers = ["NVDA", "PYPL", "DIS"] # The Torture Test Portfolio
weights = {"NVDA": 33.3, "PYPL": 33.3, "DIS": 33.3}
budget = 3000
start_date = datetime(2020, 1, 1)
end_date = datetime.now()

print("Fetching Data...")
data_map = fetch_data(tickers, start_date, end_date)

# 2. RUN BACKTEST
print("Running Backtest...")
results = run_portfolio_backtest(data_map, weights, budget, contribution_frequency='monthly')

if not results:
    print("Backtest failed - no data.")
    exit()

# 3. CALCULATE ADVANCED METRICS
def get_max_drawdown(values):
    """Calculates Max Drawdown %"""
    vals = np.array(values)
    peak = np.maximum.accumulate(vals)
    drawdown = (vals - peak) / peak
    return drawdown.min() * 100

std_mdd = get_max_drawdown(results['std_val'])
smart_mdd = get_max_drawdown(results['smart_val'])

std_total_return = (results['std_val'][-1] - results['std_invested']) / results['std_invested'] * 100
smart_total_return = (results['smart_val'][-1] - results['smart_invested']) / results['smart_invested'] * 100

deployment_rate = results['smart_invested'] / results['std_invested'] * 100

# 4. PRINT REPORT
print("\n" + "="*40)
print(f"PERFORMANCE REPORT ({start_date.strftime('%Y')} - {end_date.strftime('%Y')})")
print("="*40)

print(f"\n1. PROFITABILITY (Total Return)")
print(f"   Standard DCA: {std_total_return:>6.2f}%")
print(f"   Smart DCA:    {smart_total_return:>6.2f}%")
diff = smart_total_return - std_total_return
print(f"   Difference:   {diff:>+6.2f}%")

print(f"\n2. RISK (Max Drawdown)")
print(f"   Standard DCA: {std_mdd:>6.2f}%")
print(f"   Smart DCA:    {smart_mdd:>6.2f}%")
print(f"   Improvement:  {smart_mdd - std_mdd:>+6.2f}% (Closer to 0 is better)")

print(f"\n3. AGGRESSION (Capital Deployed)")
print(f"   Smart DCA invested {deployment_rate:.1f}% of the available budget.")
if deployment_rate < 70:
    print("   WARNING: Strategy is too conservative. Holding too much cash.")
elif deployment_rate > 110:
    print("   NOTE: Strategy is very aggressive (using leverage/reserves).")
else:
    print("   STATUS: Healthy deployment levels.")

print("="*40)