#!/usr/bin/env python3
"""
Test script to verify new o3 and o4-mini model integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Red.model import LLMModel, LLMHost
from Red.schema import response_openai
import openai
from dotenv import load_dotenv

load_dotenv()

def test_new_models():
    """Test the new o3 and o4-mini models"""
    
    # Initialize OpenAI client
    openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Test models
    models_to_test = [
        LLMModel.O3_MINI,
        LLMModel.O4_MINI,
        LLMModel.GPT_4O_MINI  # fallback
    ]
    
    # Simple test messages
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say 'Hello from model testing!'"}
    ]
    
    for model in models_to_test:
        print(f"\n=== Testing {model} ===")
        try:
            response, _ = response_openai(
                messages=messages,
                tools=[],  # No tools for simple test
                model=model
            )
            print(f"✅ {model} - Success: {response[0].message[:50]}...")
        except Exception as e:
            print(f"❌ {model} - Failed: {e}")
    
    # Test enum values
    print(f"\n=== Model Enum Values ===")
    print(f"O3_MINI: {LLMModel.O3_MINI}")
    print(f"O4_MINI: {LLMModel.O4_MINI}")
    print(f"GPT_4O_MINI: {LLMModel.GPT_4O_MINI}")

if __name__ == "__main__":
    test_new_models()
