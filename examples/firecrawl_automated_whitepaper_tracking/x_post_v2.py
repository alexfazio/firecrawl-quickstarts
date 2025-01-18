"""Module for posting research papers to X (Twitter)."""

import os
import base64
import hashlib
import secrets
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from dotenv import load_dotenv, set_key, find_dotenv
import requests
from typing import Optional
from logging_config import setup_base_logging, log_function_call
import tempfile
from playwright.sync_api import sync_playwright
import mimetypes
import random
from datetime import datetime
from requests_oauthlib import OAuth1
import time

# Configure logging using the centralized configuration
logger = setup_base_logging(
    logger_name="x_poster",
    log_file="x_poster.log",
    format_string='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s'
)

load_dotenv()

AUTH_URL = "https://twitter.com/i/oauth2/authorize"
TOKEN_URL = "https://api.twitter.com/2/oauth2/token"
CALLBACK_URL = "http://127.0.0.1:8000/callback"
X_API_URL = "https://api.twitter.com/2/tweets"
MEDIA_UPLOAD_URL = "https://upload.twitter.com/1.1/media/upload.json"
POST_UPDATE_URL = "https://api.twitter.com/1.1/statuses/update.json"  # v1.1 endpoint
PDF_SCREENSHOT_SIZE = 1080  # 1:1 ratio
PDF_LOAD_TIMEOUT = 30000  # 30 seconds

@log_function_call
def generate_pkce_pair():
    """Generate PKCE code verifier and challenge"""
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b'=').decode()
    
    logger.debug(f"Generated PKCE - Verifier: {len(code_verifier)} chars, Challenge: {len(code_challenge)} chars")
    return code_verifier, code_challenge

class CallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback"""
    code = None
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(f"OAuth Callback: {format%args}")
    
    def do_GET(self):
        """Process callback GET request"""
        logger.info(f"Received callback request: {self.path}")
        
        query = parse_qs(urlparse(self.path).query)
        CallbackHandler.code = query.get('code', [None])[0]
        
        if CallbackHandler.code:
            logger.info("Successfully received authorization code")
        else:
            logger.error(f"No authorization code in callback. Query params: {query}")
            
        # Log any error parameters
        if 'error' in query:
            logger.error(f"Error in callback: {query['error']}")
        if 'error_description' in query:
            logger.error(f"Error description: {query['error_description']}")
            
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Authorization successful! You can close this window.")
        
@log_function_call
def load_stored_tokens():
    """Load stored OAuth 2.0 tokens from .env"""
    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)
    
    # Use OAuth 2.0 specific variables
    access_token = os.getenv('X_OAUTH2_ACCESS_TOKEN')
    refresh_token = os.getenv('X_OAUTH2_REFRESH_TOKEN')
    
    if access_token and refresh_token:
        logger.debug("Successfully loaded stored OAuth 2.0 tokens")
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': os.getenv('X_OAUTH2_TOKEN_EXPIRES_IN'),
            'scope': os.getenv('X_OAUTH2_TOKEN_SCOPE')
        }
    logger.warning("No stored OAuth 2.0 tokens found")
    return None

@log_function_call
def save_tokens(tokens):
    """Save OAuth 2.0 tokens to .env"""
    dotenv_path = find_dotenv()
    
    try:
        # Use different variable names for OAuth 2.0
        set_key(dotenv_path, 'X_OAUTH2_ACCESS_TOKEN', tokens['access_token'])
        set_key(dotenv_path, 'X_OAUTH2_REFRESH_TOKEN', tokens['refresh_token'])
        set_key(dotenv_path, 'X_OAUTH2_TOKEN_EXPIRES_IN', str(tokens['expires_in']))
        set_key(dotenv_path, 'X_OAUTH2_TOKEN_SCOPE', tokens['scope'])
        load_dotenv(dotenv_path)
        logger.info("Successfully saved OAuth 2.0 tokens to .env")
    except Exception as e:
        logger.error(f"Failed to save tokens: {str(e)}")
        raise

def refresh_access_token(refresh_token):
    """Get new access token using refresh token"""
    auth = (
        os.getenv('X_OAUTH2_CLIENT_ID'),
        os.getenv('X_OAUTH2_CLIENT_SECRET')
    )
    
    data = {
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    
    response = requests.post(TOKEN_URL, auth=auth, data=data)
    return response.json()

def get_oauth2_token():
    """Get OAuth 2.0 token, using stored tokens if available"""
    # Try to load stored tokens
    tokens = load_stored_tokens()
    
    if tokens:
        logger.debug(f"Found stored tokens with keys: {list(tokens.keys())}")
        if 'refresh_token' in tokens:
            try:
                logger.info("Attempting to refresh token...")
                new_tokens = refresh_access_token(tokens['refresh_token'])
                logger.debug(f"Refresh response keys: {list(new_tokens.keys())}")
                save_tokens(new_tokens)
                return new_tokens['access_token']
            except Exception as e:
                logger.error(f"Token refresh failed: {e}")
        else:
            logger.error("Stored tokens missing refresh_token")
    
    # If no stored tokens or refresh failed, do full authorization
    logger.info("Starting OAuth 2.0 PKCE flow")
    code_verifier, code_challenge = generate_pkce_pair()
    
    auth_params = {
        'response_type': 'code',
        'client_id': os.getenv('X_OAUTH2_CLIENT_ID'),
        'redirect_uri': CALLBACK_URL,
        'scope': 'tweet.write tweet.read users.read offline.access',
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
        'state': secrets.token_urlsafe(32)
    }
    
    logger.info("Starting local callback server")
    server = HTTPServer(('127.0.0.1', 8000), CallbackHandler)
    
    auth_url = f"{AUTH_URL}?{'&'.join(f'{k}={v}' for k,v in auth_params.items())}"
    logger.info(f"Opening authorization URL: {auth_url}")
    webbrowser.open(auth_url)
    
    logger.info("Waiting for callback...")
    server.handle_request()
    
    if not CallbackHandler.code:
        raise Exception("Failed to get authorization code")
    
    logger.info("Exchanging code for token")
    token_data = {
        'code': CallbackHandler.code,
        'grant_type': 'authorization_code',
        'client_id': os.getenv('X_OAUTH2_CLIENT_ID'),
        'redirect_uri': CALLBACK_URL,
        'code_verifier': code_verifier
    }
    
    auth = (
        os.getenv('X_OAUTH2_CLIENT_ID'),
        os.getenv('X_OAUTH2_CLIENT_SECRET')
    )
    
    response = requests.post(TOKEN_URL, auth=auth, data=token_data)
    if response.status_code != 200:
        raise Exception(f"Token exchange failed: {response.text}")
        
    token_json = response.json()
    logger.debug(f"Received token response with keys: {list(token_json.keys())}")
    save_tokens(token_json)
    return token_json['access_token']

def format_post(
    paper_title: str,
    authors: list,
    url: str,
    pdf_url: Optional[str] = None,
    arxiv_url: Optional[str] = None,
    github_url: Optional[str] = None
) -> str:
    """Format paper details into X post text"""
    # Start with title and truncate if needed
    post = f"📚 {paper_title[:100]}{'...' if len(paper_title) > 100 else ''}\n\n"
    
    # Add authors (limited to first 2 if many)
    if len(authors) > 2:
        authors_text = f"by {', '.join(authors[:2])} et al."
    else:
        authors_text = f"by {', '.join(authors)}"
    post += f"{authors_text}\n\n"
    
    # Add links
    post += f"🔗 {url}"
    if pdf_url:
        post += f"\n📄 {pdf_url}"
    if arxiv_url:
        post += f"\n📝 {arxiv_url}"
    if github_url:
        post += f"\n💻 {github_url}"
        
    return post

@log_function_call
def capture_pdf_screenshot(pdf_url: str) -> Optional[bytes]:
    """Capture first page screenshot of PDF using Playwright."""
    logger.info(f"Attempting to capture screenshot of PDF: {pdf_url}")
    
    try:
        with sync_playwright() as p:
            logger.debug("Launching browser...")
            browser = p.chromium.launch(headless=False)  # Run in non-headless mode for debugging
            
            logger.debug("Creating new page with viewport size: %dx%d", 
                        PDF_SCREENSHOT_SIZE, PDF_SCREENSHOT_SIZE)
            page = browser.new_page(
                viewport={'width': PDF_SCREENSHOT_SIZE, 'height': PDF_SCREENSHOT_SIZE}
            )
            page.set_default_timeout(PDF_LOAD_TIMEOUT)
            
            logger.debug("Loading PDF...")
            page.goto(pdf_url, wait_until='networkidle')  # Wait for network to be idle
            logger.info("✅ PDF loaded successfully")
            
            # Add small delay to ensure PDF is rendered
            logger.debug("Waiting for PDF to render...")
            page.wait_for_timeout(2000)  # 2 second delay
            
            logger.debug("Taking screenshot...")
            screenshot = page.screenshot()
            
            # Validate screenshot data
            if screenshot and len(screenshot) > 0:
                logger.info(f"✅ Screenshot captured successfully! Size: {len(screenshot)} bytes")
            else:
                logger.error("❌ Screenshot data is empty!")
                return None
            
            browser.close()
            logger.info("Browser closed successfully")
            return screenshot
    except Exception as e:
        logger.error(f"❌ Failed to capture PDF screenshot: {str(e)}")
        logger.error("Exception details:", exc_info=True)
        return None

@log_function_call
def check_media_status(media_id: str, auth: OAuth1) -> bool:
    """Check if media has finished processing."""
    status_url = f"https://upload.twitter.com/1.1/media/upload.json?command=STATUS&media_id={media_id}"
    
    try:
        response = requests.get(status_url, auth=auth)
        if response.status_code == 200:
            processing_info = response.json().get('processing_info', {})
            state = processing_info.get('state')
            
            if state == 'succeeded':
                return True
            elif state == 'pending':
                time.sleep(3)  # Wait before checking again
                return check_media_status(media_id, auth)
            else:
                logger.error(f"Media processing failed: {processing_info}")
                return False
    except Exception as e:
        logger.error(f"Error checking media status: {str(e)}")
        return False

@log_function_call
def upload_media(image_data: bytes) -> Optional[str]:
    """Upload media using v1.1 API with OAuth 1.0a."""
    if not image_data:
        logger.error("❌ No image data provided for upload")
        return None
        
    # Create OAuth 1.0a auth
    auth = OAuth1(
        client_key=os.getenv('X_API_KEY'),
        client_secret=os.getenv('X_API_SECRET'),
        resource_owner_key=os.getenv('X_ACCESS_TOKEN'),
        resource_owner_secret=os.getenv('X_ACCESS_TOKEN_SECRET')
    )
    
    try:
        logger.info("📤 Uploading media using v1.1 API...")
        files = {'media': image_data}
        response = requests.post(MEDIA_UPLOAD_URL, auth=auth, files=files)
        
        if response.status_code != 200:
            logger.error(f"❌ Media upload failed: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return None
            
        media_id = response.json()['media_id_string']
        logger.info(f"✅ Media upload successful! (ID: {media_id})")
        return media_id
        
    except Exception as e:
        logger.error(f"❌ Failed to upload media: {str(e)}")
        logger.error("Exception details:", exc_info=True)
        return None

@log_function_call
def wait_for_rate_limit(response) -> bool:
    """Handle rate limit waiting. Returns True if waited, False if no wait needed."""
    try:
        # Only proceed if we have rate limit headers
        if 'x-rate-limit-remaining' not in response.headers:
            return False
            
        limit = int(response.headers.get('x-rate-limit-limit', 0))
        remaining = int(response.headers.get('x-rate-limit-remaining', 0))
        reset_time = int(response.headers.get('x-rate-limit-reset', 0))
        
        logger.info("Rate Limit Status:")
        logger.info(f"- Limit: {limit} requests")
        logger.info(f"- Remaining: {remaining} requests")
        
        # Only wait if we're actually rate limited
        if response.status_code == 429:
            current_time = time.time()
            wait_seconds = max(reset_time - current_time, 0)
            
            reset_datetime = datetime.fromtimestamp(reset_time)
            logger.info(f"Rate limit reset time: {reset_datetime}")
            
            if wait_seconds > 0:
                logger.info(f"Waiting {wait_seconds:.0f} seconds...")
                time.sleep(wait_seconds)
                return True
                
        return False
        
    except Exception as e:
        logger.error(f"Error in rate limit handling: {str(e)}")
        return False

@log_function_call
def post_paper(paper_title: str, authors: list, url: str, pdf_url: Optional[str] = None, 
               arxiv_url: Optional[str] = None, github_url: Optional[str] = None, max_retries: int = 3):
    """Post paper using v2 API."""
    logger.info(f"🔄 Starting post process for: {paper_title}")
    
    # Step 1: Upload media using v1.1 API if PDF URL provided
    media_id = None
    if pdf_url:
        logger.info("📸 Capturing PDF screenshot...")
        screenshot = capture_pdf_screenshot(pdf_url)
        if screenshot:
            media_id = upload_media(screenshot)  # Uses v1.1 API with OAuth 1.0a
    
    # Step 2: Get OAuth 2.0 token for v2 API post
    token = get_oauth2_token()
    if not token:
        logger.error("❌ Failed to get OAuth 2.0 token")
        return None
    
    # Format post text
    post_text = format_post(paper_title, authors, url, pdf_url, arxiv_url, github_url)
    
    # Prepare v2 API payload
    payload = {
        "text": post_text
    }
    
    # Add media if available
    if media_id:
        payload["media"] = {
            "media_ids": [str(media_id)]
        }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Post using v2 API
    retry_count = 0
    while retry_count < max_retries:
        try:
            logger.info("📝 Creating post using v2 API...")
            response = requests.post(X_API_URL, json=payload, headers=headers)
            
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            logger.debug(f"Response body: {response.text}")  # Log full response
            
            # Log rate limit info regardless of status
            for header, value in response.headers.items():
                if 'rate' in header.lower():
                    logger.info(f"Rate limit info - {header}: {value}")
            
            if response.status_code == 429:  # True rate limit
                if wait_for_rate_limit(response):
                    retry_count += 1
                    continue
                else:
                    logger.error("❌ True rate limit hit")
                    return {"error": "rate_limit", "response": response.text}
                    
            elif response.status_code == 201:  # Success
                logger.info("✅ Post successful!")
                return response.json()
                
            else:  # Other errors
                error_data = response.json()
                logger.error(f"❌ Post failed with status {response.status_code}")
                logger.error(f"Error details: {error_data}")
                return {"error": "api_error", "response": error_data}
                
        except Exception as e:
            logger.error(f"❌ Error posting: {str(e)}")
            logger.error("Exception details:", exc_info=True)
            break
            
        retry_count += 1
    
    return None

if __name__ == "__main__":
    # Random paper title components
    adjectives = ["Novel", "Advanced", "Innovative", "Comprehensive", "Efficient"]
    topics = ["Machine Learning", "Neural Networks", "Deep Learning", "AI", "Data Science"]
    methods = ["Framework", "Approach", "Methodology", "System", "Architecture"]

    # Random author names
    first_names = ["James", "Maria", "John", "Sarah", "Michael", "Emma", "David", "Lisa"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]

    # Generate random title and authors
    random_title = f"{random.choice(adjectives)} {random.choice(topics)} {random.choice(methods)} [{datetime.now().strftime('%H:%M:%S')}]"
    random_authors = [
        f"{random.choice(first_names)} {random.choice(last_names)}", 
        f"{random.choice(first_names)} {random.choice(last_names)}"
    ]

    logger.info("Starting X post test")
    try:
        response = post_paper(
            paper_title=random_title,
            authors=random_authors,
            url="https://huggingface.co/papers/test",
            pdf_url="https://arxiv.org/pdf/2401.00935",  # Test PDF URL
            arxiv_url="https://arxiv.org/abs/test",
            github_url="https://github.com/test/repo"
        )
        
        if response and 'data' in response:
            logger.info("✅ Post successful!")
            logger.info(f"Tweet ID: {response['data']['id']}")
            logger.info(f"Tweet text: {response['data']['text']}")
        else:
            logger.error("❌ Post failed!")
            logger.error(f"Response: {response}")
            
    except Exception as e:
        logger.error("❌ Error during posting:")
        logger.error(f"Error details: {str(e)}", exc_info=True)
