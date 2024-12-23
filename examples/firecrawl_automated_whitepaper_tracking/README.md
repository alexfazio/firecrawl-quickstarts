# Hugging Face Daily Paper Notification Agent

An alert system that tracks Hugging Face Daily Papers for new publications and informs users via Discord notification webhooks.

## Features

- Automatically notifies about Hugging Face Daily Papers releases.
- Scans for new papers every 6 hours.
- Currently supports [Hugging Face Papers](https://huggingface.co/papers) only.
- Delivers paper notifications via Discord.
- Stores historical white paper data in a PostgreSQL database.
- Provides an interactive visualization of paper history with Streamlit.

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

   d. OpenRouter API Key:
   1. Sign up at [OpenRouter](https://openrouter.ai)
   2. Go to your dashboard
   3. Create a new API key
   4. Add to `.env`:
      ```
      OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
      ```

Your final `.env` file should look like:
```
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/1234567890/abcdef...
FIRECRAWL_API_KEY=fc-f6ff27d623e548f390bdc0b9debefe59
POSTGRES_URL=postgresql://postgres:mypassword123@db.abcdefghijklm.supabase.co:5432/postgres?sslmode=require
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

TODO: Create a `.env.example` file with placeholder values after testing is complete, to serve as a template for new users.
TODO: Add to readme how to use the main function firecrawl_crawl_extract.py with arguments to set
the date for the papers to extract.