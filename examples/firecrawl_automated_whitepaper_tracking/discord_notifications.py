"""Module for sending notifications about new research papers to Discord."""

import os
import asyncio
import aiohttp
from dotenv import load_dotenv
from logging_config import setup_base_logging, log_function_call

# Configure logging using the centralized configuration
logger = setup_base_logging(
    logger_name="discord_notifier",
    log_file="discord_notifications.log",
    format_string='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s'
)

load_dotenv()

@log_function_call
async def send_paper_notification(
    paper_title: str,
    authors: list,
    abstract: str,
    upvotes: int,
    comments: int,
    url: str,
    pdf_url: str = None,
    arxiv_url: str = None,
    github_url: str = None
):
    """Send a new paper notification to Discord"""
    logger.info(f"Preparing notification for paper: {paper_title}")
    
    # Create links section
    links = []
    if pdf_url:
        links.append(f"[📄 PDF]({pdf_url})")
        logger.debug("Added PDF link to notification")
    if arxiv_url:
        links.append(f"[📝 arXiv]({arxiv_url})")
        logger.debug("Added arXiv link to notification")
    if github_url:
        links.append(f"[💻 GitHub]({github_url})")
        logger.debug("Added GitHub link to notification")
    
    # Truncate abstract if needed
    truncated_abstract = abstract[:500] + ('...' if len(abstract) > 500 else '')
    logger.debug(f"Abstract truncated from {len(abstract)} to {len(truncated_abstract)} chars")
    
    message = {
        "embeds": [
            {
                "title": "📚 New Paper Published!",
                "description": f"**{paper_title}**\n\n"
                f"**Authors:** {', '.join(authors)}\n\n"
                f"**Abstract:**\n{truncated_abstract}\n\n"
                f"**Stats:** ⬆️ {upvotes} | 💬 {comments}\n\n"
                f"**Links:**\n{' • '.join(links)}\n\n"
                f"[View on HuggingFace]({url})",
                "color": 5814783,  # HF's purple color
            }
        ]
    }

    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        logger.error("Discord webhook URL not found in environment variables")
        return

    try:
        logger.info("Sending notification to Discord webhook")
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=message) as response:
                if response.status == 204:  # Discord returns 204 on success
                    logger.info("Successfully sent Discord notification")
                else:
                    response_text = await response.text()
                    logger.error(f"Discord API returned status {response.status}: {response_text}")
                    
    except aiohttp.ClientError as e:
        logger.error(f"Network error sending Discord notification: {str(e)}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error sending Discord notification: {str(e)}", exc_info=True)

if __name__ == "__main__":
    logger.info("Starting Discord notification test")
    try:
        # Test notification
        asyncio.run(
            send_paper_notification(
                paper_title="Test Paper Title",
                authors=["Author 1", "Author 2"],
                abstract="This is a test abstract for the paper notification system.",
                upvotes=10,
                comments=5,
                url="https://huggingface.co/papers/test",
                pdf_url="https://example.com/test.pdf",
                arxiv_url="https://arxiv.org/abs/test",
                github_url="https://github.com/test/repo"
            )
        )
        logger.info("Test notification completed")
    except Exception as e:
        logger.error("Test notification failed:", exc_info=True)

# TODO: implement discord button for feedback about relevancy of notifications, 
# this must be fed back into the database for subsequent refinement of prompts

# TODO: implement admin-only error notifications in Discord - errors should only be 
# visible to channel administrators to avoid cluttering the main feed
