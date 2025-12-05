from datetime import datetime, timedelta
import os
import requests
from data_handler import fetch_data
from analysis import get_strategy_multiplier
import calendar
import json
import urllib.parse

def generate_pie_chart_url(weights):
    """Generates a URL for a static pie chart image using QuickChart.io"""
    labels = list(weights.keys())
    data = list(weights.values())
    
    # Colors matching your theme (Dark Blue, Main Blue, Accent, etc)
    colors = ["#03045e", "#0077b6", "#00b4d8", "#90e0ef", "#caf0f8", "#023e8a"]
    
    chart_config = {
        "type": "doughnut",
        "data": {
            "labels": labels,
            "datasets": [{
                "data": data,
                "backgroundColor": colors[:len(labels)]
            }]
        },
        "options": {
            "plugins": {
                "legend": {"position": "right"},
                "datalabels": {"display": True, "color": "white"}
            }
        }
    }
    
    # Create the URL
    base_url = "https://quickchart.io/chart"
    params = {
        'c': json.dumps(chart_config),
        'w': 500,
        'h': 300
    }
    return f"{base_url}?{urllib.parse.urlencode(params)}"

def send_confirmation_email(to_email, weights, budget, selected_weeks, email_config):
    
    # 1. Setup Data
    weeks_text = ", ".join([f"Week {w}" for w in selected_weeks])
    
    # Generate Chart Image URL
    chart_url = generate_pie_chart_url(weights)
    
    # Generate Allocation List HTML (The pretty text version)
    allocation_html = '<ul style="list-style-type: none; padding: 0;">'
    for ticker, weight in weights.items():
        allocation_html += f'<li style="margin-bottom: 5px;"><strong>{ticker}:</strong> {weight:.1f}%</li>'
    allocation_html += '</ul>'
    app_url = "https://yuehan-wang-smart-dca-app-cujodf.streamlit.app/"
    
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Helvetica Neue', Arial, sans-serif; color: #333; }}
            .header {{ background-color: #03045e; color: white; padding: 25px; text-align: center; }}
            .content {{ padding: 20px; max-width: 600px; margin: 0 auto; }}
            .info-box {{ background-color: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 8px; border-left: 5px solid #0096c7; }}
            .chart-container {{ text-align: center; margin: 20px 0; }}
            .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 0.9em; color: #666; text-align: center; }}
            a {{ color: #0077b6; text-decoration: none; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Subscription Confirmed!</h1>
        </div>
        <div class="content">
            <h2>Welcome to Smart DCA Notifications</h2>
            <p>You've successfully subscribed. We will monitor your portfolio and tell you exactly when to buy aggressively.</p>
            
            <div class="info-box">
                <h3 style="margin-top:0;">Your Configuration</h3>
                
                <table style="width:100%">
                    <tr>
                        <td style="vertical-align:top; width:50%">
                            <p><strong>Total Budget:</strong> ${budget:,.0f}</p>
                            <p><strong>Schedule:</strong> {weeks_text}</p>
                            <p><strong>Allocation:</strong></p>
                            {allocation_html}
                        </td>
                        <td style="vertical-align:top; width:50%">
                            <img src="{chart_url}" alt="Portfolio Allocation" width="100%" style="max-width: 250px; border-radius: 10px;">
                        </td>
                    </tr>
                </table>
            </div>
            
            <h3>Schedule</h3>
            <p>Emails are sent on the <strong>first and last day</strong> of your selected weeks.</p>
            
            <div class="footer">
                <p>To update or cancel your subscription, visit the <a href="{app_url}">Smart DCA app</a> anytime.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    subject = "Smart DCA - Subscription Confirmed!"
    return send_email(to_email, subject, html_content, email_config)

def send_unsubscribe_email(to_email, email_config):
    """Send a confirmation email when user unsubscribes"""
    html_content = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; color: #333; }
            .header { background-color: #03045e; color: white; padding: 20px; text-align: center; }
            .content { padding: 20px; text-align: center; }
            .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 0.9em; color: #666; }
            a { color: #0077b6; text-decoration: none; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Unsubscribed</h1>
        </div>
        <div class="content">
            <h2>You have been successfully unsubscribed.</h2>
            <p>You will no longer receive investment recommendations from Smart DCA.</p>
            <p>If this was a mistake, you can re-subscribe directly in the app.</p>
            <div class="footer">
                <p><a href="https://yuehan-wang-smart-dca-app-cujodf.streamlit.app/">Smart DCA</a></p>
            </div>
        </div>
    </body>
    </html>
    """

    subject = "Smart DCA - Unsubscription Confirmed"
    return send_email(to_email, subject, html_content, email_config)

def generate_recommendation_email(tickers, weights_dict, budget, user_email):
    """
    Generate email content with investment recommendations
    
    Args:
        tickers: List of tickers
        weights_dict: Dictionary of ticker weights
        budget: Contribution budget
        user_email: Subscriber's email
    
    Returns:
        HTML email content
    """
    end_d = datetime.now()
    start_d = end_d - timedelta(days=700)
    
    try:
        data_map = fetch_data(tickers, start_d, end_d)
        
        if not data_map:
            return None
        
        current_vix = data_map[tickers[0]].iloc[-1]['VIX']
        
        # Generate recommendations
        action_data = []
        total_suggested = 0
        
        for t in tickers:
            if t not in data_map:
                continue
            curr = data_map[t].iloc[-1]
            price = curr['Close']
            base_amt = budget * (weights_dict[t] / 100)
            
            inds = {
                'MA200': curr['MA200'], 
                'MA50': curr['MA50'],
                'BB_Lower': curr['BB_Lower'], 
                'BB_Upper': curr['BB_Upper'],
                'RSI': curr['RSI'], 
                'MACD_Hist': curr['MACD_Hist']
            }
            
            mult, reason = get_strategy_multiplier(price, inds, current_vix)
            final_amt = base_amt * mult
            total_suggested += final_amt
            
            action_data.append({
                'ticker': t,
                'price': price,
                'condition': reason,
                'multiplier': mult,
                'amount': final_amt
            })
        
        # Generate HTML email
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; color: #333; }}
                .header {{ background-color: #03045e; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .vix-box {{ background-color: #f0f0f0; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th {{ background-color: #023e8a; color: white; padding: 12px; text-align: left; }}
                td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
                .total {{ font-size: 1.2em; font-weight: bold; color: #03045e; margin-top: 20px; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 0.9em; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Smart DCA Investment Recommendations</h1>
                <p>{datetime.now().strftime('%B %d, %Y')}</p>
            </div>
            <div class="content">
                <div class="vix-box">
                    <strong>Fear Index (VIX):</strong> {current_vix:.2f}<br>
                    <strong>Your Contribution Budget:</strong> ${budget:,.0f}
                </div>
                
                <h2>Today's Investment Actions</h2>
                <table>
                    <tr>
                        <th>Ticker</th>
                        <th>Price</th>
                        <th>Condition</th>
                        <th>Action</th>
                        <th>Target Investment</th>
                    </tr>
        """
        
        for item in action_data:
            html_content += f"""
                    <tr>
                        <td><strong>{item['ticker']}</strong></td>
                        <td>${item['price']:.2f}</td>
                        <td>{item['condition']}</td>
                        <td>{item['multiplier']}x</td>
                        <td><strong>${item['amount']:.0f}</strong></td>
                    </tr>
            """
        
        html_content += f"""
                </table>
                
                <div class="total">
                    Total Capital to Deploy: ${total_suggested:,.2f}
                </div>
                
                <div class="footer">
                    <p>This recommendation is based on the Smart DCA algorithm analyzing current market conditions.</p>
                    <p>To manage your subscription or update your portfolio, visit the <a href="https://yuehan-wang-smart-dca-app-cujodf.streamlit.app/">Smart DCA app</a>.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    except Exception as e:
        print(f"Error generating email for {user_email}: {e}")
        return None

def send_email(to_email, subject, html_content, email_config):
    """
    Send email using Resend API (much easier than SMTP!)
    
    Args:
        to_email: Recipient email
        subject: Email subject
        html_content: HTML email content
        email_config: Dictionary with email configuration
            {
                'api_key': 'your-resend-api-key',
                'from_email': 'onboarding@resend.dev' or 'your-verified-domain@yourdomain.com'
            }
    
    Returns:
        True if successful, False otherwise
    """
    try:
        url = "https://api.resend.com/emails"
        headers = {
            "Authorization": f"Bearer {email_config['api_key']}",
            "Content-Type": "application/json"
        }
        
        data = {
            "from": email_config['from_email'],
            "to": [to_email],
            "subject": subject,
            "html": html_content
        }
        
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            print(f"Email sent successfully to {to_email}")
            return True
        else:
            print(f"Failed to send email to {to_email}: {response.text}")
            return False
    
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")
        return False

def send_recommendations_to_subscribers(email_config):
    """
    Send investment recommendations to all active subscribers
    Only sends on first and last day of each week
    
    This function should be called by a scheduler (e.g., cron job, task scheduler)
    """
    from subscription_manager import get_active_subscriptions
    
    today = datetime.now()
    current_day = today.day
    current_week = (current_day - 1) // 7 + 1  # Week 1-4 of the month
    
    # Determine first and last days of each week
    week_days = {
        1: (1, 7),
        2: (8, 14),
        3: (15, 21),
        4: (22, calendar.monthrange(today.year, today.month)[1])  # Last day of month
    }
    
    # Check if today is first or last day of current week
    if current_week not in week_days:
        print(f"Not a scheduled day (day {current_day})")
        return
    
    first_day, last_day = week_days[current_week]
    if current_day not in (first_day, last_day):
        print(f"Not a scheduled day. Week {current_week} emails send on days {first_day} and {last_day}")
        return
    
    print(f"Today is day {current_day} - Week {current_week} scheduled day")
    
    subscriptions = get_active_subscriptions()
    emails_sent = 0
    
    for sub in subscriptions:
        # Check if user wants email this week
        if current_week not in sub.get('schedule_weeks', []):
            continue
        
        email_content = generate_recommendation_email(
            sub['tickers'],
            sub['weights'],
            sub['budget'],
            sub['email']
        )
        
        if email_content:
            subject = f"Smart DCA Investment Recommendations - {today.strftime('%b %d, %Y')}"
            if send_email(sub['email'], subject, email_content, email_config):
                emails_sent += 1
    
    print(f"Sent {emails_sent} recommendation emails")
