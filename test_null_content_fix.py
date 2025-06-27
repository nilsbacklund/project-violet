#!/usr/bin/env python3
"""
Test script to verify the null content fix
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_sanitize_function():
    """Test the sanitize_message_content function"""
    sys.path.append('/Users/nilsbacklund/Documents/Jobb/AISweden/project-violet')
    from Red.sangria import sanitize_message_content
    
    # Test cases
    test_cases = [
        (None, ""),
        ("", ""),
        ("Hello", "Hello"),
        (0, 0),
        (False, False),
    ]
    
    print("Testing sanitize_message_content function:")
    for input_val, expected in test_cases:
        result = sanitize_message_content(input_val)
        status = "✅" if result == expected else "❌"
        print(f"{status} Input: {repr(input_val)} -> Output: {repr(result)} (Expected: {repr(expected)})")

def test_message_structure():
    """Test message structure with potential None values"""
    
    # Simulate the problematic scenario
    assistant_message_with_none_content = type('obj', (object,), {
        'content': None,
        'tool_calls': [
            type('obj', (object,), {
                'id': 'call_123',
                'function': type('obj', (object,), {
                    'name': 'run_command',
                    'arguments': '{"command": "ls"}'
                })()
            })()
        ]
    })()
    
    # Test the sanitization
    from Red.sangria import sanitize_message_content
    
    content = sanitize_message_content(assistant_message_with_none_content.content)
    print(f"\nMessage content sanitization test:")
    print(f"Original content: {repr(assistant_message_with_none_content.content)}")
    print(f"Sanitized content: {repr(content)}")
    print(f"Is valid for OpenAI: {'✅' if content is not None else '❌'}")

if __name__ == "__main__":
    test_sanitize_function()
    test_message_structure()
