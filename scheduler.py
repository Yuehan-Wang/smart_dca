import os
import sys
from datetime import datetime
from pathlib import Path
from email_service import send_recommendations_to_subscribers

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Install with: pip install python-dotenv")
    print("Falling back to system environment variables...")

def main():
    # Get configuration from .env file or environment variables
    api_key = os.environ.get('RESEND_API_KEY')
    from_email = os.environ.get('FROM_EMAIL', 'Smart DCA <onboarding@resend.dev>')
    
    if not api_key:
        print("ERROR: Resend API key not configured!")
        print("\nSetup is easy - just 3 steps:")
        print("1. Sign up at https://resend.com (FREE for 3,000 emails/month)")
        print("2. Get your API key from the dashboard")
        print("3. Create a .env file in the project root with:")
        print("   RESEND_API_KEY=re_xxxxxxxxxxxxx")
        print("\nOr set environment variable:")
        print("   - Windows: setx RESEND_API_KEY \"re_xxxxxxxxxxxxx\"")
        print("   - Linux/Mac: export RESEND_API_KEY=\"re_xxxxxxxxxxxxx\"")
        sys.exit(1)
    
    email_config = {
        'api_key': api_key,
        'from_email': from_email
    }
    
    print(f"Starting Smart DCA Email Scheduler - {datetime.now()}")
    print(f"Sending from: {email_config['from_email']}")
    
    try:
        send_recommendations_to_subscribers(email_config)
        print("Email distribution completed successfully!")
    except Exception as e:
        print(f"Error during email distribution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
