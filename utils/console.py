"""
Console utilities for colored output and formatting.
"""

import sys
import logging
from colorama import Fore, Style


def print_divider(char="═", length=100, color=Fore.YELLOW):
    """Prints a divider line."""
    print(color + (char * length) + Style.RESET_ALL)


def print_header(title, color=Fore.YELLOW):
    """Prints a formatted header."""
    border = "═" * 58
    print(color + f"╔{border}╗")
    print(color + f"║{title.center(58)}║")
    print(color + f"╚{border}╝" + Style.RESET_ALL)


def process_agent_action(agent, action, *args, **kwargs):
    """Processes an action for a given agent."""
    action_method = getattr(agent, action, None)
    if not action_method:
        logging.error(f"Action '{action}' not found.")
        return "Invalid action.", 0

    action_description = agent.ACTION_DESCRIPTIONS.get(action, "performing action")

    print_divider()
    print(Fore.YELLOW + f"{agent.color}{agent.name} is {action_description}..." + Style.RESET_ALL)

    try:
        result, duration = action_method(*args, **kwargs)
        if result:
            print(agent.color + f"\n=== {agent.name} {action.capitalize()} Output ===" + Style.RESET_ALL)
            print(agent.color + result[:500] + ('...' if len(result) > 500 else '') + Style.RESET_ALL)
        print(agent.color + f"{agent.name} completed in {duration:.2f}s." + Style.RESET_ALL)
        return result, duration
    except Exception as e:
        logging.error(f"Error during {action}: {e}")
        return "An error occurred.", 0


def handle_special_commands(user_input, agents):
    """Handles special user commands."""
    cmd = user_input.strip().lower()
    if cmd == 'exit':
        print(Fore.YELLOW + "Goodbye!" + Style.RESET_ALL)
        sys.exit(0)
    elif cmd == 'history':
        print(Fore.YELLOW + "\nConversation History:" + Style.RESET_ALL)
        for agent in agents:
            print(agent.color + f"\n{agent.name}:" + Style.RESET_ALL)
            for msg in agent.messages[:3]:  # Show only last 3
                print(f"{msg['role'].upper()}: {msg['content'][:100]}...")
        return True
    elif cmd == 'clear':
        for agent in agents:
            agent.messages.clear()
            agent.chat_history.clear()
        print(Fore.YELLOW + "History cleared." + Style.RESET_ALL)
        return True
    return False
