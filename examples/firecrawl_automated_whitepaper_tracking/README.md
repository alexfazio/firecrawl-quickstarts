# Automated Price Tracking System

A robust price tracking system that monitors product prices across e-commerce websites and notifies users of price changes through Discord.

## Features

- Automated price checking every 6 hours
- Support for multiple e-commerce platforms through Firecrawl API
- Discord notifications for price changes
- Historical price data storage in PostgreSQL database
- Interactive price history visualization with Streamlit

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