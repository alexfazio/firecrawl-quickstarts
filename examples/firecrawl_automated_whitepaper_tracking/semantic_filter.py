__doc__ = """Module for semantic filtering of research papers using OpenAI's API via OpenRouter."""

import os
from json import JSONDecodeError
from openai import OpenAI, OpenAIError  # noqa
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set the OPENAI_API_KEY environment variable using the value from OPENROUTER_API_KEY
os.environ['OPENAI_API_KEY'] = os.getenv('OPENROUTER_API_KEY')

# Configure OpenAI client with OpenRouter specifics
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENAI_API_KEY"),
    default_headers={
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
        "HTTP-Referer": "https://github.com/yourusername/your-repo",
        "X-Title": "Paper Category Classifier"
    }
)

class CategoryMatch(BaseModel):
    """Pydantic model for paper category classification results."""
    belongs_to_category: bool
    confidence: float

def belongs_to_category(paper_title: str, paper_abstract: str, desired_category: str) -> bool:
    """Determine if a paper belongs to a specific category using semantic analysis."""
    try:
        completion = client.chat.completions.create(
            model="openai/gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "You are a research paper classifier. You must respond with valid JSON "
                        "containing a boolean 'belongs_to_category' and a float 'confidence' "
                        "between 0 and 1."
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
            response_format={
                "type": "json_schema",
                "schema": CategoryMatch.model_json_schema()
            }
        )
        if completion.choices and completion.choices[0].message:
            content = completion.choices[0].message.content
            classification = CategoryMatch.model_validate_json(content)
            return classification.belongs_to_category and classification.confidence > 0.8
        return False
    except (ValueError, JSONDecodeError, OpenAIError) as e:
        print(f"Error in semantic analysis: {e}")
        return False

if __name__ == "__main__":
    # Test the classifier
    TEST_TITLE = "Building Reliable LLM Agents: A Study in Reinforcement Learning"
    TEST_ABSTRACT = (
        "This paper explores methods for creating more reliable AI agents "
        "using LLMs and RL..."
    )
    CATEGORY = "LLM Agents"
    result = belongs_to_category(TEST_TITLE, TEST_ABSTRACT, CATEGORY)
    print(f"Paper belongs to category '{CATEGORY}': {result}")

# TODO: implement the Instructor library for structured outputs to enhance
#  the flexibility of model switching
# TODO: add examples to system prompt of abstract that are known to be 
# in the category (agents)
