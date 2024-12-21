import os
from dotenv import load_dotenv
import requests
import json

def test_discord_webhook():
    # Load environment variables
    load_dotenv()
    
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
    if not webhook_url:
        raise ValueError("DISCORD_WEBHOOK_URL not found in .env file")

    # Test message
    message = {
        "content": "🎉 Webhook test successful! Your Discord notifications are working.",
        "embeds": [{
            "title": "Test Embed",
            "description": "This is a test message to verify the webhook configuration.",
            "color": 5814783,  # A nice blue color
            "fields": [
                {
                    "name": "Status",
                    "value": "✅ Connected",
                    "inline": True
                }
            ]
        }]
    }

    try:
        response = requests.post(
            webhook_url,
            data=json.dumps(message),
            headers={'Content-Type': 'application/json'},
            timeout=10  # 10 seconds timeout
        )
        response.raise_for_status()
        print("Test message sent successfully!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error sending test message: {e}")
        return False

if __name__ == "__main__":
    test_discord_webhook()