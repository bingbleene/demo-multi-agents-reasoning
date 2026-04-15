"""
OpenAI API client configuration.
"""

import os
import sys
import logging
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

def initialize_client():
    """Initialize and return OpenAI client."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logging.error("OpenAI API key not found. Set OPENAI_API_KEY in .env or environment.")
        sys.exit(1)
    
    return OpenAI(api_key=api_key)

# Initialize client
client = initialize_client()
