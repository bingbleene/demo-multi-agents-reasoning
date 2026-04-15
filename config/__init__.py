"""Configuration package for Multi-Agent Reasoning system."""

from .config import (
    MAX_TOTAL_TOKENS,
    MAX_REFINEMENT_ATTEMPTS,
    MAX_CHAT_HISTORY_TOKENS,
    RETRY_LIMIT,
    RETRY_BACKOFF_FACTOR,
    AGENTS_CONFIG_FILE,
    REASONING_HISTORY_FILE,
)
from .openai_client import client, initialize_client
from .agent_config import load_agents_config, get_shared_system_message
from .logging_config import setup_logging, ColoredFormatter

__all__ = [
    "MAX_TOTAL_TOKENS",
    "MAX_REFINEMENT_ATTEMPTS",
    "MAX_CHAT_HISTORY_TOKENS",
    "RETRY_LIMIT",
    "RETRY_BACKOFF_FACTOR",
    "AGENTS_CONFIG_FILE",
    "REASONING_HISTORY_FILE",
    "client",
    "initialize_client",
    "load_agents_config",
    "get_shared_system_message",
    "setup_logging",
    "ColoredFormatter",
]
