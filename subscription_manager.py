import json
import os
from datetime import datetime
from pathlib import Path

# File to store subscriptions
SUBSCRIPTIONS_FILE = Path("subscriptions.json")

def load_subscriptions():
    """Load all subscriptions from file"""
    if SUBSCRIPTIONS_FILE.exists():
        try:
            with open(SUBSCRIPTIONS_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_subscriptions(subscriptions):
    """Save subscriptions to file"""
    with open(SUBSCRIPTIONS_FILE, 'w') as f:
        json.dump(subscriptions, f, indent=2)

def add_subscription(email, tickers, weights, budget, schedule_weeks):
    """
    Add a new email subscription
    
    Args:
        email: User's email address
        tickers: List of tickers
        weights: Dictionary of ticker weights
        budget: Contribution budget
        schedule_weeks: List of weeks to send (1-4)
    """
    subscriptions = load_subscriptions()
    
    # Check if email already exists
    for sub in subscriptions:
        if sub['email'] == email:
            # Update existing subscription
            sub['tickers'] = tickers
            sub['weights'] = weights
            sub['budget'] = budget
            sub['schedule_weeks'] = schedule_weeks
            sub['updated_at'] = datetime.now().isoformat()
            save_subscriptions(subscriptions)
            return "updated"
    
    # Add new subscription
    new_sub = {
        'email': email,
        'tickers': tickers,
        'weights': weights,
        'budget': budget,
        'schedule_weeks': schedule_weeks,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'active': True
    }
    subscriptions.append(new_sub)
    save_subscriptions(subscriptions)
    return "added"

def remove_subscription(email):
    """Remove a subscription by email"""
    subscriptions = load_subscriptions()
    subscriptions = [s for s in subscriptions if s['email'] != email]
    save_subscriptions(subscriptions)

def get_subscription(email):
    """Get subscription details for an email"""
    subscriptions = load_subscriptions()
    for sub in subscriptions:
        if sub['email'] == email:
            return sub
    return None

def get_active_subscriptions():
    """Get all active subscriptions"""
    subscriptions = load_subscriptions()
    return [s for s in subscriptions if s.get('active', True)]
