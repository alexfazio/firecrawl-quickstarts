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

5. Configure environment variables:
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
   1. Go to Supabase Project Settings > Database
   2. Copy the connection string under "URI"
   3. Add to `.env`:
      ```
      POSTGRES_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres?sslmode=require
      ```
   4. Replace `[YOUR-PASSWORD]` with your database password
   5. Replace `[YOUR-PROJECT-REF]` with your project reference
   6. URL-encode any special characters in the password:
      - `#` becomes `%23`
      - `@` stays as `@`
      - `$` becomes `%24`
      - `^` becomes `%5E`
      - `&` becomes `%26`

   d. OpenAI API Key:
   1. Sign up at [OpenAI](https://platform.openai.com)
   2. Go to API Keys section
   3. Create a new API key
   4. Add to `.env`:
      ```
      OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
      ```

6. Configure paper category filtering:
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

TODO: Update the GitHub Actions workflow to trigger based on actual changes to the 
Hugging Face Daily Papers page instead of using a scheduled cron job. This can be accomplished by:
1. Creating a GitHub Action that checks for changes to the page content/hash
2. Only triggering the main paper tracking workflow when changes are detected
3. This will ensure:
   - More timely updates as papers are published
   - More efficient use of API credits by avoiding unnecessary checks
   - Reduced latency between paper publication and notification