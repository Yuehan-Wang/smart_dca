import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from config import COLOR_DARK, COLOR_MAIN, COLOR_ACCENT
from data_handler import fetch_data
from analysis import get_strategy_multiplier
from backtest import run_portfolio_backtest
from subscription_manager import add_subscription, get_subscription, remove_subscription
from email_service import send_confirmation_email, send_unsubscribe_email
import os

def show_manifesto_page():
    st.title("The Manifesto")
    st.markdown("### Why Average is for Everyone Else")
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"""
        <div class="manifesto-card">
            <h3>The Problem with Blind DCA</h3>
            <p>Dollar Cost Averaging (DCA) is safe, but it is <b>blind</b>. It buys the same amount whether the market is crashing or bubbling.</p>
            <p>Blind DCA asks: <i>"Is it the 1st of the month?"</i></p>
            <p>Smart DCA asks: <b><i>"Is this asset actually worth buying right now?"</i></b></p>
        </div>
        
        <div class="manifesto-card">
            <h3>The Philosophy: Weaponize Human Emotion</h3>
            <p>The market is driven by <b>Fear</b> and <b>Greed</b>.</p>
            <p>We do not predict the future. We simply <b>react aggressively</b> to the price tags the market gives us.</p>
        </div>
        
        <h3>The 4 Laws of the Algorithm</h3>
        <div class="law-box">
            <span class="law-title">1. The Law of Crisis (VIX > 30 or < MA200 w/ Confluence)</span>
            <strong>Blood in the streets</strong> is the greatest gift. We deploy <strong>Maximum Capital (2.0x)</strong> on high VIX. We also hunt for <strong>Deep Value (1.6x)</strong> when price is below the 200-day average, <em>but only if verified by low RSI (< 40)</em> to avoid "catching a falling knife."
        </div>
        <div class="law-box">
            <span class="law-title">2. The Law of Opportunity (RSI < 35)</span>
            Buy the <strong>Dip (1.4x)</strong> aggressively. We raised our sensitivity threshold to <strong>RSI 35</strong> to capture more buying opportunities during healthy bull market pullbacks.
        </div>
        <div class="law-box">
            <span class="law-title">3. The Law of Trend (MA50)</span>
            A strong asset's pullback is a chance to fortify your position, so <strong>Add to Winners (1.2x)</strong> when price nears the primary trend.
        </div>
        <div class="law-box">
            <span class="law-title">4. The Law of True Strength (Impulse MACD)</span>
            When the market is hot (RSI > 70), we consult the <strong>Impulse System</strong>. If the bars are <strong>Green</strong> (Rising Momentum + Inertia), we hold standard buying (1.0x). If the bars turn <strong>Blue or Red</strong>, we cut back (0.6x) immediately to protect capital.
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # 1. The Warren Buffett Quote Box
        st.markdown(f"""
        <div style="background-color:{COLOR_DARK}; padding:20px; border-radius:10px; color:white;">
            <h2 style="color:{COLOR_ACCENT} !important; margin-top:0;">Remember</h2>
            <p style="font-size:1.1em; font-style:italic; color:white;">"The stock market is a device for transferring money from the impatient to the patient."</p>
            <p align="right" style="color:white;">- Warren Buffett</p>
            <hr style="border-color:{COLOR_MAIN}">
            <p style="color:white;"><b>This tool is your discipline.</b></p>
        </div>
        """, unsafe_allow_html=True)
        
        # 2. The New Research Link (Added Here)
        st.markdown(f"""
        <div style="margin-top: 20px; text-align: center;">
            <a href="https://www.yuehan.space/post/smart_dca" target="_blank" style="text-decoration: none;">
                <div style="background-color: white; border: 1px solid #ddd; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); transition: all 0.3s;">
                    <span style="font-size: 1.5rem;"></span><br>
                    <strong style="color: {COLOR_MAIN}; font-size: 1.1rem;">Read the Full Report</strong><br>
                    <span style="font-size: 0.85rem; color: #666;">See the math & performance comparison vs. Standard DCA.</span>
                </div>
            </a>
        </div>
        """, unsafe_allow_html=True)
        
def show_dashboard_page(tickers, weights_dict):
    st.title("Action Dashboard")
    st.markdown("Your live command center. Run this on payday.")
    
    contribution_budget = st.number_input("Contribution Budget ($)", value=3000, step=100, key="dashboard_budget")
    
    if st.button("Analyze Current Market"):
        end_d = datetime.now()
        start_d = end_d - timedelta(days=700)
        
        with st.spinner("Crunching numbers..."):
            data_map = fetch_data(tickers, start_d, end_d)
            
            if not data_map:
                st.error("No data found.")
            else:
                current_vix = data_map[tickers[0]].iloc[-1]['VIX']
                
                c1, c2 = st.columns(2)
                c1.markdown(f"""<div style="color:{COLOR_DARK};">
                                <div style="font-size:0.9rem; margin-bottom:6px;">Fear Index (VIX)</div>
                                <div style="font-size:1.8rem; font-weight:700;">{current_vix:.2f}</div>
                              </div>""", unsafe_allow_html=True)
                c2.markdown(f"""<div style="color:{COLOR_DARK};">
                                <div style="font-size:0.9rem; margin-bottom:6px;">Contribution Budget</div>
                                <div style="font-size:1.8rem; font-weight:700;">${contribution_budget:,.0f}</div>
                              </div>""", unsafe_allow_html=True)
                
                action_data = []
                total_suggested = 0
                
                for t in tickers:
                    if t not in data_map: continue
                    curr = data_map[t].iloc[-1]
                    price = curr['Close']
                    base_amt = contribution_budget * (weights_dict[t] / 100)
                    
                    # UPDATED: Pass Impulse to strategy
                    inds = {'MA200': curr['MA200'], 'MA50': curr['MA50'], 
                            'BB_Lower': curr['BB_Lower'], 'BB_Upper': curr['BB_Upper'], 
                            'RSI': curr['RSI'], 'MACD_Hist': curr['MACD_Hist'],
                            'Impulse': curr['Impulse']}
                    
                    mult, reason = get_strategy_multiplier(price, inds, current_vix)
                    final_amt = base_amt * mult
                    total_suggested += final_amt
                    
                    action_data.append({
                        "Ticker": t, "Price": f"${price:.2f}",
                        "Condition": reason, "Action": f"{mult}x",
                        "Target Invest": f"${final_amt:.0f}"
                    })
                
                st.dataframe(pd.DataFrame(action_data), use_container_width=True)
                st.markdown(f"""<div style="color:{COLOR_DARK}; font-weight:700; font-size:1.1rem;">
                                Total Capital to Deploy: ${total_suggested:,.2f}
                              </div>""", unsafe_allow_html=True)
    
    # Email Subscription Section
    st.markdown("---")
    st.subheader("Email Subscription")
    st.markdown("Get automated investment recommendations delivered to your inbox!")
    
    if st.button("Subscribe for Email Notifications", key="btn_show_subscription"):
        st.session_state['show_subscription'] = not st.session_state.get('show_subscription', False)
    
    if st.session_state.get('show_subscription', False):
        st.markdown("""
        Subscribe to receive weekly email recommendations based on your portfolio configuration.
        You'll receive emails on the **first and last day** of each selected week (e.g., selecting Week 1 sends emails on the 1st and 7th of each month).
        """)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            email_input = st.text_input("Email Address", placeholder="your.email@example.com", key="sub_email")
        
        with col2:
            st.write("Send emails on:")
            week_selections = []
            cols = st.columns(4)
            for i, col in enumerate(cols):
                with col:
                    if st.checkbox(f"Week {i+1}", key=f"week_{i+1}"):
                        week_selections.append(i+1)
        
        if email_input and week_selections:
            col_sub, col_unsub = st.columns(2)
            
            with col_sub:
                if st.button("Subscribe / Update", use_container_width=True, key="btn_subscribe"):
                    if '@' in email_input and '.' in email_input:
                        result = add_subscription(
                            email_input,
                            tickers,
                            weights_dict,
                            contribution_budget,
                            week_selections
                        )
                        
                        # Send confirmation email
                        try:
                            from dotenv import load_dotenv
                            load_dotenv()
                            
                            api_key = os.environ.get('RESEND_API_KEY')
                            from_email = os.environ.get('FROM_EMAIL', 'Smart DCA <onboarding@resend.dev>')
                            
                            if api_key:
                                email_config = {
                                    'api_key': api_key,
                                    'from_email': from_email
                                }
                                send_confirmation_email(
                                    email_input,
                                    weights_dict, 
                                    contribution_budget,
                                    week_selections,
                                    email_config
                                )
                                if result == "added":
                                    st.success(f"Subscribed! Check your email for confirmation.")
                                else:
                                    st.success(f"Subscription updated! Check your email for confirmation.")
                            else:
                                st.warning("Subscribed, but confirmation email not sent (API key not configured)")
                        except Exception as e:
                            st.warning(f"Subscribed, but confirmation email failed: {str(e)}")
                    else:
                        st.error("Please enter a valid email address")
            
            with col_unsub:
                with col_unsub:
                    if st.button("Unsubscribe", use_container_width=True):
                        # 1. Remove from database
                        remove_subscription(email_input)
                        
                        # 2. Send Confirmation Email
                        try:
                            from dotenv import load_dotenv
                            load_dotenv()
                            
                            api_key = os.environ.get('RESEND_API_KEY')
                            from_email = os.environ.get('FROM_EMAIL', 'Smart DCA <onboarding@resend.dev>')
                            
                            if api_key:
                                email_config = {
                                    'api_key': api_key,
                                    'from_email': from_email
                                }
                                send_unsubscribe_email(email_input, email_config)
                                st.success("Unsubscribed successfully! Confirmation email sent.")
                            else:
                                st.success("Unsubscribed successfully! (Email failed: No API Key)")
                                
                        except Exception as e:
                            st.warning(f"Unsubscribed locally, but email failed: {e}")
        
        elif email_input and not week_selections:
            st.warning("Please select at least one week to receive emails.")
        
        st.markdown("---")
        st.caption("**Note:** Emails are sent on the first and last day of selected weeks.")

def show_backtest_page(tickers, weights_dict):
    st.title("Strategy Backtest")
    
    # Date range inputs
    c1, c2 = st.columns(2)
    start_date = c1.date_input("Start Date", value=datetime(2020, 1, 1))
    end_date = c2.date_input("End Date", value=datetime.now())
    
    # New flexible investment parameters
    st.markdown("### Investment Parameters")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        initial_investment = st.number_input(
            "Initial Investment ($)", 
            value=0, 
            step=1000, 
            help="One-time investment at the start of the backtest period"
        )
    
    with col2:
        contribution_frequency = st.selectbox(
            "Contribution Frequency",
            ["monthly", "weekly"],
            help="How often to make regular contributions",
            key="backtest_contribution_frequency"
        )
    
    with col3:
        contribution_amount = st.number_input(
            "Contribution Amount ($)",
            value=3000,
            step=100,
            help="Amount to invest per contribution period",
            key="backtest_contribution_amount"
        )
    
    with col4:
        enable_rebalancing = st.checkbox(
            "Enable Rebalancing", 
            value=False,
            help="Rebalance portfolio annually to maintain target weights"
        )
    
    if start_date >= end_date:
        st.error("Start Date must be before End Date.")
    
    if st.button("Run Simulation"):
        with st.spinner("Replaying history..."):
            data_map = fetch_data(tickers, start_date, end_date)
            if not data_map:
                st.error("No data found for this range.")
            else:
                res = run_portfolio_backtest(data_map, weights_dict, contribution_amount, 
                                           initial_investment, enable_rebalancing, contribution_frequency)
                if not res:
                    st.error("Data mismatch or empty result.")
                else:
                    std_final = res['std_val'][-1]
                    smart_final = res['smart_val'][-1]
                    std_profit = std_final - res['std_invested']
                    smart_profit = smart_final - res['smart_invested']
                    profit_diff = smart_profit - std_profit
                    
                    c1, c2, c3 = st.columns(3)
                    
                    with c1:
                        st.markdown(f"""
                        <div class="metric-card">
                            <h4 style="margin:0; color:#555;">Standard DCA</h4>
                            <h2 style="color:{COLOR_DARK};">${std_final:,.0f}</h2>
                            <p style="margin:0; font-weight:bold;">Profit: ${std_profit:,.0f}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    with c2:
                        st.markdown(f"""
                        <div class="metric-card" style="border-left-color:{COLOR_ACCENT}">
                            <h4 style="margin:0; color:#555;">Smart DCA</h4>
                            <h2 style="color:{COLOR_DARK};">${smart_final:,.0f}</h2>
                            <p style="margin:0; font-weight:bold;">Profit: ${smart_profit:,.0f}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    with c3:
                        color = "#2a9d8f" if profit_diff > 0 else "#e63946"
                        st.markdown(f"""
                        <div class="metric-card" style="border-left-color:{color}">
                            <h4 style="margin:0; color:#555;">Net Profit Difference</h4>
                            <h2 style="color:{color};">{profit_diff:+,.0f}</h2>
                            <p style="margin:0; font-weight:bold;">Pure Alpha</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=res['dates'], y=res['std_val'], name="Standard", line=dict(color=COLOR_ACCENT)))
                    fig.add_trace(go.Scatter(x=res['dates'], y=res['smart_val'], name="Smart", line=dict(color=COLOR_DARK, width=3)))
                    
                    # Add rebalancing event markers if enabled
                    if enable_rebalancing and res['rebalancing_events']:
                        for rebal_date in res['rebalancing_events']:
                            # Find corresponding value for the rebalancing date
                            date_idx = res['dates'].get_indexer([rebal_date], method='nearest')[0]
                            if date_idx < len(res['smart_val']):
                                # --- FIX START: Convert Pandas Timestamp to MS Timestamp for Plotly/Pandas 2.0 Compatibility ---
                                fig.add_vline(x=rebal_date.timestamp() * 1000, line_dash="dash", line_color="orange", 
                                            annotation_text="Rebalanced", annotation_position="top")
                                # --- FIX END ---
                    
                    chart_title = f"Wealth Growth ({contribution_frequency.title()} Contributions)"
                    fig.update_layout(title=chart_title, hovermode="x unified", height=500, 
                                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Additional statistics
                    if res['rebalancing_events']:
                        st.info(f"Portfolio was rebalanced {len(res['rebalancing_events'])} times during the backtest period.")
                    
                    if initial_investment > 0:
                        st.info(f"Initial investment of ${initial_investment:,.0f} was included at the start of the period.")

    st.markdown("---")
    st.subheader("Historical Trade Inspector")
    st.markdown("Check what the strategy would have done on a specific day in the past.")
    
    col_date, col_btn = st.columns([3, 1], vertical_alignment="bottom")
    
    with col_date:
        inspect_date = st.date_input("Select Date to Inspect", value=datetime.now() - timedelta(days=1), label_visibility="collapsed")
    
    # The button click triggers the analysis, but results are displayed below
    button_clicked = col_btn.button("Check Date Action", key="btn_inspect_historical", use_container_width=True)

    if button_clicked:
        insp_start = inspect_date - timedelta(days=400)
        
        with st.spinner(f"Analyzing {inspect_date}..."):
            insp_data = fetch_data(tickers, insp_start, inspect_date)
            
            if not insp_data:
                st.error("Could not fetch data for this date.")
            else:
                insp_res = []
                try:
                    vix_series = insp_data[tickers[0]]['VIX']
                    vix_val = vix_series.iloc[-1]
                except (KeyError, IndexError):
                    vix_val = 20.0
                
                for t in tickers:
                    if t not in insp_data: continue
                    df = insp_data[t]
                    if df.empty: continue
                    
                    curr = df.iloc[-1]
                    price = curr['Close']
                    actual_date = curr.name.strftime('%Y-%m-%d')
                    
                    # UPDATED: Added Impulse to inspector
                    inds = {'MA200': curr['MA200'], 'MA50': curr['MA50'], 
                            'BB_Lower': curr['BB_Lower'], 'BB_Upper': curr['BB_Upper'], 
                            'RSI': curr['RSI'], 'MACD_Hist': curr['MACD_Hist'],
                            'Impulse': curr['Impulse']}
                    
                    mult, reason = get_strategy_multiplier(price, inds, vix_val)
                    base_amt = contribution_amount * (weights_dict.get(t, 0) / 100)
                    final_amt = base_amt * mult
                    
                    insp_res.append({
                        "Ticker": t,
                        "Data Date": actual_date,
                        "Price": f"${price:.2f}",
                        "RSI": f"{curr['RSI']:.1f}",
                        "Impulse": curr['Impulse'],
                        "Signal": reason,
                        "Action": f"{mult}x",
                        "Invest Amount": f"${final_amt:.0f}"
                    })
                
                st.success(f"**Market Conditions on {inspect_date}: VIX = {vix_val:.2f}**")
                st.info(f"Note: Amounts shown are based on ${contribution_amount:,.0f} contribution amount.")
                st.dataframe(pd.DataFrame(insp_res), use_container_width=True)