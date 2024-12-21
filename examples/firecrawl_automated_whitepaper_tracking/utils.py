__doc__ = """Module for utility functions."""

from urllib.parse import urlparse
import re


def is_valid_url(url: str) -> bool:
    """Validate if the given string is a properly formatted HTTP(S) URL.

    Args:
        url (str): The URL to validate

    Returns:
        bool: True if URL is valid, False otherwise
    """
    try:
        # Parse the URL
        result = urlparse(url)

        # Check if scheme and netloc are present
        if not all([result.scheme, result.netloc]):
            return False

        # Check if scheme is http or https
        if result.scheme not in ["http", "https"]:
            return False

        # Basic regex pattern for domain validation
        domain_pattern = (
            r"^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$"
        )
        if not re.match(domain_pattern, result.netloc):
            return False

        return True

    except ValueError:
        return False
