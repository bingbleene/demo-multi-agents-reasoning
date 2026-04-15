"""
Metrics tracking and visualization for Multi-Agent Reasoning.
"""

from collections import defaultdict
import matplotlib.pyplot as plt
from colorama import Fore, Style


class MetricsTracker:
    """Tracks metrics for visualization purposes."""
    
    def __init__(self):
        self.agent_metrics = defaultdict(lambda: {
            'tokens_used': 0,
            'cached_tokens': 0,
            'reasoning_tokens': 0,
            'response_lengths': [],
            'durations': [],
            'step_durations': {}
        })
        self.step_times = {}

    def record_agent_usage(self, agent_name, prompt_tokens, completion_tokens, 
                          total_tokens, cached_tokens, reasoning_tokens, duration):
        """Records agent API usage."""
        metrics = self.agent_metrics[agent_name]
        metrics['tokens_used'] += total_tokens
        metrics['cached_tokens'] += cached_tokens
        metrics['reasoning_tokens'] += reasoning_tokens
        metrics['durations'].append(duration)

    def record_response_length(self, agent_name, response_text):
        """Records response text length."""
        self.agent_metrics[agent_name]['response_lengths'].append(len(response_text))

    def record_step_time(self, step_name, duration):
        """Records time for a reasoning step."""
        if step_name not in self.step_times:
            self.step_times[step_name] = []
        self.step_times[step_name].append(duration)

    def visualize_metrics(self):
        """Generate visualization dashboard."""
        if not self.agent_metrics:
            return

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Multi-Agent Reasoning Metrics Dashboard', fontsize=16, fontweight='bold')

        # 1. Total Tokens Used per Agent
        ax1 = axes[0, 0]
        agents = list(self.agent_metrics.keys())
        tokens = [self.agent_metrics[a]['tokens_used'] for a in agents]
        colors_agents = plt.cm.Set3(range(len(agents)))
        bars1 = ax1.bar(agents, tokens, color=colors_agents, edgecolor='black', linewidth=1.5)
        ax1.set_ylabel('Total Tokens', fontweight='bold')
        ax1.set_title('Token Usage by Agent', fontweight='bold')
        ax1.grid(axis='y', alpha=0.3)
        for bar, token in zip(bars1, tokens):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(token)}', ha='center', va='bottom', fontweight='bold')

        # 2. Reasoning Tokens vs Cached Tokens
        ax2 = axes[0, 1]
        reasoning_tokens = [self.agent_metrics[a]['reasoning_tokens'] for a in agents]
        cached_tokens = [self.agent_metrics[a]['cached_tokens'] for a in agents]
        
        x = range(len(agents))
        width = 0.35
        bars2_1 = ax2.bar([i - width/2 for i in x], reasoning_tokens, width, 
                          label='Reasoning Tokens', color='#FF6B6B', edgecolor='black', linewidth=1)
        bars2_2 = ax2.bar([i + width/2 for i in x], cached_tokens, width,
                          label='Cached Tokens', color='#4ECDC4', edgecolor='black', linewidth=1)
        ax2.set_ylabel('Tokens', fontweight='bold')
        ax2.set_title('Reasoning vs Cached Tokens', fontweight='bold')
        ax2.set_xticks(x)
        ax2.set_xticklabels(agents)
        ax2.legend()
        ax2.grid(axis='y', alpha=0.3)

        # 3. Response Processing Time per Agent
        ax3 = axes[1, 0]
        avg_durations = []
        for agent in agents:
            durations = self.agent_metrics[agent]['durations']
            avg_duration = sum(durations) / len(durations) if durations else 0
            avg_durations.append(avg_duration)
        
        bars3 = ax3.bar(agents, avg_durations, color=colors_agents, edgecolor='black', linewidth=1.5)
        ax3.set_ylabel('Average Duration (seconds)', fontweight='bold')
        ax3.set_title('Average Processing Time per Agent', fontweight='bold')
        ax3.grid(axis='y', alpha=0.3)
        for bar, duration in zip(bars3, avg_durations):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{duration:.2f}s', ha='center', va='bottom', fontweight='bold', fontsize=9)

        # 4. Reasoning Steps Timeline
        ax4 = axes[1, 1]
        steps = list(self.step_times.keys())
        durations_list = [sum(self.step_times[step]) for step in steps]
        
        if steps:
            colors_steps = plt.cm.Spectral(range(len(steps)))
            bars4 = ax4.barh(steps, durations_list, color=colors_steps, edgecolor='black', linewidth=1.5)
            ax4.set_xlabel('Total Duration (seconds)', fontweight='bold')
            ax4.set_title('Time per Reasoning Step', fontweight='bold')
            ax4.grid(axis='x', alpha=0.3)
            for i, (bar, duration) in enumerate(zip(bars4, durations_list)):
                width = bar.get_width()
                ax4.text(width, bar.get_y() + bar.get_height()/2.,
                        f'{duration:.2f}s', ha='left', va='center', fontweight='bold', fontsize=9)
        else:
            ax4.text(0.5, 0.5, 'No step data available', 
                    ha='center', va='center', transform=ax4.transAxes)
            ax4.set_title('Time per Reasoning Step', fontweight='bold')

        plt.tight_layout()
        plt.savefig('reasoning_metrics.png', dpi=300, bbox_inches='tight')
        print(Fore.GREEN + "\n✓ Metrics saved to 'reasoning_metrics.png'" + Style.RESET_ALL)
        plt.show()

    def visualize_response_summary(self, user_prompt, optimal_response, agent_responses):
        """Visualize response summary."""
        fig = plt.figure(figsize=(14, 8))
        gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

        # Title
        fig.suptitle(f'Response Analysis Dashboard\nPrompt: {user_prompt[:60]}...', 
                    fontsize=14, fontweight='bold')

        # 1. Agent Response Lengths
        ax1 = fig.add_subplot(gs[0, :])
        agents = list(agent_responses.keys())
        lengths = [len(agent_responses[a]) for a in agents]
        colors = plt.cm.Set3(range(len(agents)))
        
        bars = ax1.bar(agents, lengths, color=colors, edgecolor='black', linewidth=1.5)
        ax1.set_ylabel('Character Count', fontweight='bold')
        ax1.set_title('Response Length Comparison', fontweight='bold')
        ax1.grid(axis='y', alpha=0.3)
        
        for bar, length in zip(bars, lengths):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(length)}', ha='center', va='bottom', fontweight='bold')

        # 2. Response Text Display - Agent Responses
        for idx, agent in enumerate(agents[:2]):
            ax = fig.add_subplot(gs[1 + idx//2, idx%2])
            response_text = agent_responses[agent][:200] + ('...' if len(agent_responses[agent]) > 200 else '')
            
            ax.text(0.05, 0.95, response_text, transform=ax.transAxes,
                   fontsize=9, verticalalignment='top', wrap=True,
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            ax.set_title(f'{agent} Response Preview', fontweight='bold')
            ax.axis('off')

        # 3. Final Blended Response
        ax3 = fig.add_subplot(gs[2, :])
        response_preview = optimal_response[:500] + ('...' if len(optimal_response) > 500 else '')
        ax3.text(0.05, 0.95, response_preview, transform=ax3.transAxes,
                fontsize=9, verticalalignment='top', wrap=True,
                bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
        ax3.set_title('Final Blended Response', fontweight='bold')
        ax3.axis('off')

        plt.savefig('response_summary.png', dpi=300, bbox_inches='tight')
        print(Fore.GREEN + "✓ Response summary saved to 'response_summary.png'" + Style.RESET_ALL)
        plt.show()

    def get_metrics_dict(self):
        """Return metrics as dictionary for Streamlit display."""
        return {
            "agent_metrics": dict(self.agent_metrics),
            "step_times": self.step_times
        }


# Global metrics tracker instance
metrics_tracker = MetricsTracker()
