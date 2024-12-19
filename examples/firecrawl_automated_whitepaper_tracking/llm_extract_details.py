import os  # noqa
from firecrawl import FirecrawlApp  # noqa
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

def extract_paper_details(url: str):
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
    data = app.scrape_url(url, {
        'formats': ['extract'],
        'extract': {
            'schema': ExtractSchema.model_json_schema(),
        }
    })
    print(data['extract'])
    return data['extract']

if __name__ == "__main__":
    URL = input("Enter the URL of the paper: ")
    extract_paper_details(URL)
