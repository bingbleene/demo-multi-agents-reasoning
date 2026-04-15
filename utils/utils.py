"""
Utility functions for reasoning history and context retrieval.
"""

import os
import json
import re
from config.config import REASONING_HISTORY_FILE


def append_session_record(file_path: str, record: dict):
    """Appends a session record to a JSON file."""
    if not os.path.exists(file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump([], f, indent=2, ensure_ascii=False)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, list):
                data = []
    except (json.JSONDecodeError, FileNotFoundError):
        data = []

    data.append(record)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def append_reasoning_history(record: dict):
    """Appends a reasoning session record."""
    append_session_record(REASONING_HISTORY_FILE, record)


def get_local_context_for_prompt(user_prompt, max_records=3):
    """Fetches local memory from reasoning_history.json."""
    keywords = re.findall(r"\w+", user_prompt)
    contexts = []
    
    try:
        with open(REASONING_HISTORY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, list):
                return ""
    except (json.JSONDecodeError, FileNotFoundError):
        return ""

    data.reverse()
    count = 0
    for entry in data:
        if count >= max_records:
            break
        combined_text = (entry.get("user_prompt", "") + " " +
                        entry.get("final_response", "")).lower()
        if any(kw.lower() in combined_text for kw in keywords):
            summary = (f"Timestamp: {entry.get('timestamp')}\n"
                      f"User Prompt: {entry.get('user_prompt')}\n"
                      f"Final Response: {entry.get('final_response')}")
            contexts.append(summary)
            count += 1

    if not contexts:
        return ""

    combined = "\n\n--- Retrieved Local Context ---\n\n"
    combined += "\n\n".join(contexts)
    return combined
