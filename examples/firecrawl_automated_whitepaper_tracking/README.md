# Automated Price Tracking System

A robust price tracking system that monitors product prices across e-commerce websites and notifies users of price changes through Discord.

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
   Then edit .env with your:
   - Discord webhook URL
   - Database credentials
   - Firecrawl API key