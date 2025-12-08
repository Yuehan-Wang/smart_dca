import logging
import os
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

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
    Rounds values to 1 decimal place to avoid 33.333333% ugly formats.
    """
    if not weights:
        return ""
    
    labels = list(weights.keys())
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
                    "formatter": "(value) => { return value + '%' }"
                }
            }
        }
    }
    
    base_url = "https://quickchart.io/chart?c="
    chart_json = str(chart_config).replace("'", '"')
    return f"{base_url}{chart_json}"

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
    <div style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2a9d8f;">Welcome to Smart DCA!</h2>
        <p>You have successfully subscribed to automated investment updates.</p>
        
        <div style="background-color: #f4f4f4; padding: 15px; border-radius: 8px;">
            <h3>Your Configuration</h3>
            <p><b>Monthly Budget:</b> ${budget:,.0f}</p>
            <p><b>Notification Schedule:</b> {week_str} (Sent on Day 1 & Day 7)</p>
            <p><b>Target Portfolio:</b></p>
            <ul>{portfolio_html}</ul>
        </div>

        <div style="text-align: center; margin: 20px 0;">
            <img src="{chart_url}" alt="Portfolio Pie Chart" style="max-width: 100%; border-radius: 10px;">
        </div>
        
        <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="font-size: 12px; color: #888;">
            You can update your preferences or unsubscribe at any time via the Smart DCA dashboard.
        </p>
    </div>
    """

    try:
        r = resend_module.Emails.send({
            "from": sender,
            "to": user_email,
            "subject": "Smart DCA: Subscription Confirmed",
            "html": html_content
        })
        return r
    except Exception as e:
        print(f"Error sending email: {e}")
        raise e

def send_unsubscribe_email(user_email, email_config=None):
    """Sends an unsubscribe confirmation."""
    resend_module = _ensure_resend()
    if email_config:
        api_key = email_config.get('api_key')
        if api_key:
            resend_module.api_key = api_key
        sender = email_config.get('from_email', FROM_EMAIL)
    else:
        sender = FROM_EMAIL

    html_content = """
    <div style="font-family: Arial, sans-serif; color: #333;">
        <h2>Unsubscribed</h2>
        <p>You have been removed from the Smart DCA notification list.</p>
        <p>We hope to see you again when the markets get interesting!</p>
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
        color = "black"
        if mult_val > 1.0: color = "green"
        elif mult_val < 1.0: color = "red"
        
        table_rows += f"""
        <tr style="border-bottom: 1px solid #eee;">
            <td style="padding: 10px;"><b>{item['Ticker']}</b></td>
            <td style="padding: 10px;">{item['Price']}</td>
            <td style="padding: 10px; color: #666;">{item['Condition']}</td>
            <td style="padding: 10px; font-weight: bold; color: {color};">{item['Action']}</td>
            <td style="padding: 10px;">{item['Target Invest']}</td>
        </tr>
        """

    html_content = f"""
    <div style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2a9d8f;">Smart DCA Action Report</h2>
        <p>Here are your recommended actions for this week based on current market data.</p>
        
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
            <h3 style="margin-top: 0;">Total Capital to Deploy: <span style="color: #2a9d8f;">${total_invest:,.0f}</span></h3>
        </div>

        <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
            <thead>
                <tr style="background-color: #eee; text-align: left;">
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
             <p style="font-size: 14px; color: #888;">Your Target Allocation</p>
             <img src="{chart_url}" alt="Allocation Chart" style="max-width: 100%; border-radius: 10px;">
        </div>
        
        <p style="font-size: 12px; color: #888; margin-top: 30px;">
            Disclaimer: This is an automated report based on technical indicators. Not financial advice.
        </p>
    </div>
    """

    try:
        resend_module.Emails.send({
            "from": FROM_EMAIL,
            "to": user_email,
            "subject": f"Smart DCA Alert: Deploy ${total_invest:,.0f}",
            "html": html_content
        })
        return True
    except Exception as e:
        print(f"Error sending notification email: {e}")
        return False