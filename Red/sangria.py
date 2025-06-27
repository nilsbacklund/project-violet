# %%
import sys
import os

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import Red.sangria_config as sangria_config
from Red.attack_session import run_single_attack_session
from Red.utilities import DockerManager, LogFileManager, AttackProgressTracker
from Red.model import MitreMethodUsed

# Global tracking for MITRE methods (maintained for compatibility)
mitre_method_used_list = []

def run_attacks(n_attacks, save_logs, log_path):
    """
    Execute multiple attack sessions with improved organization and feedback.
    
    This function orchestrates multiple attack sessions using the new class-based
    architecture, providing better progress tracking and resource management.
    
    Args:
        n_attacks: Number of attack sessions to run
        save_logs: Whether to save logs to files
        log_path: Base path for saving log files
    """
    # Initialize progress tracking
    progress_tracker = AttackProgressTracker(n_attacks)
    
    for i in range(n_attacks):
        attack_number = i + 1
        
        # Display progress
        progress_tracker.start_attack_session(attack_number)
        
        # Reset messages for each attack session
        fresh_messages = sangria_config.messages.copy()

        containers_started = DockerManager.manage_containers_for_session(attack_number, n_attacks)
        
        try:
            logs, tokens_used = run_single_attack_session(save_logs, fresh_messages)
            
            if save_logs:
                LogFileManager.save_attack_session_data(logs, tokens_used, log_path, attack_number)
            
            progress_tracker.complete_attack_session(attack_number, tokens_used)
            
        finally:
            if containers_started:
                DockerManager.stop_containers_if_running()
    
    progress_tracker.print_final_summary()


# %%
