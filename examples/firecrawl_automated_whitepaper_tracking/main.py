import json
import os
import re
from datetime import datetime
from typing import Dict, Any
import pytz

import requests
from pydantic import BaseModel
from firecrawl import FirecrawlApp
from dotenv import load_dotenv

load_dotenv()

__doc__ = """Module for crawling and extracting paper URLs and content of
such URLs from the main HuggingFace Daily Papers page."""

def extract_paper_urls(target_url: str) -> list:
    """
    Extract all paper source URLs from a given target URL using Firecrawl.
    
    Args:
        target_url (str): The URL to crawl for paper sources
        
    Returns:
        list: A list of extracted source URLs, excluding daily papers URLs
    """
    exclude_url_pattern = (
        r"^https://huggingface\.co/papers\?date="
        r"\d{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])$"
    )
    def get_all_source_urls(json_data: Dict[str, Any]) -> list:
        extracted_urls = []
        if "data" in json_data:
            for entry in json_data["data"]:
                if "metadata" in entry and "sourceURL" in entry["metadata"]:
                    url = entry["metadata"]["sourceURL"]
                    if not re.match(exclude_url_pattern, url):
                        extracted_urls.append(url)
        if "next" in json_data and json_data["next"]:
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
    crawl_result = app.crawl_url(target_url, params=params)
    return get_all_source_urls(crawl_result)

def extract_paper_details(url: str) -> dict:
    """Extract paper details from a given URL using FirecrawlApp.
    
    Args:
        url (str): The URL of the paper to extract details from.
        
    Returns:
        dict: Extracted paper details including title, upvotes, comments, and URLs.
    """
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
    print(data['extract'])
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
    today_papers_url = get_todays_papers_url()
    urls = extract_paper_urls(today_papers_url)
    paper_details_dict = {}  # Create a dictionary instead of a list
    try:
        for url in urls:
            details = extract_paper_details(url)
            paper_details_dict[url] = details
    except Exception as e:
        print(f"Error processing URL {url}: {str(e)}")
    # Write the results to a JSON file
    with open('paper_details.json', 'w', encoding='utf-8') as f:
        json.dump(paper_details_dict, f, indent=4, ensure_ascii=False)