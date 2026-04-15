"""
Configuration settings for Multi-Agent Reasoning system.
All settings can be overridden via environment variables or .env file.
"""

import os

# Load configuration from .env file
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")
MAX_TOTAL_TOKENS = int(os.environ.get("MAX_TOTAL_TOKENS", 4096))
MAX_REFINEMENT_ATTEMPTS = int(os.environ.get("MAX_REFINEMENT_ATTEMPTS", 3))
MAX_CHAT_HISTORY_TOKENS = int(os.environ.get("MAX_CHAT_HISTORY_TOKENS", 4096))
RETRY_LIMIT = int(os.environ.get("RETRY_LIMIT", 3))
RETRY_BACKOFF_FACTOR = int(os.environ.get("RETRY_BACKOFF_FACTOR", 2))
AGENTS_CONFIG_FILE = os.environ.get("AGENTS_CONFIG_FILE", "agents.json")
REASONING_HISTORY_FILE = os.environ.get("REASONING_HISTORY_FILE", "reasoning_history.json")
