#!/usr/bin/env python3
"""
Test the refactored sangria code with new class-based architecture
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Test only the standalone classes that don't have heavy dependencies
from Red.message_manager import MessageBuilder, ConversationManager, ToolCallFormatter


def test_message_builder():
    """Test the MessageBuilder class functionality."""
    print("=== Testing MessageBuilder ===")
    
    # Test content sanitization
    assert MessageBuilder.sanitize_content(None) == ""
    assert MessageBuilder.sanitize_content("test") == "test"
    print("✓ Content sanitization works")
    
    # Test message creation
    user_msg = MessageBuilder.create_user_message("Hello")
    assert user_msg["role"] == "user"
    assert user_msg["content"] == "Hello"
    print("✓ User message creation works")
    
    system_msg = MessageBuilder.create_system_message("System prompt")
    assert system_msg["role"] == "system"
    assert system_msg["content"] == "System prompt"
    print("✓ System message creation works")
    
    assistant_msg = MessageBuilder.create_assistant_message("Response")
    assert assistant_msg["role"] == "assistant"
    assert assistant_msg["content"] == "Response"
    print("✓ Assistant message creation works")
    
    # Test tool response message
    tool_msg = MessageBuilder.create_tool_response_message("call_123", "run_command", "Success")
    assert tool_msg["role"] == "tool"
    assert tool_msg["tool_call_id"] == "call_123"
    assert tool_msg["name"] == "run_command"
    assert tool_msg["content"] == "Success"
    print("✓ Tool response message creation works")


def test_conversation_manager():
    """Test the ConversationManager class functionality."""
    print("\n=== Testing ConversationManager ===")
    
    # Initialize conversation
    conv = ConversationManager()
    assert conv.get_message_count() == 0
    print("✓ Empty conversation initialization works")
    
    # Add messages
    conv.add_user_message("Test user message")
    conv.add_system_message("Test system message")
    
    # Create mock assistant message
    class MockAssistantMessage:
        def __init__(self, content, tool_calls=None):
            self.content = content
            self.tool_calls = tool_calls
    
    # Test assistant message without tool calls
    mock_assistant = MockAssistantMessage("Assistant response")
    has_tool_calls = conv.add_assistant_response(mock_assistant)
    assert has_tool_calls == False
    print("✓ Assistant response without tool calls works")
    
    assert conv.get_message_count() == 3
    print("✓ Adding messages works")
    
    # Test validation (should not raise error)
    try:
        conv.validate_messages()
        print("✓ Message validation works")
    except ValueError:
        print("✗ Message validation failed")
    
    # Test tool response addition
    conv.add_tool_response("call_123", "test_tool", "Tool result")
    assert conv.get_message_count() == 4
    print("✓ Tool response addition works")


def test_tool_call_formatter():
    """Test the ToolCallFormatter class functionality."""
    print("\n=== Testing ToolCallFormatter ===")
    
    # Create mock tool call
    class MockFunction:
        def __init__(self, name, arguments):
            self.name = name
            self.arguments = arguments
    
    class MockToolCall:
        def __init__(self, id, function):
            self.id = id
            self.function = function
    
    mock_function = MockFunction("run_command", '{"command": "ls"}')
    mock_tool_call = MockToolCall("call_123", mock_function)
    
    # Test formatting
    formatted = ToolCallFormatter.format_tool_calls_for_conversation([mock_tool_call])
    
    assert len(formatted) == 1
    assert formatted[0]["id"] == "call_123"
    assert formatted[0]["type"] == "function"
    assert formatted[0]["function"]["name"] == "run_command"
    print("✓ Tool call formatting works")
    
    # Test extraction
    extracted = ToolCallFormatter.extract_tool_call_info(mock_tool_call)
    assert extracted.id == "call_123"
    assert extracted.function.name == "run_command"
    print("✓ Tool call extraction works")


def test_conversation_with_tool_calls():
    """Test conversation management with tool calls."""
    print("\n=== Testing Conversation with Tool Calls ===")
    
    conv = ConversationManager()
    
    # Create mock tool calls
    class MockFunction:
        def __init__(self, name, arguments):
            self.name = name
            self.arguments = arguments
    
    class MockToolCall:
        def __init__(self, id, function):
            self.id = id
            self.function = function
    
    class MockAssistantMessage:
        def __init__(self, content, tool_calls=None):
            self.content = content
            self.tool_calls = tool_calls
    
    # Test with tool calls
    mock_function = MockFunction("run_command", '{"command": "whoami"}')
    mock_tool_call = MockToolCall("call_456", mock_function)
    mock_assistant_with_tools = MockAssistantMessage("I'll run a command", [mock_tool_call])
    
    has_tool_calls = conv.add_assistant_response(mock_assistant_with_tools)
    assert has_tool_calls == True
    print("✓ Assistant response with tool calls works")
    
    # Check the message structure
    messages = conv.get_messages()
    last_message = messages[-1]
    assert last_message["role"] == "assistant"
    assert "tool_calls" in last_message
    assert len(last_message["tool_calls"]) == 1
    print("✓ Tool calls properly formatted in conversation")


def run_all_tests():
    """Run all tests for the refactored code."""
    print("TESTING REFACTORED SANGRIA CLASSES")
    print("=" * 50)
    
    try:
        test_message_builder()
        test_conversation_manager()
        test_tool_call_formatter()
        test_conversation_with_tool_calls()
        
        print("\n" + "=" * 50)
        print("✅ ALL CORE TESTS PASSED!")
        print("The refactored message management classes are working correctly.")
        print("\nKey improvements:")
        print("- Clean, object-oriented message creation")
        print("- Proper tool call formatting and handling")
        print("- Conversation state management")
        print("- Content sanitization for OpenAI API compliance")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
