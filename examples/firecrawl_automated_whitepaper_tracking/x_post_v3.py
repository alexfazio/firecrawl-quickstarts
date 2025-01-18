import os
import base64
import hashlib
import secrets
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import requests
import logging
import re
from dotenv import load_dotenv
from requests_oauthlib import OAuth2Session
import time

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# API endpoints - Updated to correct domains
MEDIA_ENDPOINT_URL = 'https://api.x.com/2/media/upload'
POST_TO_X_URL = 'https://api.x.com/2/tweets'
AUTH_URL = "https://twitter.com/i/oauth2/authorize"
TOKEN_URL = "https://api.twitter.com/2/oauth2/token"
CALLBACK_URL = "http://127.0.0.1:8000/callback"

class CallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback"""
    code = None
    
    def do_GET(self):
        """Process callback GET request"""
        query = parse_qs(urlparse(self.path).query)
        CallbackHandler.code = query.get('code', [None])[0]
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Authorization successful! You can close this window.")

class XPost:
    def __init__(self):
        client_id = os.getenv('X_OAUTH2_CLIENT_ID')
        client_secret = os.getenv('X_OAUTH2_CLIENT_SECRET')
        self.access_token = os.getenv('X_OAUTH2_ACCESS_TOKEN')
        refresh_token = os.getenv('X_OAUTH2_REFRESH_TOKEN')
        
        # Initialize OAuth2 session
        self.oauth = OAuth2Session(
            client_id,
            token={
                'access_token': self.access_token,
                'refresh_token': refresh_token,
                'token_type': 'bearer'
            }
        )
        
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "User-Agent": "XPostBot"
        }

    def upload_image(self, image_path):
        """Upload an image using the v2 endpoint with multi-step process"""
        logger.info(f"Attempting to upload image: {image_path}")
        
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        total_bytes = os.path.getsize(image_path)
        
        # Step 1: INIT
        init_data = {
            'command': 'INIT',
            'media_type': 'image/png',
            'total_bytes': total_bytes,
            'media_category': 'tweet_image'
        }
        
        response = self.oauth.post(MEDIA_ENDPOINT_URL, params=init_data, headers=self.headers)
        if response.status_code < 200 or response.status_code > 299:  # Accept any 2xx status
            logger.error(f"Media INIT failed: {response.text}")
            raise Exception(f"Failed to initialize media upload: {response.text}")
        
        media_id = response.json()['data']['id']
        
        # Step 2: APPEND
        with open(image_path, 'rb') as file:
            chunk = file.read()
            files = {'media': ('chunk', chunk, 'application/octet-stream')}
            data = {
                'command': 'APPEND',
                'media_id': media_id,
                'segment_index': 0
            }
            
            response = self.oauth.post(MEDIA_ENDPOINT_URL, data=data, files=files)
            if response.status_code < 200 or response.status_code > 299:  # Accept any 2xx status
                logger.error(f"Media APPEND failed: {response.text}")
                raise Exception(f"Failed to append media: {response.text}")
        
        # Step 3: FINALIZE
        finalize_data = {
            'command': 'FINALIZE',
            'media_id': media_id
        }
        
        response = self.oauth.post(MEDIA_ENDPOINT_URL, params=finalize_data, headers=self.headers)
        if response.status_code < 200 or response.status_code > 299:  # Accept any 2xx status
            logger.error(f"Media FINALIZE failed: {response.text}")
            raise Exception(f"Failed to finalize media: {response.text}")
        
        logger.info(f"Successfully uploaded media with ID: {media_id}")
        return media_id

    def create_tweet(self, text, media_id):
        """Create a tweet with text and attached media"""
        logger.info("Attempting to create tweet")
        
        payload = {
            'text': text,
            'media': {
                'media_ids': [media_id]
            }
        }
        
        response = self.oauth.post(POST_TO_X_URL, json=payload, headers=self.headers)
        
        logger.debug(f"Response status code: {response.status_code}")
        logger.debug(f"Response headers: {response.headers}")
        logger.debug(f"Response body: {response.text}")

        if response.status_code == 429:
            reset_time = int(response.headers.get('x-app-limit-24hour-reset', 0))
            wait_seconds = max(reset_time - int(time.time()), 0)
            logger.warning(f"Rate limit exceeded. Waiting {wait_seconds} seconds...")
            time.sleep(wait_seconds)
            # Retry the request
            return self.create_tweet(text, media_id)
        elif response.status_code != 201:
            logger.error(f"Tweet creation failed with status {response.status_code}")
            logger.error(f"Response: {response.text}")
            raise Exception(f"Failed to create tweet: {response.text}")
        
        return response.json()

def main():
    try:
        poster = XPost()
        
        # Use absolute path or correct relative path to your image
        image_path = "test.png"  # Update this to your image path
        logger.info(f"Starting process with image: {image_path}")
        
        # Upload image
        media_id = poster.upload_image(image_path)
        
        # Create tweet with image
        tweet_text = "Testing X API v2 with an image attachment! 🚀"
        result = poster.create_tweet(tweet_text, media_id)
        
        logger.info("Tweet posted successfully!")
        logger.info(f"Result: {result}")
    
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()