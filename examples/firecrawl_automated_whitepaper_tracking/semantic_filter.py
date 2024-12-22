__doc__ = """Module for semantic filtering of research papers using OpenAI's API via OpenRouter."""

import os
import json
import openai
import logging
from datetime import datetime
from functools import wraps
from json import JSONDecodeError
from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure OpenAI API key directly
openai.api_key = os.getenv('OPENAI_API_KEY')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s',
    handlers=[
        logging.FileHandler(f'semantic_filter_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Log OpenAI version after logger is configured
logger.info(f"Using OpenAI version: {openai.__version__}")

# Update the client initialization
client = openai.OpenAI()

def log_function_call(func):
    """Decorator to log entry and exit of functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"Entering {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.info(f"Exiting {func.__name__} successfully")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            raise
    return wrapper

class CategoryMatch(BaseModel):
    """
    Pydantic model for paper category classification results.
    We validate the structured output from the model here, ensuring
    it has a boolean 'belongs_to_category' and a float 'confidence'.
    """
    belongs_to_category: bool
    confidence: float

@log_function_call
def belongs_to_category(paper_title: str, paper_abstract: str, desired_category: str) -> bool:
    """
    Determine if a paper belongs to a specific category using
    an OpenAI model that supports structured outputs.
    """
    logger.info(f"Analyzing paper: '{paper_title}' for category '{desired_category}'")
    
    # Define the function schema following the function-calling format
    functions = [
        {
            "name": "classify_paper",
            "description": "Classify if a given paper belongs to a specified category.",
            "parameters": {
                "type": "object",
                "properties": {
                    "belongs_to_category": {
                        "type": "boolean",
                        "description": "True if the paper belongs to the category; otherwise false."
                    },
                    "confidence": {
                        "type": "number",
                        "description": "Confidence level between 0 and 1."
                    }
                },
                "required": ["belongs_to_category", "confidence"]
            }
        }
    ]

    # Updated API call format for OpenAI SDK v1.0.0+
    try:
        response = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a research paper classifier. You must respond by calling the function "
                        "`classify_paper` with JSON that has two keys: belongs_to_category (bool) and "
                        "confidence (float). Do not output anything except valid JSON for those arguments."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Does this paper belong to the category '{desired_category}'?\n\n"
                        f"Title: {paper_title}\n\n"
                        f"Abstract: {paper_abstract}"
                    )
                }
            ],
            functions=functions,
            function_call={"name": "classify_paper"}  # Force the function call
        )
    except Exception as e:
        logger.error(f"Error during ChatCompletion request: {e}")
        return False

    # Update the response parsing
    try:
        message = response.choices[0].message
        if message.function_call:  # Updated attribute access
            function_call = message.function_call
            arguments_json = function_call.arguments
            parsed_args = json.loads(arguments_json)
            
            classification = CategoryMatch(**parsed_args)
            logger.info(
                f"Classification result: belongs={classification.belongs_to_category}, "
                f"confidence={classification.confidence}"
            )
            return classification.belongs_to_category and classification.confidence > 0.8

        logger.warning("No function_call found in the response.")
        return False

    except (JSONDecodeError, ValidationError) as e:
        logger.error(f"Error parsing or validating classification result: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting semantic filter test")

    # Test the classifier
    TEST_TITLE = "Building Reliable LLM Agents: A Study in Reinforcement Learning"
    TEST_ABSTRACT = (
        "This paper explores methods for creating more reliable AI agents using LLMs and RL..."
    )
    CATEGORY = "LLM Agents"
    result = belongs_to_category(TEST_TITLE, TEST_ABSTRACT, CATEGORY)
    logger.info(f"Test result for category '{CATEGORY}': {result}")

# TODO: implement the Instructor library for structured outputs to enhance
#  the flexibility of model switching
# TODO: add examples to system prompt of abstract that are known to be 
# in the category (agents)
