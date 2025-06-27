"""
Docker and Logging Utilities

This module handles Docker container management and log file operations
for attack sessions, providing clean interfaces for these operations.
"""

import os
from typing import List, Dict, Any
from Utils import save_json_to_file, append_json_to_file
from Blue_Lagoon.honeypot_tools import start_dockers, stop_dockers
from Red.model import DataLogObject
import config


class DockerManager:
    """Manages Docker containers for attack sessions."""
    
    @staticmethod
    def start_containers_if_needed() -> bool:
        """
        Start Docker containers if not in simulation mode.
        
        Returns:
            True if containers were started, False if in simulation mode
        """
        if not config.simulate_command_line:
            print("Starting Docker containers for attack session")
            start_dockers()
            return True
        return False
    
    @staticmethod
    def stop_containers_if_running() -> None:
        """Stop Docker containers if they were started."""
        if not config.simulate_command_line:
            print("Stopping Docker containers")
            stop_dockers()
    
    @staticmethod
    def manage_containers_for_session(attack_number: int, total_attacks: int) -> bool:
        """
        Manage container lifecycle for a single attack session.
        
        Args:
            attack_number: Current attack number (1-based)
            total_attacks: Total number of attacks planned
            
        Returns:
            True if containers were started and need cleanup
        """
        if not config.simulate_command_line:
            print(f"Starting Docker containers for attack {attack_number}/{total_attacks}")
            start_dockers()
            return True
        return False


class LogFileManager:
    """Manages saving logs and token usage to files."""
    
    @staticmethod
    def create_log_directories(log_path: str) -> None:
        """Create necessary log directories."""
        os.makedirs(log_path + "full_logs", exist_ok=True)
    
    @staticmethod
    def save_attack_logs(logs: List[DataLogObject], log_path: str, attack_number: int) -> str:
        """
        Save attack logs to file.
        
        Args:
            logs: List of DataLogObject instances
            log_path: Base path for log files
            attack_number: Attack session number
            
        Returns:
            Path to the saved log file
        """
        # Convert logs to dictionary format
        logs_dict = [log.to_dict() for log in logs]
        
        # Create file path
        log_file_path = log_path + f"full_logs/attack_{attack_number}.json"
        
        # Save file
        save_json_to_file(logs_dict, log_file_path)
        
        return log_file_path
    
    @staticmethod
    def save_token_usage(tokens_used: Dict[str, int], log_path: str) -> str:
        """
        Save token usage to file.
        
        Args:
            tokens_used: Dictionary with token usage data
            log_path: Base path for log files
            
        Returns:
            Path to the saved tokens file
        """
        tokens_file_path = log_path + "tokens_used.json"
        append_json_to_file(tokens_used, tokens_file_path)
        return tokens_file_path
    
    @staticmethod
    def save_attack_session_data(logs: List[DataLogObject], tokens_used: Dict[str, int], 
                                log_path: str, attack_number: int) -> None:
        """
        Save complete attack session data (logs + tokens).
        
        Args:
            logs: List of DataLogObject instances
            tokens_used: Dictionary with token usage data
            log_path: Base path for log files
            attack_number: Attack session number
        """
        # Create directories
        LogFileManager.create_log_directories(log_path)
        
        # Save logs
        log_file_path = LogFileManager.save_attack_logs(logs, log_path, attack_number)
        
        # Save tokens
        tokens_file_path = LogFileManager.save_token_usage(tokens_used, log_path)
        
        # Provide feedback
        print(f"✓ Logs saved to: {log_file_path}")
        print(f"✓ Tokens saved to: {tokens_file_path}")


class AttackProgressTracker:
    """Tracks and displays progress for multiple attack sessions."""
    
    def __init__(self, total_attacks: int):
        self.total_attacks = total_attacks
        self.completed_attacks = 0
        self.tokens_used_list = []
    
    def start_attack_session(self, attack_number: int) -> None:
        """Display start message for an attack session."""
        print(f"\n{'='*60}")
        print(f"ATTACK SESSION {attack_number} of {self.total_attacks}")
        print(f"{'='*60}")
    
    def complete_attack_session(self, attack_number: int, tokens_used: Dict[str, int]) -> None:
        """Record completion of an attack session."""
        self.completed_attacks += 1
        self.tokens_used_list.append(tokens_used)
        print(f"✓ Attack session {attack_number} completed")
        print(f"Progress: {self.completed_attacks}/{self.total_attacks} sessions completed\n")
    
    def print_final_summary(self) -> None:
        """Print final summary of all attack sessions."""
        if not self.tokens_used_list:
            print("No attack sessions completed")
            return
        
        total_prompt_tokens = sum(t['prompt_tokens'] for t in self.tokens_used_list)
        total_completion_tokens = sum(t['completion_tokens'] for t in self.tokens_used_list)
        total_cached_tokens = sum(t['cached_tokens'] for t in self.tokens_used_list)
        
        print(f"\n{'='*60}")
        print(f"ATTACK CAMPAIGN SUMMARY")
        print(f"{'='*60}")
        print(f"Total sessions completed: {self.completed_attacks}")
        print(f"Total prompt tokens: {total_prompt_tokens:,}")
        print(f"Total completion tokens: {total_completion_tokens:,}")
        print(f"Total cached tokens: {total_cached_tokens:,}")
        print(f"Total tokens used: {total_prompt_tokens + total_completion_tokens:,}")
        print(f"{'='*60}")
    
    def get_tokens_summary(self) -> List[Dict[str, int]]:
        """Get the complete list of token usage per session."""
        return self.tokens_used_list.copy()
