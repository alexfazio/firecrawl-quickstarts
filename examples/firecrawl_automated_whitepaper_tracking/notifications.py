__doc__ = """Module for sending notifications about new research papers to Discord."""

import os
import asyncio
import aiohttp
from dotenv import load_dotenv
from semantic_filter import belongs_to_category

load_dotenv()

# Categories of interest for notifications
CATEGORIES_OF_INTEREST = [
    "LLM Agents",
    "AI Safety",
    "Reinforcement Learning"
    # Add more categories as needed
]

def should_notify(paper_details: dict, is_new_paper: bool) -> bool:
    """
    Determine if a notification should be sent for this paper.
    
    Args:
        paper_details (dict): Dictionary containing paper details
        is_new_paper (bool): Whether this is a new paper or an update
        
    Returns:
        bool: True if notification should be sent, False otherwise
    """
    # First check if this is a new paper
    if not is_new_paper:
        return False
        
    # Then check if it belongs to any category of interest
    for category in CATEGORIES_OF_INTEREST:
        if belongs_to_category(
            paper_details["paper_title"],
            paper_details["abstract_body"],
            category
        ):
            return True
    
    return False

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
    
    # Create links section
    links = []
    if pdf_url:
        links.append(f"[📄 PDF]({pdf_url})")
    if arxiv_url:
        links.append(f"[📝 arXiv]({arxiv_url})")
    if github_url:
        links.append(f"[💻 GitHub]({github_url})")
    
    message = {
        "embeds": [
            {
                "title": "📚 New Paper Published!",
                "description": f"**{paper_title}**\n\n"
                f"**Authors:** {', '.join(authors)}\n\n"
                f"**Abstract:**\n{abstract[:500]}{'...' if len(abstract) > 500 else ''}\n\n"
                f"**Stats:** 👍 {upvotes} | 💬 {comments}\n\n"
                f"**Links:**\n{' • '.join(links)}\n\n"
                f"[View on HuggingFace]({url})",
                "color": 5814783,  # HF's purple color
            }
        ]
    }

    try:
        async with aiohttp.ClientSession() as session:
            await session.post(os.getenv("DISCORD_WEBHOOK_URL"), json=message)
    except Exception as e:
        print(f"Error sending Discord notification: {e}")


if __name__ == "__main__":
    # Test notification
    asyncio.run(
        send_paper_notification(
            paper_title="Test Paper Title",
            authors=["Author 1", "Author 2"],
            abstract="This is a test abstract for the paper notification system.",
            upvotes=10,
            comments=5,
            url="https://huggingface.co/papers/test",
            pdf_url="https://example.com/pdf",
            arxiv_url="https://arxiv.org/abs/test",
            github_url="https://github.com/test/repo"
        )
    )

# TODO: implement discord button for feedback about relevancy of notifications
