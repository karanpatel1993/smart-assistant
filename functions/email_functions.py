import datetime
import json
import os
import re

# Path to store our mock data
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
EMAIL_FILE = os.path.join(DATA_DIR, 'emails.json')

# Ensure the data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Initialize the email file if it doesn't exist
if not os.path.exists(EMAIL_FILE):
    with open(EMAIL_FILE, 'w') as f:
        json.dump([], f)

def get_email_from_name(name):
    """
    Simple function that converts a name to an email address.
    In a real app, this would query a contacts database.
    """
    # Remove any non-alphanumeric characters and convert to lowercase
    email_name = re.sub(r'[^a-zA-Z0-9]', '', name.lower())
    return f"{email_name}@example.com"

def send_email(recipient, subject, body=None):
    """
    Send an email to the specified recipient.
    This is a mock function that simulates sending an email.
    """
    try:
        # If recipient is a name, convert it to email
        if '@' not in recipient:
            recipient = get_email_from_name(recipient)
        
        # Create a default body if none provided
        if not body:
            body = f"This is a message regarding: {subject}"
        
        # Load existing emails
        with open(EMAIL_FILE, 'r') as f:
            emails = json.load(f)
        
        # Create the new email
        new_email = {
            "id": len(emails) + 1,
            "to": recipient,
            "subject": subject,
            "body": body,
            "sent_at": datetime.datetime.now().isoformat(),
            "status": "sent"
        }
        
        # Add to our email log
        emails.append(new_email)
        
        # Save the updated emails
        with open(EMAIL_FILE, 'w') as f:
            json.dump(emails, f, indent=2)
        
        return {
            "success": True,
            "email": {
                "to": recipient,
                "subject": subject,
                "sent_at": new_email["sent_at"]
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_sent_emails(limit=5):
    """Get a list of recently sent emails."""
    try:
        # Load existing emails
        with open(EMAIL_FILE, 'r') as f:
            emails = json.load(f)
        
        # Sort by sent time, descending
        emails.sort(key=lambda x: x['sent_at'], reverse=True)
        
        return {"emails": emails[:limit]}
    except Exception as e:
        return {"error": str(e)} 