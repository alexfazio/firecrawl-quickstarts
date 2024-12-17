import os
from typing import Dict, Any
from firecrawl import FirecrawlApp
from dotenv import load_dotenv
import requests

load_dotenv()

def get_all_source_urls(json_data: Dict[str, Any]) -> list:
    """
    Recursively extract all 'sourceURL' values from paginated JSON data returned by crawl_papers().
    """
    source_urls = []
    
    if "data" in json_data:
        for entry in json_data["data"]:
            if "metadata" in entry and "sourceURL" in entry["metadata"]:
                source_urls.append(entry["metadata"]["sourceURL"])
    
    if "next" in json_data and json_data["next"]:
        next_page_url = json_data["next"]
        response = requests.get(next_page_url)
        if response.ok:
            next_json_data = response.json()
            source_urls.extend(get_all_source_urls(next_json_data))
    
    return source_urls

def crawl_papers(api_key: str, URL: str) -> list:
    """
    Crawl papers from a given URL using Firecrawl's crawl_url() method and return all source URLs
    """
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
    crawl_result = app.crawl_url(URL, params=params)
    return get_all_source_urls(crawl_result)

if __name__ == "__main__":
    api_key = os.getenv("FIRECRAWL_API_KEY")
    URL = 'https://huggingface.co/papers'
    source_urls = crawl_papers(api_key, URL)
    print("Extracted sourceURLs:", source_urls)
