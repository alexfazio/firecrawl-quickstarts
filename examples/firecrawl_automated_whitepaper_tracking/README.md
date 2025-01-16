<a href="https://x.com/alxfazio" target="_blank">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./images/hf-daily-papers-github-logo.png">
    <img alt="Firecrawl Quickstarts Logo" src="./images/hf-daily-papers-github-logo.png" width="400px" style="max-width: 100%; margin-bottom: 20px;">
  </picture>
</a>

# Hugging Face "Daily Papers" Tracker

This system provides **automated notifications** about the latest white papers published on the [Hugging Face Daily Papers](https://huggingface.co/papers) page. Using **Firecrawl's semantic crawling and scraping capabilities** (Crawl and Extract APIs), it fetches and processes new publications daily. The system uses semantic filtering to determine which papers are most relevant to the user's interests, based on a user-defined category prompt, and delivers notifications directly to Discord.

### Key Features
- **Daily Notifications**: Receive real-time updates about the latest papers that match your research interests.
- **Firecrawl Integration**:
  - **Crawl API**: Retrieves the list of newly published papers from the Hugging Face Daily Papers page.
  - **Extract API**: Extracts structured and semantically enriched data from each paper for filtering and analysis.
- **Semantic Filtering**: Matches papers to the user's category of interest using a customizable category prompt.
- **Customizable Interests**: Easily define your research area by editing the `category_prompt` file.
- **Default Configuration**: Preconfigured to track papers related to AI Agents, but can be adapted for any topic.

### How It Works
1. **Crawl**: The system uses the Firecrawl Crawl API to retrieve today's list of papers from the Hugging Face Daily Papers page.
2. **Extract**: It processes and extracts structured semantic data from each paper using the Firecrawl Extract API.
3. **Store**: All extracted paper data is stored in a **Supabase database** for future reference and analysis.
4. **Filter**: Semantic filtering identifies papers relevant to the category defined in `category_prompt`.
5. **Notify**: Sends summaries of the filtered papers directly to a Discord channel.

### System Architecture
```mermaid
flowchart TB
    subgraph entry ["Entry Points"]
        CLI["CLI Arguments\n--url or --date"]
        GHA["GitHub Actions\nScheduled/Manual Trigger"]
    end

    subgraph hf_white_paper_tracker ["hf_white_paper_tracker.py"]
        A[Initialize Logger] --> B[Initialize Database]
        B --> C[Verify DB Connection/Version]
        C --> D{"URL Source?"}
        D -->|CLI Args| E1["Use Provided URL"]
        D -->|No Args| E2["Get Today's URL"]
        E1 --> F[Run Paper Tracker]
        E2 --> F
    end

    subgraph firecrawl_crawl_extract ["firecrawl_crawl_extract.py"]
        G[Extract Paper URLs] --> H[Process Paper Batch]
        H --> I[Extract Paper Details]
    end

    subgraph semantic_filter ["semantic_filter.py"]
        J[Load Category Definition] --> K[Classify Paper]
        K --> L{Meets Criteria?}
    end

    subgraph discord_notifications ["discord_notifications.py"]
        M[Format Message] --> N[Send to Discord]
    end

    subgraph supabase_db ["supabase_db.py"]
        O[Store Paper Data] --> P[Update Status]
    end

    %% Module connections
    CLI -->|Optional| hf_white_paper_tracker
    GHA -->|Scheduled| hf_white_paper_tracker
    F -->|Calls| G
    I -->|Passes paper data| J
    L -->|Yes| M
    L -->|No| O
    N -->|Update notification status| P

    %% Environment dependencies
    env[".env File"] -.->|Config| hf_white_paper_tracker
    category[category_prompt.py] -.->|Definition| semantic_filter

    classDef module fill:#f9f,stroke:#333,stroke-width:2px;
    class hf_white_paper_tracker,firecrawl_crawl_extract,semantic_filter,discord_notifications,supabase_db module;
    classDef entry fill:#aaf,stroke:#333,stroke-width:2px;
    class CLI,GHA entry;
```

### Setup
1. Configure your Firecrawl API keys.
2. Modify the `category_prompt` to specify your topic of interest.
3. Set up a Discord webhook for receiving notifications.
4. Run the system to start tracking and getting updates.

## Setup

1. Clone the repository

2. Install Poetry (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. Install dependencies:
   ```bash
   poetry install
   ```

4. Ensure PostgreSQL is installed:
   - PostgreSQL must be installed and pg_config must be in your PATH.
   - On macOS (using Homebrew):
     ```bash
     brew install postgresql
     ```
   - Verify pg_config:
     ```bash
     pg_config --version
     ```

5. Set up Supabase Database:
   1. Create a Supabase account at [Supabase](https://supabase.com)
   2. Create a new project
   3. Go to Project Settings > Database
   4. Note down:
      - Database password (set during project creation)
      - Connection string/URI
      - Project reference ID
   5. Enable the PostgREST API:
      - Go to Project Settings > API
      - Ensure PostgREST is enabled
   6. Configure database tables:
      - The application will automatically create the required tables:
        - `papers`: Stores paper information and tracking status
        - `schema_version`: Manages database migrations
   7. Important connection string notes:
      - For local development, use port 5432:
        ```
        POSTGRES_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres?sslmode=require
        ```
      - For GitHub Actions, use port 6543:
        ```
        POSTGRES_URL=postgresql://postgres.[YOUR-PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require
        ```
      - Remember to URL-encode special characters in your password:
        - `#` → `%23`
        - `$` → `%24`
        - `^` → `%5E`
        - `&` → `%26`
        - `@` stays as `@`

6. Set up Discord Notifications:
   1. Create a Discord server (skip if you already have one)
   2. Create a channel for paper notifications
   3. Configure the webhook:
      - Go to Server Settings > Integrations
      - Click on "Create Webhook" (or edit an existing one)
      - Set a name for your webhook (e.g., "Paper Tracker")
      - Select the channel where notifications should be sent
      - Copy the Webhook URL
   4. Important webhook URL format:
      ```
      https://discord.com/api/webhooks/{webhook.id}/{webhook.token}
      ```
   5. The notifications will include:
      - Paper title
      - Authors
      - Abstract (first 500 characters)
      - Engagement stats (upvotes and comments)
      - Links to:
        - PDF version
        - arXiv page
        - GitHub repository (if available)
        - Original HuggingFace post
   6. Security notes:
      - Keep your webhook URL private
      - The webhook URL contains a secret token
      - If compromised, you can regenerate the webhook token in Discord
      - Add the URL to your `.env` file:
        ```
        DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN
        ```

7. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` with:

   a. Discord Webhook URL:
   1. Go to your Discord server
   2. Edit a channel > Integrations > Create Webhook
   3. Copy the Webhook URL
   4. Add to `.env`:
      ```
      DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN
      ```

   b. Firecrawl API Key:
   1. Sign up at [Firecrawl](https://firecrawl.co)
   2. Go to API Keys section
   3. Create a new API key
   4. Add to `.env`:
      ```
      FIRECRAWL_API_KEY=fc-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
      ```

   c. Supabase Database URL:
   1. Use the connection string from your Supabase setup (Step 5)
   2. Add to `.env`:
      ```
      POSTGRES_URL=<your-connection-string>
      ```

   d. OpenAI API Key:
   1. Sign up at [OpenAI](https://platform.openai.com)
   2. Go to API Keys section
   3. Create a new API key
   4. Add to `.env`:
      ```
      OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
      ```

8. Configure paper category filtering:
   ```bash
   cp category_prompt.example.py category_prompt.py
   ```
   Then edit `category_prompt.py` to define your `DESIRED_CATEGORY`. This string defines what papers are considered relevant and will trigger notifications. 
   
   The default configuration is set up for "AI Agents" papers, but you can modify it for your needs.

   The semantic filter uses this definition to determine:
   - Which papers trigger Discord notifications
   - Classification confidence threshold (default: 0.8)
   - Categorization criteria for the LLM-based filter

Your final `.env` file should look like:
```
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/1234567890/abcdef...
FIRECRAWL_API_KEY=fc-f6ff27d623e548f390bdc0b9debefe59
POSTGRES_URL=postgresql://postgres:mypassword123@db.abcdefghijklm.supabase.co:5432/postgres?sslmode=require
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

TODO: Create a `.env.example` file with placeholder values after testing is complete, to serve as a template for new users.
TODO: Add to readme how to use the main function firecrawl_crawl_extract.py with arguments to set
the date for the papers to extract.

## Database Schema

The application uses a PostgreSQL database with the following schema:

### Papers Table

| Column                  | Type      | Description                                           |
|------------------------|-----------|-------------------------------------------------------|
| url                    | String    | Primary key - unique paper URL                        |
| title                  | String    | Paper title                                           |
| authors                | String[]  | Array of author names                                 |
| abstract               | Text      | Paper abstract                                        |
| pdf_url                | String    | URL to PDF version                                    |
| arxiv_url              | String    | URL to arXiv page                                     |
| github_url             | String    | URL to GitHub repository                              |
| publication_date       | DateTime  | Original publication date                             |
| submission_date        | DateTime  | Date added to HuggingFace                            |
| upvotes                | Integer   | Current number of upvotes (default: 0)                |
| comments               | Integer   | Current number of comments (default: 0)               |
| last_updated          | DateTime  | Last time the record was updated                      |
| notification_sent     | Boolean   | Whether notification was sent (default: false)        |
| extraction_success    | Boolean   | Whether extraction succeeded (default: true)          |
| extraction_error      | Text      | Error message if extraction failed (nullable)         |
| last_extraction_attempt| DateTime  | When the last extraction was attempted               |

### Schema Version Table

| Column     | Type      | Description                          |
|-----------|-----------|--------------------------------------|
| version   | Integer   | Schema version number                 |
| applied_at| Timestamp | When this version was applied        |

## Deployment Options

### Local Deployment
Follow the setup instructions above for running the tracker locally.

### GitHub Actions Deployment (Recommended)
This project includes GitHub Actions workflow configuration for automated paper tracking. The workflow:
- Runs every 12 hours automatically
- Can be triggered manually via workflow_dispatch
- Sends notifications on both success and failure

To set up with GitHub Actions:

1. Fork/clone this repository to your GitHub account

2. Set up GitHub Secrets:
   Go to your repository's Settings > Secrets and Variables > Actions and add the following secrets:

   ```
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN
   FIRECRAWL_API_KEY=fc-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   POSTGRES_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres?sslmode=require
   OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

   Note: Make sure your Supabase database URL uses port 6543 for GitHub Actions compatibility.

3. Configure your tracking preferences:
   - Fork the repository
   - Edit `category_prompt.py` to define your paper interests
   - Commit the changes to your repository

4. Enable GitHub Actions:
   - Go to your repository's Actions tab
   - Enable workflows if they're not already enabled
   - The `Paper Tracker` workflow will now run automatically every 12 hours

5. Monitor the workflow:
   - Check the Actions tab for run history and logs
   - Failed runs will send notifications to your configured Discord channel
   - Successful runs will send notifications only for relevant papers

The workflow is defined in `.github/workflows/paper-tracker.yml` and includes:
- Python 3.10 setup
- Poetry dependency management
- Database connection testing
- Automatic error notifications via Discord

You can also trigger the workflow manually from the Actions tab using the "Run workflow" button.

## TODOs

[ ] Update the GitHub Actions workflow to trigger based on actual changes to the 
   Hugging Face Daily Papers page instead of using a scheduled cron job. This can be accomplished by:
   1. Creating a GitHub Action that checks for changes to the page content/hash
   2. Only triggering the main paper tracking workflow when changes are detected
   3. This will ensure:
      - More timely updates as papers are published
      - More efficient use of API credits by avoiding unnecessary checks
      - Reduced latency between paper publication and notification
[ ] Implement Hugging Face Daily Papers API to reduce API costs in calling scraping, and crawling models.
   - API: https://huggingface.co/api/daily_papers
   - Docs: https://huggingface.co/docs/hub/en/api#paper-pages-api

### X (Twitter) API Setup

The system uses X's OAuth 2.0 for posting updates. This requires a one-time local authorization:

1. Configure X API credentials in `.env`:
   ```
   X_OAUTH2_CLIENT_ID=your_client_id
   X_OAUTH2_CLIENT_SECRET=your_client_secret
   ```

2. Run the script locally ONCE to authorize:
   ```bash
   python x_post.py
   ```
   This will:
   - Open a browser window
   - Prompt for X account authorization
   - Store OAuth tokens in your `.env` file:
     ```
     X_ACCESS_TOKEN=...
     X_REFRESH_TOKEN=...
     X_TOKEN_EXPIRES_IN=...
     X_TOKEN_SCOPE=...
     ```

3. After authorization:
   - The tokens are stored in `.env`
   - Copy the updated `.env` to your server
   - Subsequent runs will use stored tokens
   - No browser interaction needed
   - Works in automated environments

Note: Keep your `.env` file secure and never commit it to version control.