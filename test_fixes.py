#!/usr/bin/env python3
"""
Simple test to verify log saving functionality
"""

import os
import tempfile
import json

def test_log_directory_creation():
    """Test if log directories are created properly"""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        log_path = os.path.join(temp_dir, "test_logs/")
        
        # Test the same logic as in run_attacks
        os.makedirs(log_path + "full_logs", exist_ok=True)
        
        # Verify directories were created
        full_logs_exists = os.path.exists(log_path + "full_logs")
        
        print(f"Log path: {log_path}")
        print(f"Full logs directory created: {full_logs_exists}")
        
        # Test creating a sample log file
        sample_log = {"test": "data", "session": 1}
        log_file_path = log_path + "full_logs/attack_1.json"
        
        with open(log_file_path, 'w') as f:
            json.dump(sample_log, f, indent=2)
        
        log_file_exists = os.path.exists(log_file_path)
        print(f"Sample log file created: {log_file_exists}")
        
        # Test tokens file
        tokens_file_path = log_path + "tokens_used.json"
        with open(tokens_file_path, 'w') as f:
            json.dump({"prompt_tokens": 100, "completion_tokens": 50}, f)
        
        tokens_file_exists = os.path.exists(tokens_file_path)
        print(f"Tokens file created: {tokens_file_exists}")
        
        return full_logs_exists and log_file_exists and tokens_file_exists

def verify_config_models():
    """Verify that config files use new models"""
    
    print("\n=== Model Configuration Check ===")
    
    # Check main config
    try:
        import sys
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        import config
        
        print(f"Sangria model: {config.llm_model_sangria}")
        print(f"Config model: {config.llm_model_config}")
        print(f"Save logs: {config.save_logs}")
        print(f"Simulate command line: {config.simulate_command_line}")
        
        # Check if models are new o-series
        valid_models = ["O3_MINI", "O4_MINI"]
        sangria_model_name = str(config.llm_model_sangria).split('.')[-1]
        config_model_name = str(config.llm_model_config).split('.')[-1]
        
        print(f"Sangria model name: {sangria_model_name}")
        print(f"Config model name: {config_model_name}")
        
        sangria_valid = sangria_model_name in valid_models
        config_valid = config_model_name in valid_models
        
        print(f"Sangria model is new o-series: {sangria_valid}")
        print(f"Config model is new o-series: {config_valid}")
        
        return sangria_valid and config_valid
        
    except ImportError as e:
        print(f"Could not import config: {e}")
        return False

if __name__ == "__main__":
    print("=== Testing Log Directory Creation ===")
    log_test_passed = test_log_directory_creation()
    print(f"Log directory test: {'PASSED' if log_test_passed else 'FAILED'}")
    
    model_test_passed = verify_config_models()
    print(f"Model configuration test: {'PASSED' if model_test_passed else 'FAILED'}")
    
    overall_result = log_test_passed and model_test_passed
    print(f"\n=== Overall Result: {'PASSED' if overall_result else 'FAILED'} ===")
