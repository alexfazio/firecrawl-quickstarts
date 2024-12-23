__doc__ = """Module for semantic filtering of research papers using OpenAI's API."""

import os
import json

from json import JSONDecodeError
from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv

import openai
from logging_config import setup_semantic_filter_logging, log_function_call

# Load environment variables
load_dotenv()

# Configure OpenAI API key
openai.api_key = os.getenv('OPENAI_API_KEY')

# Configure logging using centralized configuration
logger = setup_semantic_filter_logging()
logger.info("Using OpenAI version: %s", openai.__version__)

client = openai.OpenAI()

class CategoryMatch(BaseModel):
    """
    Pydantic model for paper category classification results.
    We validate the structured output from the model here, ensuring
    it has a boolean 'belongs_to_category' and a float 'confidence'.
    """
    belongs_to_category: bool
    confidence: float

@log_function_call
def belongs_to_category(paper_title: str, paper_abstract: str, desired_category: str) -> tuple[bool, float]:
    """
    Determine if a paper belongs to a specific category using
    an OpenAI model that supports structured JSON outputs.
    
    Returns:
        tuple: (belongs_to_category: bool, confidence: float)
    """
    logger.info("Analyzing paper: '%s' for category '%s'", paper_title, desired_category)

    system_instructions = (
        "You are a research paper classifier. "
        "Given: a desired_category, a paper_title, and a paper_abstract, "
        "determine if the paper belongs to the desired_category. "
        "Output only valid JSON with the exact format: "
        "{ \"belongs_to_category\": boolean, \"confidence\": float }. "
        "Where 'belongs_to_category' is True if the paper belongs to the specified desired_category, "
        "otherwise False, and 'confidence' is a float between 0 and 1. No additional keys or text."
    )

    user_prompt = (
        f"desired_category: {desired_category}\n"
        f"paper_title: {paper_title}\n"
        f"paper_abstract: {paper_abstract}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_instructions},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7
        )
        # Add detailed response logging
        logger.debug("Full API response: %s", response)
        
        message_content = response.choices[0].message.content.strip()
        logger.debug("Raw message content: %s", message_content)
        
        if not message_content:
            logger.error("Empty response from model")
            return False, 0.0
            
        parsed_args = json.loads(message_content)

        classification = CategoryMatch(**parsed_args)
        logger.info(
            "Classification result: belongs=%s, confidence=%s",
            classification.belongs_to_category,
            classification.confidence
        )
        belongs = classification.belongs_to_category and classification.confidence > 0.8
        return belongs, classification.confidence

    except (JSONDecodeError, ValidationError) as e:
        logger.error("Error parsing or validating classification result: %s", e)
        return False, 0.0

if __name__ == "__main__":
    logger.info("Starting semantic filter test")

    # Test the classifier
    TEST_TITLE = "Building Reliable LLM Agents: A Study in Reinforcement Learning"
    TEST_ABSTRACT = (
        "This paper explores methods for creating more reliable AI agents using LLMs and RL..."
    )
    CATEGORY = "LLM Agents"
    result = belongs_to_category(TEST_TITLE, TEST_ABSTRACT, CATEGORY)
    logger.info("Test result for category '%s': %s", CATEGORY, result)

# TODO: implement the Instructor library for structured outputs to enhance
#  the flexibility of model switching
# TODO: add examples to system prompt of abstract that are known to be 
# in the category (agents)
# TODO: store paper category relevance evaluations and confidence scores in the database 
# to develop more accurate relevance response evaluations in the future 
# using the OpenAI Evals platform.
# TODO: implement error handling for OpenAI API credit exhaustion and send admin-only
# notifications to Discord using discord_notifications.py's webhook. Research needed:
# Discord webhook might not support role-based visibility (@admin mentions) directly - 
# may need to create a separate admin-only channel or explore Discord bot implementation
