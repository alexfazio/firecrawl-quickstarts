#!/usr/bin/env python3
"""
Entry point module for the Hugging Face White Paper Tracker.
Handles command line arguments and initiates the paper tracking process.
"""

import argparse
import asyncio
import os
from typing import Optional

import requests
from sqlalchemy.exc import SQLAlchemyError

from supabase_db import Database
from firecrawl_crawl_extract import (
    extract_paper_urls,
    process_paper_batch,
    get_todays_papers_url
)
from logging_config import setup_crawler_logging

# Initialize logger
logger = setup_crawler_logging()

def run_paper_tracker(url: Optional[str] = None, date: Optional[str] = None) -> None:
    """
    Main function to run the paper tracking process.
    
    Args:
        url (Optional[str]): Full URL to crawl (e.g., https://huggingface.co/papers?date=2024-12-19)
        date (Optional[str]): Date in YYYY-MM-DD format (e.g., 2024-12-19)
    """
    # Determine which URL to use
    if url:
        papers_url = url
        logger.info("Using provided full URL: %s", papers_url)
    elif date:
        papers_url = f"https://huggingface.co/papers?date={date}"
        logger.info("Using URL for specified date: %s", papers_url)
    else:
        papers_url = get_todays_papers_url()
        logger.info("Using today's papers URL: %s", papers_url)
    
    urls = extract_paper_urls(papers_url)
    logger.info("Found %d papers to process", len(urls))
    
    db = Database(os.getenv("POSTGRES_URL"))
    logger.info("Database connection established")
    
    try:
        asyncio.run(process_paper_batch(urls, db))
    except (SQLAlchemyError, requests.RequestException, ValueError) as e:
        logger.error("Critical error in main process: %s", str(e), exc_info=True)
        raise

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Crawl and extract papers from HuggingFace.')
    parser.add_argument('--url', type=str, 
                       help='Full URL to crawl (e.g., https://huggingface.co/papers?date=2024-12-19)')
    parser.add_argument('--date', type=str, 
                       help='Date in YYYY-MM-DD format (e.g., 2024-12-19)')
    
    args = parser.parse_args()
    run_paper_tracker(url=args.url, date=args.date)

# TODO: Include a Bluesky API call to publish the paper's posts to Bluesky. This will require a new
# llm flow to generate the post content and a new function to send the post to Bluesky.