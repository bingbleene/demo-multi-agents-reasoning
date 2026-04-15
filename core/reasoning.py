"""
Multi-step reasoning logic orchestration.
"""

import sys
import time
import logging
from concurrent.futures import ThreadPoolExecutor
from colorama import Fore, Style
from config.config import MAX_REFINEMENT_ATTEMPTS
from utils.utils import get_local_context_for_prompt
from visualization.metrics import metrics_tracker
from .blend import blend_responses
from utils.console import print_header, print_divider, process_agent_action, handle_special_commands
from .session import save_reasoning_session


def reasoning_logic(agents):
    """Handles the multi-step reasoning workflow."""
    while True:
        print(Fore.YELLOW + "Enter your prompt (or 'menu'/'exit'): " + Style.RESET_ALL, end='')
        user_prompt = input().strip()

        if user_prompt.lower() == 'menu':
            print(Fore.YELLOW + "Returning to main menu." + Style.RESET_ALL)
            break
        if user_prompt.lower() == 'exit':
            print(Fore.YELLOW + "Goodbye!" + Style.RESET_ALL)
            sys.exit(0)

        if handle_special_commands(user_prompt, agents):
            continue

        if len(user_prompt) <= 4:
            print(Fore.YELLOW + "Prompt must be > 4 characters." + Style.RESET_ALL)
            continue

        local_context = get_local_context_for_prompt(user_prompt, max_records=3)
        extended_prompt = f"{user_prompt}\n\n{local_context}" if local_context else user_prompt

        # Step 1: Discuss
        print_header("Step 1: Discussing")
        opinions = {}
        durations = {}
        start_discuss = time.time()
        
        for agent in agents:
            opinion, duration = process_agent_action(agent, 'discuss', extended_prompt)
            opinions[agent.name] = opinion
            durations[agent.name] = duration
        
        discuss_duration = time.time() - start_discuss
        metrics_tracker.record_step_time("Discuss", discuss_duration)

        # Step 2: Verify
        print_header("Step 2: Verifying")
        verified_opinions = {}
        start_verify = time.time()

        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(process_agent_action, agent, 'verify', opinions[agent.name]): agent 
                      for agent in agents}
            for future in futures:
                agent = futures[future]
                verified_opinion, _ = future.result()
                verified_opinions[agent.name] = verified_opinion

        verify_duration = time.time() - start_verify
        metrics_tracker.record_step_time("Verify", verify_duration)

        # Step 3: Critique
        print_header("Step 3: Critiquing")
        critiques = {}
        start_critique = time.time()
        
        num_agents = len(agents)
        for i, agent in enumerate(agents):
            other_agent = agents[(i + 1) % num_agents]
            critique, _ = process_agent_action(agent, 'critique', verified_opinions[other_agent.name])
            critiques[agent.name] = critique

        critique_duration = time.time() - start_critique
        metrics_tracker.record_step_time("Critique", critique_duration)

        # Step 4: Refine
        print_header("Step 4: Refining")
        refined_opinions = {}
        start_refine = time.time()
        
        for agent in agents:
            refined_opinion, _ = process_agent_action(agent, 'refine', opinions[agent.name])
            refined_opinions[agent.name] = refined_opinion

        refine_duration = time.time() - start_refine
        metrics_tracker.record_step_time("Refine", refine_duration)

        # Step 5: Blend
        print_header("Step 5: Blending")
        agent_responses = [(agent.name, refined_opinions[agent.name]) for agent in agents]
        start_blend = time.time()
        optimal_response = blend_responses(agent_responses, user_prompt)
        blend_duration = time.time() - start_blend
        metrics_tracker.record_step_time("Blend", blend_duration)

        print_divider()
        print_header("Optimal Response")
        print(Fore.GREEN + optimal_response + Style.RESET_ALL)
        print_divider()

        # Visualize Response Summary
        print(Fore.YELLOW + "\nGenerating response visualizations..." + Style.RESET_ALL)
        metrics_tracker.visualize_response_summary(user_prompt, optimal_response, refined_opinions)

        # Feedback Loop
        refine_count = 0
        user_feedback = None
        while refine_count < MAX_REFINEMENT_ATTEMPTS:
            print(Fore.YELLOW + "\nWas this helpful? (yes/no/menu/exit): " + Style.RESET_ALL, end='')
            user_feedback = input().strip().lower()

            if user_feedback == 'menu':
                save_reasoning_session(user_prompt, optimal_response, user_feedback)
                return
            if user_feedback == 'exit':
                save_reasoning_session(user_prompt, optimal_response, user_feedback)
                sys.exit(0)
            if user_feedback == 'yes':
                print(Fore.YELLOW + "Thank you!" + Style.RESET_ALL)
                break
            elif user_feedback != 'no':
                print(Fore.YELLOW + "Please answer yes/no." + Style.RESET_ALL)
                continue

            refine_count += 1
            if refine_count >= 2:
                print(Fore.YELLOW + "Take more time refining? (yes/no): " + Style.RESET_ALL, end='')
                more_time = input().strip().lower() == 'yes'
            else:
                more_time = False

            print(Fore.YELLOW + "Refining response..." + Style.RESET_ALL)

            for agent in agents:
                refined_opinion, _ = process_agent_action(agent, 'refine', refined_opinions[agent.name],
                                                          more_time=more_time)
                refined_opinions[agent.name] = refined_opinion

            # Re-blend
            print_divider()
            print_header("Blending Refined Responses")
            agent_responses = [(agent.name, refined_opinions[agent.name]) for agent in agents]
            optimal_response = blend_responses(agent_responses, user_prompt)

            print_divider()
            print_header("New Optimal Response")
            print(Fore.GREEN + optimal_response + Style.RESET_ALL)
            print_divider()

        if not user_feedback:
            user_feedback = "no"

        print(Fore.YELLOW + "Retain context? (yes/no): " + Style.RESET_ALL, end='')
        if input().strip().lower() != 'yes':
            for agent in agents:
                agent.messages.clear()
            print(Fore.YELLOW + "Context cleared." + Style.RESET_ALL)

        save_reasoning_session(user_prompt, optimal_response, user_feedback)
