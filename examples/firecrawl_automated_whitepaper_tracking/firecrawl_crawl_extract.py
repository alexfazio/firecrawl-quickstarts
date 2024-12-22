__doc__ = """Module for crawling and extracting data from Hugging Face papers using Firecrawl.
Module for crawling and extracting data from Hugging Face papers using Firecrawl.
Handles paper metadata extraction and processing for the notification system.
"""

import asyncio
import os
import re
from datetime import datetime
from typing import Dict, Any

import pytz
import requests
from pydantic import BaseModel
from firecrawl import FirecrawlApp
from dotenv import load_dotenv
from database import Database
from notifications import send_paper_notification, should_notify
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
def setup_logging():
    """Configure logging with both file and console handlers."""
    logger = logging.getLogger('firecrawl_crawler')
    logger.setLevel(logging.INFO)
    
    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and configure file handler (rotating log files, max 5MB each, keep 5 backup files)
    file_handler = RotatingFileHandler(
        'crawler.log', maxBytes=5*1024*1024, backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    # Create and configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Initialize logger
logger = setup_logging()

# Load environment variables
load_dotenv()

# Validate required environment variables
if not os.getenv("POSTGRES_URL"):
    raise ValueError("POSTGRES_URL environment variable not set")
if not os.getenv("FIRECRAWL_API_KEY"):
    raise ValueError("FIRECRAWL_API_KEY environment variable not set")

def extract_paper_urls(target_url: str) -> list:
    """
    Extract all paper source URLs from a given target URL using Firecrawl.
    
    Args:
        target_url (str): The URL to crawl for paper sources
        
    Returns:
        list: A list of extracted source URLs, excluding daily papers URLs
    """
    logger.info(f"Starting URL extraction from: {target_url}")
    exclude_url_pattern = (
        r"^https://huggingface\.co/papers\?date="
        r"\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])$"
    )
    def get_all_source_urls(json_data: Dict[str, Any]) -> list:
        extracted_urls = []
        logger.debug(f"Processing JSON data with {len(json_data.get('data', []))} entries")
        if "data" in json_data:
            for entry in json_data["data"]:
                if "metadata" in entry and "sourceURL" in entry["metadata"]:
                    url = entry["metadata"]["sourceURL"]
                    if not re.match(exclude_url_pattern, url):
                        extracted_urls.append(url)
        if "next" in json_data and json_data["next"]:
            logger.debug(f"Found next page: {json_data['next']}")
            next_page_url = json_data["next"]
            response = requests.get(next_page_url)  # noqa
            if response.ok:
                next_json_data = response.json()
                extracted_urls.extend(get_all_source_urls(next_json_data))
        return extracted_urls

    load_dotenv()
    api_key = os.getenv("FIRECRAWL_API_KEY")
    app = FirecrawlApp(api_key=api_key)
    params = {
        'limit': 30,
        'excludePaths': ['papers$'],
        'includePaths': ['papers/*'],
        'ignoreSitemap': True,
        'scrapeOptions': {
            'formats': ['markdown', 'links', 'html'],
            'onlyMainContent': False,
            'includeTags': ['a']
        }
    }
    logger.info(f"Crawling URL with params: {params}")
    crawl_result = app.crawl_url(target_url, params=params)
    urls = get_all_source_urls(crawl_result)
    logger.info(f"Extracted {len(urls)} paper URLs")
    return urls

def extract_paper_details(url: str) -> dict:
    """Extract paper details from a given URL using FirecrawlApp.
    
    Args:
        url (str): The URL of the paper to extract details from.
        
    Returns:
        dict: Extracted paper details including title, upvotes, comments, and URLs.
    """
    logger.info(f"Extracting paper details from: {url}")
    # Initialize the FirecrawlApp with your API key
    app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

    class ExtractSchema(BaseModel):  # noqa
        """Schema for extracting paper details from Hugging Face papers."""
        paper_title: str
        number_of_upvotes: int
        number_of_comments: int
        view_pdf_url: str
        view_arxiv_page_url: str
        authors: str
        abstract_body: str
        # Publication date represents when the paper was originally published (e.g., on arXiv)
        utc_publication_date_day: int
        utc_publication_date_month: int
        utc_publication_date_year: int
        # Submission date represents when the paper was submitted/added to
        # HuggingFace's daily papers page
        utc_submission_date_day: int
        utc_submission_date_month: int
        utc_submission_date_year: int
        github_repo_url: str
    data = app.scrape_url(url, {
        'formats': ['extract'],
        'extract': {
            'schema': ExtractSchema.model_json_schema(),
        }
    })
    logger.debug(f"Raw extraction data: {data['extract']}")
    return data['extract']

def get_todays_papers_url() -> str:
    """
    Returns today's HuggingFace papers URL using San Francisco timezone.
    
    Returns:
        str: URL for today's papers webpage in format https://huggingface.co/papers?date=YYYY-MM-DD
    """
    sf_tz = pytz.timezone('America/Los_Angeles')
    today = datetime.now(sf_tz).strftime('%Y-%m-%d')
    return f"https://huggingface.co/papers?date={today}"

if __name__ == "__main__":
    import sys
    import argparse
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Crawl and extract papers from HuggingFace.')
    parser.add_argument('--url', type=str, help='Full URL to crawl (e.g., https://huggingface.co/papers?date=2024-12-19)')
    parser.add_argument('--date', type=str, help='Date in YYYY-MM-DD format (e.g., 2024-12-19)')
    
    args = parser.parse_args()
    
    # Determine which URL to use
    if args.url:
        papers_url = args.url
        logger.info(f"Using provided full URL: {papers_url}")
    elif args.date:
        papers_url = f"https://huggingface.co/papers?date={args.date}"
        logger.info(f"Using URL for specified date: {papers_url}")
    else:
        papers_url = get_todays_papers_url()
        logger.info(f"Using today's papers URL: {papers_url}")
    
    urls = extract_paper_urls(papers_url)
    logger.info(f"Found {len(urls)} papers to process")
    
    db = Database(os.getenv("POSTGRES_URL"))
    logger.info("Database connection established")
    
    try:
        for i, url in enumerate(urls, 1):
            logger.info(f"Processing paper {i}/{len(urls)}: {url}")
            try:
                details = extract_paper_details(url)
                details["url"] = url
                is_new_paper = db.add_paper(details)
                logger.info(
                    f"Paper processed: '{details['paper_title']}' "
                    f"({'new' if is_new_paper else 'existing'} paper)"
                )
                
                if should_notify(details, is_new_paper):
                    logger.info(f"Sending notification for paper: {details['paper_title']}")
                    asyncio.run(send_paper_notification(
                        paper_title=details["paper_title"],
                        authors=details["authors"].split(", "),
                        abstract=details["abstract_body"],
                        upvotes=details["number_of_upvotes"],
                        comments=details["number_of_comments"],
                        url=url,
                        pdf_url=details["view_pdf_url"],
                        arxiv_url=details["view_arxiv_page_url"],
                        github_url=details["github_repo_url"]
                    ))
                    
            except Exception as e:
                logger.error(f"Error processing paper at {url}: {str(e)}", exc_info=True)
                continue
                
    except Exception as e:
        logger.error(f"Critical error in main process: {str(e)}", exc_info=True)

# TODO: create a streamlit ui to set environment variables and desired categories for the semantic filter
# TODO: make the extract_paper_details function async so details are extracted in parallel
# TODO: make all functions async to avoid redudant code
s