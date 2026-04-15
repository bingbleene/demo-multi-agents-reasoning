"""
Agent class definition for multi-agent reasoning.
"""

import time
import logging
import tiktoken
from colorama import Style
from config.openai_client import client
from config.config import OPENAI_MODEL, MAX_TOTAL_TOKENS, MAX_CHAT_HISTORY_TOKENS, RETRY_LIMIT, RETRY_BACKOFF_FACTOR
from config.agent_config import get_shared_system_message
from visualization.metrics import metrics_tracker


class Agent:
    """Represents an AI assistant agent with specific capabilities."""
    
    ACTION_DESCRIPTIONS = {
        'discuss':  "formulating a response",
        'verify':   "verifying data",
        'refine':   "refining the response",
        'critique': "critiquing another agent's response"
    }

    def __init__(self, color, **kwargs):
        self.name = kwargs.get('name', 'AI Assistant')
        self.color = color
        self.messages = []
        self.chat_history = []
        self.system_purpose = kwargs.get('system_purpose', '')

        additional_attributes = {
            k: v for k, v in kwargs.items()
            if k not in ['name', 'system_purpose', 'color']
        }
        self.instructions = self.system_purpose
        for attr_name, attr_value in additional_attributes.items():
            if isinstance(attr_value, dict):
                details = "\n".join(f"{kk.replace('_', ' ').title()}: {vv}" 
                                   for kk, vv in attr_value.items())
                self.instructions += f"\n\n{attr_name.replace('_', ' ').title()}:\n{details}"
            else:
                self.instructions += f"\n\n{attr_name.replace('_', ' ').title()}: {attr_value}"

    def _add_message(self, role, content, mode='reasoning'):
        """Adds a message and manages token limits."""
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logging.error(f"Error getting encoding: {e}")
            raise e

        if mode == 'chat':
            self.chat_history.append({"role": role, "content": content})
            total_tokens = sum(len(encoding.encode(msg['content'])) for msg in self.chat_history)
            while total_tokens > MAX_CHAT_HISTORY_TOKENS and len(self.chat_history) > 1:
                self.chat_history.pop(0)
                total_tokens = sum(len(encoding.encode(msg['content'])) for msg in self.chat_history)
        else:
            self.messages.append({"role": role, "content": content})
            total_tokens = sum(len(encoding.encode(msg['content'])) for msg in self.messages)
            while total_tokens > MAX_TOTAL_TOKENS and len(self.messages) > 1:
                self.messages.pop(0)
                total_tokens = sum(len(encoding.encode(msg['content'])) for msg in self.messages)

    def _handle_reasoning_logic(self, prompt):
        """Handles generating a response from OpenAI API."""
        shared_system = get_shared_system_message()
        system_message = f"{shared_system}\n\n{self.instructions}"

        messages = [{"role": "user", "content": system_message}]
        messages.extend(self.messages)
        messages.append({"role": "user", "content": prompt})

        start_time = time.time()
        retries = 0
        backoff = 1

        while retries < RETRY_LIMIT:
            try:
                response = client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=messages
                )
                end_time = time.time()
                duration = end_time - start_time

                assistant_reply = response.choices[0].message.content.strip()
                self._add_message("assistant", assistant_reply)

                usage = getattr(response, 'usage', None)
                if usage:
                    prompt_tokens = getattr(usage, 'prompt_tokens', 0)
                    completion_tokens = getattr(usage, 'completion_tokens', 0)
                    total_tokens = getattr(usage, 'total_tokens', 0)

                    prompt_tokens_details = getattr(usage, 'prompt_tokens_details', None)
                    cached_tokens = getattr(prompt_tokens_details, 'cached_tokens', 0) if prompt_tokens_details else 0

                    completion_tokens_details = getattr(usage, 'completion_tokens_details', None)
                    reasoning_tokens = getattr(completion_tokens_details, 'reasoning_tokens', 0) if completion_tokens_details else 0

                    # Record metrics
                    metrics_tracker.record_agent_usage(self.name, prompt_tokens, completion_tokens,
                                                      total_tokens, cached_tokens, reasoning_tokens, duration)
                    metrics_tracker.record_response_length(self.name, assistant_reply)

                    return assistant_reply, duration
                else:
                    return assistant_reply, duration
            except Exception as e:
                error_type = type(e).__name__
                logging.error(f"Error in {self.name} reasoning: {error_type}: {e}")
                retries += 1
                if retries >= RETRY_LIMIT:
                    logging.error(f"{self.name} reached retry limit.")
                    break
                backoff_time = backoff * (RETRY_BACKOFF_FACTOR ** (retries - 1))
                logging.info(f"Retrying in {backoff_time} seconds...")
                time.sleep(backoff_time)

        return "An error occurred.", time.time() - start_time

    def discuss(self, prompt):
        """Initiates a discussion."""
        return self._handle_reasoning_logic(prompt)

    def verify(self, data):
        """Verifies data accuracy."""
        verification_prompt = f"Verify the accuracy of:\n\n{data}"
        return self._handle_reasoning_logic(verification_prompt)

    def refine(self, data, more_time=False, iterations=2):
        """Refines the provided data."""
        refinement_prompt = f"Please refine:\n\n{data}"
        if more_time:
            refinement_prompt += "\nTake additional time to improve thoroughly."

        total_duration = 0
        refined_response = data
        for _ in range(iterations):
            refined_response, duration = self._handle_reasoning_logic(refinement_prompt)
            total_duration += duration
            refinement_prompt = f"Please further refine:\n\n{refined_response}"

        return refined_response, total_duration

    def critique(self, other_agent_response):
        """Critiques another agent's response."""
        critique_prompt = f"Critique for accuracy:\n\n{other_agent_response}"
        return self._handle_reasoning_logic(critique_prompt)
