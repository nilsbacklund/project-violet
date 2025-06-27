#!/usr/bin/env python3
"""
Debug script to test OpenAI API message structure
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import openai
from dotenv import load_dotenv
import json

load_dotenv()

# Initialize OpenAI client
openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Test tools (same format as your project)
tools = [
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a command on the Kali Linux SSH",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The command to run"
                    },
                    "tactic_used": {
                        "type": "string",
                        "description": "The MITRE ATT&CK tactic"
                    },
                    "technique_used": {
                        "type": "string",
                        "description": "The MITRE ATT&CK technique"
                    }
                },
                "required": ["command", "tactic_used", "technique_used"]
            }
        }
    }
]

def test_message_structure():
    """Test different message structures to identify the issue"""
    
    # Test 1: Basic conversation
    print("=== Test 1: Basic conversation ===")
    messages1 = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello"}
    ]
    
    try:
        response = openai_client.chat.completions.create(
            model="o3-mini",
            messages=messages1,
            tools=tools
        )
        print("✅ Test 1 passed")
        
        # Check if this response has tool calls
        if response.choices[0].message.tool_calls:
            print("Response has tool calls:")
            for call in response.choices[0].message.tool_calls:
                print(f"  - {call.function.name}: {call.function.arguments}")
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")
    
    # Test 2: Message with tool call response (simulating your scenario)
    print("\n=== Test 2: Message with tool response ===")
    messages2 = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Run the command 'ls'"},
        {
            "role": "assistant", 
            "content": "I'll run the ls command for you.",
            "tool_calls": [
                {
                    "id": "call_123",
                    "type": "function",
                    "function": {
                        "name": "run_command",
                        "arguments": json.dumps({
                            "command": "ls",
                            "tactic_used": "Discovery",
                            "technique_used": "File and Directory Discovery"
                        })
                    }
                }
            ]
        },
        {
            "role": "tool",
            "tool_call_id": "call_123",
            "name": "run_command",
            "content": "file1.txt\nfile2.txt\ndirectory1/"
        }
    ]
    
    try:
        response = openai_client.chat.completions.create(
            model="o3-mini",
            messages=messages2,
            tools=tools
        )
        print("✅ Test 2 passed")
    except Exception as e:
        print(f"❌ Test 2 failed: {e}")
    
    # Test 3: Invalid structure (tool without tool_calls)
    print("\n=== Test 3: Invalid structure (should fail) ===")
    messages3 = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello"},
        {
            "role": "tool",
            "tool_call_id": "call_invalid",
            "name": "run_command",
            "content": "some output"
        }
    ]
    
    try:
        response = openai_client.chat.completions.create(
            model="o3-mini",
            messages=messages3,
            tools=tools
        )
        print("✅ Test 3 passed (unexpected)")
    except Exception as e:
        print(f"❌ Test 3 failed as expected: {e}")

if __name__ == "__main__":
    test_message_structure()
