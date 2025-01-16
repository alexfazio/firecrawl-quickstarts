"""Module for posting research papers to X (Twitter)."""

import os
import base64
import hashlib
import secrets
import webbrowser
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from dotenv import load_dotenv, set_key, find_dotenv
import requests
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('x_oauth_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

AUTH_URL = "https://twitter.com/i/oauth2/authorize"
TOKEN_URL = "https://api.twitter.com/2/oauth2/token"
CALLBACK_URL = "http://127.0.0.1:8000/callback"
X_API_URL = "https://api.twitter.com/2/tweets"

def generate_pkce_pair():
    """Generate PKCE code verifier and challenge"""
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).rstrip(b'=').decode()
    
    logger.debug(f"Generated PKCE - Verifier length: {len(code_verifier)}, Challenge length: {len(code_challenge)}")
    return code_verifier, code_challenge

class CallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback"""
    code = None
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info(f"CallbackHandler: {format%args}")
    
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
        
def load_stored_tokens():
    """Load stored OAuth tokens from .env"""
    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)
    
    # Check if we have both required tokens
    access_token = os.getenv('X_ACCESS_TOKEN')
    refresh_token = os.getenv('X_REFRESH_TOKEN')
    
    if access_token and refresh_token:
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': os.getenv('X_TOKEN_EXPIRES_IN'),
            'scope': os.getenv('X_TOKEN_SCOPE')
        }
    return None

def save_tokens(tokens):
    """Save OAuth tokens to .env"""
    dotenv_path = find_dotenv()
    
    # Update each token in .env
    set_key(dotenv_path, 'X_ACCESS_TOKEN', tokens['access_token'])
    set_key(dotenv_path, 'X_REFRESH_TOKEN', tokens['refresh_token'])
    set_key(dotenv_path, 'X_TOKEN_EXPIRES_IN', str(tokens['expires_in']))
    set_key(dotenv_path, 'X_TOKEN_SCOPE', tokens['scope'])
    
    # Reload environment
    load_dotenv(dotenv_path)

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

def post_paper(
    paper_title: str,
    authors: list,
    url: str,
    pdf_url: Optional[str] = None,
    arxiv_url: Optional[str] = None,
    github_url: Optional[str] = None
):
    """Post paper to X"""
    logger.info(f"Attempting to post paper: {paper_title}")
    
    # Get OAuth 2.0 token
    try:
        token = get_oauth2_token()
        logger.info("Successfully obtained OAuth token")
    except Exception as e:
        logger.error(f"Failed to get OAuth token: {str(e)}")
        return None
    
    post_text = format_post(
        paper_title, authors, url, 
        pdf_url, arxiv_url, github_url
    )
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    payload = {"text": post_text}
    
    try:
        logger.info("Sending post request to X API")
        response = requests.post(X_API_URL, json=payload, headers=headers)
        
        logger.debug(f"Post response status: {response.status_code}")
        logger.debug(f"Post response headers: {response.headers}")
        
        if response.status_code != 201:
            logger.error(f"Error posting to X: {response.text}")
        else:
            logger.info("Successfully posted to X")
            
        return response.json()
    except Exception as e:
        logger.error(f"Error posting to X: {str(e)}", exc_info=True)
        return None

if __name__ == "__main__":
    logger.info("Starting X post test")
    try:
        response = post_paper(
            paper_title="Test Paper Title",
            authors=["Author 1", "Author 2"],
            url="https://huggingface.co/papers/test",
            pdf_url="https://example.com/test.pdf",
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
