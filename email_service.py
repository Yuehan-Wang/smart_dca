import logging
import os
import json
import urllib.parse
from datetime import datetime

logger = logging.getLogger(__name__)

# Defensive import to prevent crashes if requirements aren't installed
try:
    import resend  # type: ignore[import-not-found]
except ModuleNotFoundError:
    resend = None  # type: ignore[assignment]
    logger.warning("Optional dependency 'resend' not installed; email features disabled.")

# Load API Key
RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'Smart DCA <onboarding@resend.dev>')

def _ensure_resend():
    if resend is None:
        raise RuntimeError("Install the 'resend' package (`pip install resend`) to enable Smart DCA email features.")
    if RESEND_API_KEY and getattr(resend, 'api_key', None) != RESEND_API_KEY:
        resend.api_key = RESEND_API_KEY
    return resend

def generate_pie_chart_url(weights):
    """
    Generates a QuickChart URL for the portfolio allocation.
    Uses json.dumps and urllib.parse.quote to PREVENT chart errors.
    """
    if not weights:
        return ""
    
    labels = list(weights.keys())
    # Round values to 1 decimal place to fix the "33.33333%" ugly format
    data = [round(v, 1) for v in weights.values()]
    
    chart_config = {
        "type": "pie",
        "data": {
            "labels": labels,
            "datasets": [{
                "data": data,
                "backgroundColor": ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF", "#FF9F40", "#E7E9ED", "#76A346", "#D32F2F", "#1976D2", "#FBC02D", "#388E3C", "#7B1FA2", "#F57C00", "#455A64", "#C2185B", "#00796B", "#512DA8", "#F06292", "#4E342E"]
            }]
        },
        "options": {
            "plugins": {
                "datalabels": {
                    "color": "white",
                    "font": {"weight": "bold", "size": 14},
                    # We pass this function as a string for QuickChart to interpret
                    "formatter": "(value) => { return value + '%' }"
                }
            }
        }
    }
    
    # CRITICAL FIX: Encode JSON properly to avoid 'Unexpected token' errors
    base_url = "https://quickchart.io/chart?c="
    chart_json = json.dumps(chart_config)
    encoded_json = urllib.parse.quote(chart_json)
    
    return f"{base_url}{encoded_json}"

def send_confirmation_email(user_email, weights, budget, weeks, email_config=None):
    """Sends a subscription confirmation email."""
    resend_module = _ensure_resend()

    # Use config if passed (for local testing), else env vars
    if email_config:
        api_key = email_config.get('api_key')
        if api_key:
            resend_module.api_key = api_key
        sender = email_config.get('from_email', FROM_EMAIL)
    else:
        sender = FROM_EMAIL

    portfolio_html = ""
    for ticker, weight in weights.items():
        portfolio_html += f"<li><b>{ticker}</b>: {weight:.1f}%</li>"

    week_str = ", ".join([f"Week {w}" for w in weeks])
    chart_url = generate_pie_chart_url(weights)

    html_content = f"""
    <div style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto; border: 1px solid #eee; border-radius: 8px; overflow: hidden;">
        <div style="background-color: #2a9d8f; padding: 20px; text-align: center;">
            <h2 style="color: white; margin: 0;">Welcome to Smart DCA!</h2>
        </div>
        
        <div style="padding: 20px;">
            <p style="font-size: 16px;">You have successfully subscribed to automated investment updates.</p>
            
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-top: 20px;">
                <h3 style="color: #264653; margin-top: 0;">Your Configuration</h3>
                <p style="margin: 5px 0;"><b>Monthly Budget:</b> ${budget:,.0f}</p>
                <p style="margin: 5px 0;"><b>Notification Schedule:</b> {week_str} (Day 1 & 7)</p>
                <p style="margin: 5px 0;"><b>Target Portfolio:</b></p>
                <ul style="margin-top: 5px;">{portfolio_html}</ul>
            </div>

            <div style="text-align: center; margin: 30px 0;">
                <img src="{chart_url}" alt="Portfolio Pie Chart" style="max-width: 100%; border-radius: 10px;">
            </div>
            
            <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
            <p style="font-size: 12px; color: #888; text-align: center;">
                You can update your preferences or unsubscribe at any time via the Smart DCA dashboard.
            </p>
        </div>
    </div>
    """

    try:
        r = resend_module.Emails.send({
            "from": sender,
            "to": user_email,
            "subject": "Smart DCA: Subscription Confirmed ✅",
            "html": html_content
        })
        return r
    except Exception as e:
        print(f"Error sending email: {e}")
        raise e

def send_unsubscribe_email(user_email, email_config=None):
    """Sends an unsubscribe confirmation (Now styled to match the app)."""
    resend_module = _ensure_resend()
    if email_config:
        api_key = email_config.get('api_key')
        if api_key:
            resend_module.api_key = api_key
        sender = email_config.get('from_email', FROM_EMAIL)
    else:
        sender = FROM_EMAIL

    # REDESIGNED: Matches the Teal/Dark theme
    html_content = """
    <div style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto; border: 1px solid #eee; border-radius: 8px; overflow: hidden;">
        <div style="background-color: #264653; padding: 20px; text-align: center;">
            <h2 style="color: white; margin: 0;">Unsubscribed</h2>
        </div>
        <div style="padding: 30px; text-align: center;">
            <p style="font-size: 16px; line-height: 1.5;">
                You have been removed from the <b>Smart DCA</b> notification list.
            </p>
            <p style="color: #666;">
                No further emails will be sent to this address.
            </p>
            <div style="margin-top: 30px;">
                <p style="font-size: 14px; color: #2a9d8f; font-weight: bold;">
                    We hope to see you again when the markets get interesting!
                </p>
            </div>
        </div>
    </div>
    """

    try:
        resend_module.Emails.send({
            "from": sender,
            "to": user_email,
            "subject": "Smart DCA: Unsubscribed",
            "html": html_content
        })
    except Exception as e:
        print(f"Error sending unsubscribe email: {e}")

def send_notification_email(user_email, action_data, total_invest, weights):
    """
    Sends the weekly/monthly action report.
    """
    resend_module = _ensure_resend()
    chart_url = generate_pie_chart_url(weights)
    
    # Build the action table HTML
    table_rows = ""
    for item in action_data:
        # Determine color based on action multiplier
        mult_val = float(item['Action'].replace('x', ''))
        color = "#264653" # Dark Blue/Black default
        if mult_val > 1.0: color = "#2a9d8f" # Teal Green
        elif mult_val < 1.0: color = "#e76f51" # Burnt Orange/Red
        
        table_rows += f"""
        <tr style="border-bottom: 1px solid #eee;">
            <td style="padding: 12px; font-weight:bold;">{item['Ticker']}</td>
            <td style="padding: 12px;">{item['Price']}</td>
            <td style="padding: 12px; color: #666; font-size: 14px;">{item['Condition']}</td>
            <td style="padding: 12px; font-weight: bold; color: {color};">{item['Action']}</td>
            <td style="padding: 12px;">{item['Target Invest']}</td>
        </tr>
        """

    html_content = f"""
    <div style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto; border: 1px solid #eee; border-radius: 8px; overflow: hidden;">
        <div style="background-color: #2a9d8f; padding: 20px; text-align: center;">
            <h2 style="color: white; margin: 0;">Smart DCA Action Report</h2>
        </div>
        
        <div style="padding: 20px;">
            <p style="text-align: center; color: #666;">Here are your recommended actions for this period.</p>
            
            <div style="background-color: #e9c46a; color: #264653; padding: 15px; border-radius: 8px; margin: 20px 0; text-align: center;">
                <span style="font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">Total Capital to Deploy</span><br>
                <span style="font-size: 28px; font-weight: bold;">${total_invest:,.0f}</span>
            </div>

            <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
                <thead>
                    <tr style="background-color: #f4f4f4; text-align: left;">
                        <th style="padding: 10px;">Ticker</th>
                        <th style="padding: 10px;">Price</th>
                        <th style="padding: 10px;">Signal</th>
                        <th style="padding: 10px;">Mult</th>
                        <th style="padding: 10px;">Invest</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>

            <div style="text-align: center; margin: 20px 0;">
                 <p style="font-size: 14px; color: #888; margin-bottom: 10px;">Current Target Allocation</p>
                 <img src="{chart_url}" alt="Allocation Chart" style="max-width: 100%; border-radius: 10px;">
            </div>
            
            <hr style="border: 0; border-top: 1px solid #eee; margin: 30px 0;">
            <p style="font-size: 11px; color: #999; text-align: center; line-height: 1.4;">
                <b>Disclaimer:</b> This is an automated report based on technical analysis algorithms. 
                It does not constitute financial advice. Market conditions change rapidly. 
                Invest responsibly.
            </p>
        </div>
    </div>
    """

    try:
        resend_module.Emails.send({
            "from": FROM_EMAIL,
            "to": user_email,
            "subject": f"Smart DCA Alert: Deploy ${total_invest:,.0f} 🚀",
            "html": html_content
        })
        return True
    except Exception as e:
        print(f"Error sending notification email: {e}")
        return False