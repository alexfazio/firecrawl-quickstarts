#!/usr/bin/env python3
"""
Entry point module for the Hugging Face White Paper Tracker.
Handles command line arguments and initiates the paper tracking process.
"""

import os
import sys
import argparse
import asyncio
import requests
from typing import Optional
from sqlalchemy.exc import SQLAlchemyError

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

# Now we can import our modules
from examples.firecrawl_automated_whitepaper_tracking.firecrawl_crawl_extract import (
    extract_paper_urls,
    process_paper_batch,
    get_todays_papers_url
)
from examples.firecrawl_automated_whitepaper_tracking.supabase_db import Database
from examples.firecrawl_automated_whitepaper_tracking.logging_config import setup_crawler_logging

# Initialize logger
logger = setup_crawler_logging()

def verify_database_connection(db: Database) -> tuple[bool, str]:
    """Test database connection and return status."""
    logger.debug("Verifying database connection...")
    try:
        db.get_all_papers()
        return True, "Database connection successful"
    except SQLAlchemyError as e:
        logger.error("Database connection failed: %s", str(e))
        return False, f"Database connection failed: {str(e)}"

def verify_database_version(db: Database) -> tuple[bool, str]:
    """Verify database schema version matches required version."""
    logger.debug("Verifying database schema version...")
    try:
        session = db.session_factory()
        db._check_schema_version()
        session.close()
        return True, f"Database schema version verified"
    except RuntimeError as e:
        logger.error("Database version check failed: %s", str(e))
        return False, str(e)

def perform_startup_checks(db: Database) -> None:
    """Perform all startup checks before proceeding."""
    # Database connection check
    connection_ok, connection_msg = verify_database_connection(db)
    logger.info(connection_msg)
    if not connection_ok:
        raise RuntimeError(connection_msg)

    # Database version check
    version_ok, version_msg = verify_database_version(db)
    logger.info(version_msg)
    if not version_ok:
        raise RuntimeError(version_msg)

def run_paper_tracker(url: Optional[str] = None, date: Optional[str] = None) -> None:
    """
    Main function to run the paper tracking process.
    
    Args:
        url (Optional[str]): Full URL to crawl (e.g., https://huggingface.co/papers?date=2024-12-19)
        date (Optional[str]): Date in YYYY-MM-DD format (e.g., 2024-12-19)
    """
    # Initialize database first
    db = Database(os.getenv("POSTGRES_URL"))
    logger.info("Database connection initialized")
    
    # Perform startup checks before proceeding
    perform_startup_checks(db)
    
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
# TODO: test db connection and add check for db versoin matching supabase_db.py before running any modules