#!/usr/bin/env python3
"""
Test script to verify that logs are being saved correctly in simulation mode
"""

import os
import sys
import tempfile
import shutil

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import simulate_command_line, save_logs
from Red.sangria import run_attacks

def test_logs_saving():
    """Test that logs are saved even in simulation mode"""
    
    # Create a temporary directory for test logs
    with tempfile.TemporaryDirectory() as temp_dir:
        log_path = os.path.join(temp_dir, "test_logs/")
        
        print(f"Testing log saving in temporary directory: {log_path}")
        print(f"Current config - simulate_command_line: {simulate_command_line}, save_logs: {save_logs}")
        
        # Run a single attack to test log saving
        try:
            run_attacks(n_attacks=1, save_logs=True, log_path=log_path)
            
            # Check if logs were created
            full_logs_dir = os.path.join(log_path, "full_logs")
            tokens_file = os.path.join(log_path, "tokens_used.json")
            
            logs_exist = os.path.exists(full_logs_dir)
            tokens_exist = os.path.exists(tokens_file)
            
            print(f"Full logs directory created: {logs_exist}")
            print(f"Tokens file created: {tokens_exist}")
            
            if logs_exist:
                log_files = os.listdir(full_logs_dir)
                print(f"Log files created: {log_files}")
                
                if log_files:
                    # Read and print first log file to verify content
                    first_log = os.path.join(full_logs_dir, log_files[0])
                    with open(first_log, 'r') as f:
                        content = f.read()
                        print(f"Sample log content (first 500 chars): {content[:500]}")
            
            if tokens_exist:
                with open(tokens_file, 'r') as f:
                    content = f.read()
                    print(f"Tokens file content: {content}")
            
            return logs_exist and tokens_exist
            
        except Exception as e:
            print(f"Error during test: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    print("Testing log saving functionality...")
    success = test_logs_saving()
    print(f"Test {'PASSED' if success else 'FAILED'}")
