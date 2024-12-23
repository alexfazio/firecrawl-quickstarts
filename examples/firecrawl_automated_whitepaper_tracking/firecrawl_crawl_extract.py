__doc__ = """Module for crawling and extracting data from Hugging Face papers using Firecrawl.
Module for crawling and extracting data from Hugging Face papers using Firecrawl.
Handles paper metadata extraction and processing for the notification system.
"""

import asyncio
import os
import re
from datetime import datetime
from typing import Dict, Any

# Third-party imports
import pytz
import requests
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel
from firecrawl import FirecrawlApp
from dotenv import load_dotenv
from supabase_db import Database
from examples.firecrawl_automated_whitepaper_tracking.discord_notifications import send_paper_notification, should_notify
from logging_config import setup_crawler_logging

# Initialize logger
logger = setup_crawler_logging()

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
    logger.info("Starting URL extraction from: %s", target_url)
    exclude_url_pattern = (
        r"^https://huggingface\.co/papers\?date="
        r"\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])$"
    )
    def get_all_source_urls(json_data: Dict[str, Any]) -> list:
        extracted_urls = []
        logger.debug("Processing JSON data with %d entries", len(json_data.get('data', [])))
        if "data" in json_data:
            for entry in json_data["data"]:
                if "metadata" in entry and "sourceURL" in entry["metadata"]:
                    url = entry["metadata"]["sourceURL"]
                    if not re.match(exclude_url_pattern, url):
                        extracted_urls.append(url)
        if "next" in json_data and json_data["next"]:
            logger.debug("Found next page: %s", json_data['next'])
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
    logger.info("Crawling URL with params: %s", params)
    crawl_result = app.crawl_url(target_url, params=params)
    urls = get_all_source_urls(crawl_result)
    logger.info("Extracted %d paper URLs", len(urls))
    return urls

async def extract_paper_details(url: str) -> dict:
    """Extract paper details from a given URL using FirecrawlApp.
    
    This async function handles the extraction of metadata from individual paper pages.
    It uses the FirecrawlApp to scrape structured data according to the ExtractSchema.
    The synchronous FirecrawlApp calls are run in a separate thread using asyncio.to_thread.
    
    Args:
        url (str): The URL of the paper to extract details from.
        
    Returns:
        dict: Extracted paper details including title, upvotes, comments, and URLs.
    """
    logger.info("Extracting paper details from: %s", url)
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

    # Run the synchronous scrape_url method in a separate thread
    data = await asyncio.to_thread(
        app.scrape_url,
        url,
        {
            'formats': ['extract'],
            'extract': {
                'schema': ExtractSchema.model_json_schema(),
            }
        }
    )
    logger.debug("Raw extraction data: %s", data['extract'])
    return data['extract']

async def process_paper_batch(urls: list[str], db: Database, batch_size: int = 5):
    """Process papers in batches to avoid overwhelming resources"""
    for i in range(0, len(urls), batch_size):
        batch = urls[i:i + batch_size]
        tasks = []
        for url in batch:
            tasks.append(extract_paper_details(url))
        
        # Process batch of papers
        details_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle results synchronously
        for url, details in zip(batch, details_list):
            if isinstance(details, Exception):
                logger.error(f"Error processing {url}: {details}")
                continue
                
            try:
                # Synchronous database operations
                details["url"] = url
                is_new_paper = db.add_paper(details)
                
                if should_notify(details, is_new_paper):
                    await send_paper_notification(
                        paper_title=details["paper_title"],
                        authors=details["authors"].split(", "),
                        abstract=details["abstract_body"],
                        upvotes=details["number_of_upvotes"],
                        comments=details["number_of_comments"],
                        url=url,
                        pdf_url=details["view_pdf_url"],
                        arxiv_url=details["view_arxiv_page_url"],
                        github_url=details["github_repo_url"]
                    )
            except Exception as e:
                logger.error(f"Error processing details for {url}: {e}")

def get_todays_papers_url() -> str:
    """
    Returns today's HuggingFace papers URL using San Francisco timezone.
    
    Returns:
        str: URL for today's papers webpage in format https://huggingface.co/papers?date=YYYY-MM-DD
    """
    sf_tz = pytz.timezone('America/Los_Angeles')
    today = datetime.now(sf_tz).strftime('%Y-%m-%d')
    return f"https://huggingface.co/papers?date={today}"

# TODO: create a streamlit ui to set environment variables and desired categories for the semantic filter
# TODO: make the extract_paper_details function async so details are extracted in parallel
# TODO: make all functions async to avoid redudant code
# TODO: for each url extracted by the crawler it should be verified if it exists already in 
# the database before passing it to the extract_paper_details function
# TODO: update the extract_paper_details function to process new papers only if the number of
# found papers for the specific date is greater than the number of papers already found for that date
# within the database. so this will need a new specific database table to store the number of papers
# found for each date.
# TODO: implement an improve error handling system for the extract_paper_details function which will
# add papers that failed to be processed to the database but include a column to indicate that the
# paper was not processed successfully, so that a retry can be performed when cron jobs are re-run.
# this will require changing the database structure and schema, as well as some of the existing logic
# that verifies if a paper should be processed or not.
