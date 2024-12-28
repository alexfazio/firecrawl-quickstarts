# Building an Automated White Paper Tracking Tool

There's a fascinating psychological effect in keeping track of the ever-expanding world of AI research. Every day, new white papers, preprints, and breakthroughs appear, and it's all too easy to miss something groundbreaking simply because it got buried under a deluge of new publications. This leads to a constant sense of FOMO (Fear of Missing Out) for those of us working on or curious about AI research.

Luckily, automation can help. In this guide, we'll build a Python application that tracks newly published white papers from the [Hugging Face Daily Papers page](https://huggingface.co/papers), filters them semantically to match your unique research interests, and instantly notifies you about the most relevant papers right in your favorite Discord server. Here is a sneak peek of the app:

![Screenshot](https://www.firecrawl.dev/images/blog/whitepapers/sneak-peek.png)

The system has a simple appearance but provides robust functionality under the hood:

* A minimalistic approach to retrieving new white papers  
* Simple controls for editing your categories of interest (via the `category_prompt.py`)  
* A semantic filtering system to match papers that align with your research domain  
* A notifications pipeline that sends Discord alerts whenever relevant new papers appear  
* An automated scheduling system that checks for fresh content daily (or at any interval you specify)  
* All hosted for free as long as you remain within the free tiers of the services used

Let's get started building this automated white paper tracking tool.

---

## The Toolstack We Will Use

We'll be building the tracker with Python and these libraries:

* [Firecrawl](https://firecrawl.dev/) for AI-based crawling and scraping of new white papers  
* [SQLAlchemy](https://www.sqlalchemy.org/) for database management  
* [Supabase](https://supabase.com/) for hosting a free Postgres database instance  
* Discord for notifications  
* GitHub for storing our code  
* GitHub Actions for running scheduled jobs  

We'll also make use of environment variable management and best practices such as storing secrets in `.env` files and GitHub Repository Secrets.

---

## Building an Automated White Paper Tracking Tool Step-by-step

Just like any multi-component project, we'll follow a top-down approach, introducing each tool as it becomes relevant in our workflow. This method helps keep the process coherent so you can see how it all fits together, rather than focusing on each piece in isolation.

### Step 1: Setting up the environment

First, let's create a dedicated folder for our project and switch into it. Then, we'll initialize a virtual environment:

```bash
mkdir huggingface-paper-tracker
cd huggingface-paper-tracker
python -m venv .venv
source .venv/bin/activate
```

These commands:
1. Make a new directory named huggingface-paper-tracker
2. Move into it
3. Create a Python virtual environment called .venv
4. Activate that environment so that installed libraries stay isolated from the rest of your system

Next, we'll initialize a Git repository and create a basic .gitignore:

```bash
git init
touch .gitignore
echo ".venv" >> .gitignore
git commit -m "Initial commit"
```

Finally, since we'll be using Poetry in this project for dependency management (as recommended in the original documentation), let's install it. If Poetry is not installed:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Now, let's create a pyproject.toml or simply run:

```bash
poetry init
```

and follow the prompts. This will configure our project for Poetry.

### Step 2: Defining the main script for white paper tracking

Let's create a file called hf_white_paper_tracker.py. This script will be responsible for orchestrating the daily process:

```bash
touch hf_white_paper_tracker.py
```

Open it up and paste the following skeleton code:

```python
# hf_white_paper_tracker.py

import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main(url=None):
    """
    This function orchestrates the daily paper tracking process.
    If a URL is provided, it fetches from that URL;
    otherwise, it fetches from the Hugging Face Daily Papers default.
    """

    try:
        # Step 1: Check DB connection, environment variables, etc.
        logger.info("Initializing resources...")

        # Step 2: Determine paper source
        if url:
            target_url = url
            logger.info(f"Using provided URL: {target_url}")
        else:
            # In a real scenario, we might generate today's URL or fallback
            target_url = "https://huggingface.co/papers"
            logger.info("Using default Hugging Face Daily Papers URL")

        # Step 3: Run the daily paper fetching and filtering
        logger.info("Running daily paper tracker...")

        # More code in future steps

    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
```

We have:
1. A main function that sets up the environment and determines which URL to crawl
2. A basic logging setup to keep track of events and errors
3. A place to add subsequent functionality (filtering, scraping, notification logic)

Commit this to Git:

```bash
git add .
git commit -m "Add main script for white paper tracking"
```

### Step 3: Adding Firecrawl-based crawling and scraping

We want to:
* Crawl the Hugging Face Daily Papers page for newly published white papers
* Extract structured information from each publication
* Make sure this extraction logic is robust and flexible in case the webpage structure changes

Firecrawl's AI-based approach is perfect for these tasks. Let's install the Python client:

```bash
poetry add firecrawl-py
```

Now, we'll create a file called firecrawl_crawl_extract.py to encapsulate the scraping logic:

```bash
touch firecrawl_crawl_extract.py
```

Inside, add:

```python
# firecrawl_crawl_extract.py

from firecrawl import FirecrawlApp
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = FirecrawlApp()  # Firecrawl automatically reads FIRECRAWL_API_KEY from the environment

def get_daily_paper_urls():
    """
    This function retrieves today's list of paper URLs
    from the Hugging Face Daily Papers page.
    """
    # We can do something like:
    # Use Firecrawl's crawl endpoint or advanced scraping
    # For simplicity, let's pretend we just want to fetch the main page's links
    # and filter them. The real logic can be more advanced:
    response = app.scrape_url(
        "https://huggingface.co/papers",
        params={
            "formats": ["extract"],
            "extract": {
                "schema": {
                    "paper_links": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "description": "URLs for newly published AI white papers"
                        }
                    }
                }
            }
        },
    )
    raw_links = response["extract"]["paper_links"]
    return raw_links

def extract_paper_details(paper_url):
    """
    This function uses Firecrawl to extract semantic info for each paper.
    """
    extraction_data = app.scrape_url(
        paper_url,
        params={
            "formats": ["extract"],
            "extract": {
                "schema": {
                    "title": {"type": "string"},
                    "authors": {"type": "array", "items": {"type": "string"}},
                    "abstract": {"type": "string"},
                    "pdf_url": {"type": "string"},
                    "arxiv_url": {"type": "string"},
                    "github_url": {"type": "string"},
                    "publication_date": {"type": "string"},
                }
            }
        },
    )

    # We'll also record the time we extracted the data
    extraction_data["extract"]["submission_date"] = datetime.utcnow().isoformat()
    return extraction_data["extract"]
```

In this snippet:
* get_daily_paper_urls fetches a list of paper URLs from the main Hugging Face Daily Papers page
* extract_paper_details fetches the structured data (title, authors, abstract, etc.) from each paper's detail page

Add your Firecrawl API key to your .env file:

```bash
echo "FIRECRAWL_API_KEY=fc-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" >> .env
```

Make sure .env is in .gitignore to avoid exposing your key:

```bash
git add .
git commit -m "Implement Firecrawl-based crawling and extraction"
```

### Step 4: Adding Supabase Postgres integration for storing paper data

We need a way to store the papers, so we can avoid re-notifying ourselves for the same ones repeatedly and keep track of updates (such as how many upvotes or comments a paper has).
1. Create an account on Supabase and set up a free Postgres database
2. Retrieve your POSTGRES_URL from the "Project Settings" → "Database" section

Let's install SQLAlchemy for database operations:

```bash
poetry add sqlalchemy psycopg2-binary
```

Create a new file supabase_db.py:

```bash
touch supabase_db.py
```

Paste:

```python
# supabase_db.py

from sqlalchemy import create_engine, Column, String, Text, Integer, Boolean, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()
Base = declarative_base()

class Paper(Base):
    __tablename__ = "papers"

    url = Column(String, primary_key=True)
    title = Column(String)
    authors = Column(String)  # Comma-separated for simplicity
    abstract = Column(Text)
    pdf_url = Column(String)
    arxiv_url = Column(String)
    github_url = Column(String)
    publication_date = Column(DateTime)
    submission_date = Column(DateTime)
    upvotes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)
    notification_sent = Column(Boolean, default=False)
    extraction_success = Column(Boolean, default=True)
    extraction_error = Column(Text, nullable=True)
    last_extraction_attempt = Column(DateTime)

class SchemaVersion(Base):
    __tablename__ = "schema_version"

    version = Column(Integer, primary_key=True)
    applied_at = Column(DateTime)

class SupabaseDB:
    def __init__(self):
        self.engine = create_engine(os.getenv("POSTGRES_URL"))
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)

    def insert_or_update_paper(self, paper_data):
        session = self.Session()
        try:
            existing_paper = session.query(Paper).filter_by(url=paper_data["url"]).first()
            if existing_paper:
                # Update fields
                existing_paper.title = paper_data.get("title")
                existing_paper.authors = ", ".join(paper_data.get("authors", []))
                existing_paper.abstract = paper_data.get("abstract")
                existing_paper.pdf_url = paper_data.get("pdf_url")
                existing_paper.arxiv_url = paper_data.get("arxiv_url")
                existing_paper.github_url = paper_data.get("github_url")
                existing_paper.publication_date = paper_data.get("publication_date")
                existing_paper.submission_date = paper_data.get("submission_date")
                existing_paper.last_updated = datetime.utcnow()
            else:
                new_paper = Paper(
                    url=paper_data["url"],
                    title=paper_data.get("title"),
                    authors=", ".join(paper_data.get("authors", [])),
                    abstract=paper_data.get("abstract"),
                    pdf_url=paper_data.get("pdf_url"),
                    arxiv_url=paper_data.get("arxiv_url"),
                    github_url=paper_data.get("github_url"),
                    publication_date=paper_data.get("publication_date"),
                    submission_date=paper_data.get("submission_date"),
                )
                session.add(new_paper)
            session.commit()
        finally:
            session.close()
```

In summary:
* We use SQLAlchemy to create two tables, papers and schema_version
* The Papers table stores essential metadata about each paper
* The SchemaVersion table is there to handle future migrations
* SupabaseDB is a simple class for inserting or updating paper records

In your .env, add:

```bash
echo "POSTGRES_URL=postgresql://postgres:YOUR_PASSWORD@db.YOURPROJECT.supabase.co:5432/postgres?sslmode=require" >> .env
```

Then commit:

```bash
git add .
git commit -m "Set up Supabase Postgres integration with SQLAlchemy"
```

### Step 5: Tracking paper interests via a semantic filter

We only want to be notified about certain papers. Let's create a new script semantic_filter.py:

```bash
touch semantic_filter.py
```

Paste:

```python
# semantic_filter.py

import os
from dotenv import load_dotenv

load_dotenv()

# We'll keep it simple by storing user interests in a single file or variable
# In a real scenario, we might use an LLM-based approach with OpenAI or similar
DESIRED_CATEGORY = "AI Agents"  # Default interest

def is_relevant(paper_data):
    """
    A simplified check to see if the paper matches the desired category.
    In practice, we'd do a more advanced LLM-based classification using the paper abstract.
    """
    abstract = paper_data.get("abstract", "").lower()
    return DESIRED_CATEGORY.lower() in abstract
```

This function checks whether the abstract field for the paper contains your target topic of interest (in this case, "AI Agents"). Of course, in real usage, you might call OpenAI or another LLM for more sophisticated classification.

Commit changes:

```bash
git add .
git commit -m "Add a basic semantic filter for categories of interest"
```

### Step 6: Sending Discord notifications

Next, we want to set up Discord notifications for new relevant papers. If you haven't done so already:
1. Create a Discord server or pick an existing server
2. Create a channel (like #research-alerts)
3. Go to "Edit Channel" → "Integrations" → "Create Webhook" → "Copy Webhook URL"
4. In your .env file, add the line:

```bash
echo "DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN" >> .env
```

Create discord_notifications.py:

```bash
touch discord_notifications.py
```

Paste:

```python
# discord_notifications.py

import requests
import os

def notify_discord(paper_data):
    """
    Sends a formatted message to Discord about the newly published paper
    """
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        return  # Webhook not set up

    title = paper_data.get("title", "Untitled Paper")
    authors = paper_data.get("authors", "")
    abstract = paper_data.get("abstract", "")[:500]
    pdf_url = paper_data.get("pdf_url")
    arxiv_url = paper_data.get("arxiv_url")
    github_url = paper_data.get("github_url")
    original_url = paper_data.get("url")

    embed_description = (
        f"**Title**: {title}\n\n"
        f"**Authors**: {authors}\n\n"
        f"**Abstract**: {abstract}\n\n"
        "**Links**:\n"
    )

    if pdf_url:
        embed_description += f"- [PDF]({pdf_url})\n"
    if arxiv_url:
        embed_description += f"- [arXiv]({arxiv_url})\n"
    if github_url:
        embed_description += f"- [GitHub]({github_url})\n"
    if original_url:
        embed_description += f"- [Hugging Face Post]({original_url})\n"

    embed = {
        "title": "New Relevant Paper Published",
        "description": embed_description,
        "color": 16711680  # red color
    }

    data = {"embeds": [embed]}
    try:
        requests.post(webhook_url, json=data)
    except Exception as e:
        print(f"Failed to send Discord notification: {e}")
```

This script uses requests to send a JSON payload to your Discord webhook URL, generating a rich embed that includes a paper's title, authors, abstract, and relevant links.

Install requests:

```bash
poetry add requests
git add .
git commit -m "Implement basic Discord notification functionality"
```

### Step 7: Putting it all together in hf_white_paper_tracker.py

Now that we have all components—scraping, filtering, database integration, and Discord notifications—let's update our main script so it's fully functional.

Open hf_white_paper_tracker.py again:

```python
# hf_white_paper_tracker.py

import os
import logging
from dotenv import load_dotenv
from firecrawl_crawl_extract import get_daily_paper_urls, extract_paper_details
from supabase_db import SupabaseDB
from semantic_filter import is_relevant
from discord_notifications import notify_discord

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main(url=None):
    """
    Orchestrates the daily paper tracking process:
    1. Gets new paper URLs
    2. Extracts paper details
    3. Stores them in Supabase
    4. Performs semantic filtering
    5. Notifies on Discord if relevant
    """
    db = SupabaseDB()

    try:
        if url:
            target_url = url
            logger.info(f"Using provided URL: {target_url}")
        else:
            target_url = "https://huggingface.co/papers"
            logger.info("Using Hugging Face Daily Papers URL")

        # 1. Crawl to get paper links
        logger.info("Fetching newly published papers...")
        new_paper_urls = get_daily_paper_urls()
        logger.info(f"Found {len(new_paper_urls)} potential paper links.")

        for p_url in new_paper_urls:
            logger.info(f"Extracting details for {p_url}")
            details = extract_paper_details(p_url)
            details["url"] = p_url

            # 2. Insert or update the paper record in our database
            db.insert_or_update_paper(details)

            # 3. Check if it's relevant
            if is_relevant(details):
                logger.info(f"Paper {p_url} is relevant to your interest.")
                notify_discord(details)

    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
```

Key points:
* We instantiate our SupabaseDB class to handle DB operations
* For each new paper URL, we extract details, store them, and then run them through our filter
* If is_relevant(details) is True, we call notify_discord to send an alert

```bash
git add .
git commit -m "Complete the daily paper tracker functionality"
```

### Step 8: Adding command-line arguments and a manual override

Suppose we want to let users override the default Hugging Face URL or pass a date. We'll integrate argparse into our main script:

```bash
poetry add argparse
```

Modify hf_white_paper_tracker.py:

```python
import argparse
...

def cli():
    parser = argparse.ArgumentParser(description="Daily white paper tracker")
    parser.add_argument("--url", help="URL to fetch papers from (optional)", default=None)
    args = parser.parse_args()
    return args

def main():
    args = cli()
    run_tracker(args.url)

def run_tracker(url=None):
    db = SupabaseDB()
    ...
    # The rest of the logic is moved into run_tracker()
```

Now you can do:

```bash
python hf_white_paper_tracker.py --url "https://huggingface.co/papers/2024-01-05"
```

to specify a custom date or page URL.

```bash
git add .
git commit -m "Add CLI argument support for URL overrides"
```

### Step 9: Automating daily checks with GitHub Actions

We'll automate the execution with GitHub Actions. Create a .github/workflows directory and a paper-tracker.yml:

```bash
mkdir -p .github/workflows
touch .github/workflows/paper-tracker.yml
```

Paste:

```yaml
name: Paper Tracker

on:
  schedule:
    - cron: "0 12 * * *"  # every day at noon (UTC)
  workflow_dispatch:

jobs:
  run-tracker:
    runs-on: ubuntu-latest
    steps:
      - name: Check out the code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.10"

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install poetry
          poetry install

      - name: Run Paper Tracker
        env:
          FIRECRAWL_API_KEY: ${{ secrets.FIRECRAWL_API_KEY }}
          POSTGRES_URL: ${{ secrets.POSTGRES_URL }}
          DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
          # If you use any LLM API keys:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          poetry run python hf_white_paper_tracker.py
```

Steps explained:
1. schedule → triggers the workflow daily at noon UTC
2. workflow_dispatch → allows manual triggers
3. run-tracker job → sets up Python 3.10, installs dependencies via Poetry, then runs our script
4. We retrieve environment variables from GitHub Secrets

Go to your repository → Settings → Secrets → Actions and add FIRECRAWL_API_KEY, POSTGRES_URL, DISCORD_WEBHOOK_URL, etc.

```bash
git add .
git commit -m "Add GitHub Actions for daily white paper tracking"
git push origin main
```

Visit your GitHub repository's "Actions" tab to see it in action.

### Step 10: Verifying our notifications in Discord

Once the GitHub Action runs, it should gather new papers, filter them, and post relevant entries to Discord. Head to your Discord channel and see if you have a "New Relevant Paper Published" embed.

### Step 11: Testing and refining your semantic filter

By default, we set DESIRED_CATEGORY = "AI Agents". If you want to tailor it, open semantic_filter.py and change the string to reflect your interests. You might be more specific, like:

```python
DESIRED_CATEGORY = "LLM for robotic control"
```

In a more robust version, you could incorporate OpenAI's semantic text classification or another large language model-based approach to assess the abstract. The sky's the limit.

```bash
git add .
git commit -m "Refine the semantic filter to match new interests"
```

## Limitations of the Free Tier Tools

As with any free-tier solution, be mindful of usage:
* GitHub Actions: Free plan has a limited number of CI/CD minutes per month
* Firecrawl: The free plan provides a certain number of scraping requests monthly. Large-scale usage may require a paid tier
* Supabase: Limited DB storage in the free plan
* OpenAI (if you decide to use it): The free trial credit eventually expires, and beyond that, usage is pay-as-you-go

For a modest number of daily scrapes (like a single fetch of ~30–40 new papers daily), these limits shouldn't pose any problems.

## Conclusion and Next Steps

That's it! We've built a fully automated daily paper tracking system using Python, Firecrawl, Supabase, and Discord. It:
1. Retrieves new AI white papers from Hugging Face Daily Papers
2. Extracts structured info about each paper
3. Filters them based on your semantic interests
4. Publishes notifications to Discord if a paper matches your preferences
5. Repeats on a schedule with GitHub Actions

Feel free to adapt this project and make it your own. Here are a few possible enhancements:
* Improve the LLM-based filter: Instead of a simple keyword match, use GPT or another model to produce more accurate classification
* Track engagement stats: For each paper, fetch upvotes or comments if you prefer to filter by popularity
* Provide a UI: Use a library like Streamlit or a lightweight web framework to let non-technical folks change the category of interest or view stored papers without checking the database directly
* Handle concurrency and real-time events: If you need to scale up, consider serverless platforms or containerization with Docker to handle frequent or high-volume checks

This approach is a powerful and robust template for many types of automated content monitoring, not just AI research. The core pattern—crawl → extract → store → filter → notify—remains the same whether you're scraping e-commerce deals or tracking newly published arXiv papers.

Good luck, and happy researching!

## Further Reading
* How to Run Web Scrapers on a Schedule for Free
* Mastering Firecrawl's scrape_url Function
* Advanced AI Agents for Automated Research Discovery

Thanks for reading!