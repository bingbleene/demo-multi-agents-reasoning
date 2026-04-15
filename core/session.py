"""
Session management and persistence.
"""

import time
from utils.utils import append_reasoning_history


def save_reasoning_session(user_prompt, final_response, user_feedback):
    """Saves session details to history file."""
    record = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "user_prompt": user_prompt,
        "final_response": final_response,
        "user_feedback": user_feedback
    }
    append_reasoning_history(record)
