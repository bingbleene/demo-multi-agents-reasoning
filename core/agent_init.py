"""
Agent initialization from configuration.
"""

from colorama import Fore, Style
from .agent import Agent
from config.agent_config import load_agents_config


def initialize_agents():
    """Initializes agents from configuration."""
    agents_data = load_agents_config()
    agents = []
    agent_data_dict = {}

    if not agents_data:
        print(Fore.YELLOW + "No agents found. Using defaults." + Style.RESET_ALL)
        agent_a_data = {
            'name': 'Agent 47',
            'system_purpose': 'You are logical and analytical.',
            'personality': {'logical': 'Yes', 'analytical': 'Yes'},
        }
        agent_b_data = {
            'name': 'Agent 74',
            'system_purpose': 'You are creative and empathetic.',
            'personality': {'creative': 'Yes', 'empathetic': 'Yes'},
        }
        agent_a = Agent(Fore.MAGENTA, **agent_a_data)
        agent_b = Agent(Fore.CYAN, **agent_b_data)
        agents = [agent_a, agent_b]
    else:
        print(Fore.YELLOW + "Available agents:" + Style.RESET_ALL)
        agent_colors = {
            "Agent 47": Fore.MAGENTA,
            "Agent 74": Fore.CYAN,
        }
        for agent_data in agents_data[:2]:  # Load only first 2 agents
            name = agent_data.get('name', 'Unnamed Agent')
            if name == 'Swarm Agent':  # Skip Swarm Agent
                continue
            color = agent_colors.get(name, Fore.WHITE)
            print(color + f"- {name}" + Style.RESET_ALL)

            agent = Agent(color, **agent_data)
            agents.append(agent)
            agent_data_dict[name] = agent_data

        # Inform agents about other agents
        for agent in agents:
            other_agents_info = ""
            for other_agent in agents:
                if other_agent.name != agent.name:
                    info = f"Name: {other_agent.name}"
                    other_agent_data = agent_data_dict.get(other_agent.name, {})
                    system_purpose = other_agent_data.get('system_purpose', '')
                    info += f"\nSystem Purpose: {system_purpose}"
                    other_agents_info += f"\n\n{info}"
            agent.instructions += f"\n\nYou are aware of:\n{other_agents_info.strip()}"

    return agents
