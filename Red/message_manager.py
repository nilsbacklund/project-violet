"""
Message and Tool Call Management Classes

This module provides clean, object-oriented interfaces for handling OpenAI API messages
and tool calls, making the code more readable and maintainable.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ToolCallFunction:
    """Represents a function within a tool call."""
    name: str
    arguments: str


@dataclass
class ToolCall:
    """Represents a single tool call from the assistant."""
    id: str
    type: str
    function: ToolCallFunction


class MessageBuilder:
    """
    Builder class for creating properly formatted OpenAI API messages.
    Handles message validation and ensures API compliance.
    """
    
    @staticmethod
    def sanitize_content(content: Any) -> str:
        """
        Ensure message content is never None, which causes OpenAI API errors.
        OpenAI API requires empty string instead of None values.
        """
        if content is None:
            return ""
        return str(content)
    
    @staticmethod
    def create_user_message(content: str) -> Dict[str, str]:
        """Create a user message."""
        return {
            "role": "user",
            "content": MessageBuilder.sanitize_content(content)
        }
    
    @staticmethod
    def create_system_message(content: str) -> Dict[str, str]:
        """Create a system message."""
        return {
            "role": "system",
            "content": MessageBuilder.sanitize_content(content)
        }
    
    @staticmethod
    def create_assistant_message(content: str) -> Dict[str, str]:
        """Create a basic assistant message without tool calls."""
        return {
            "role": "assistant",
            "content": MessageBuilder.sanitize_content(content)
        }
    
    @staticmethod
    def create_assistant_message_with_tool_calls(content: str, tool_calls: List[Any]) -> Dict[str, Any]:
        """
        Create an assistant message with tool calls.
        
        Args:
            content: The assistant's text response
            tool_calls: List of tool call objects from OpenAI response
            
        Returns:
            Properly formatted message dictionary
        """
        return {
            "role": "assistant",
            "content": MessageBuilder.sanitize_content(content),
            "tool_calls": ToolCallFormatter.format_tool_calls_for_conversation(tool_calls)
        }
    
    @staticmethod
    def create_tool_response_message(tool_call_id: str, tool_name: str, content: str) -> Dict[str, str]:
        """Create a tool response message."""
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": MessageBuilder.sanitize_content(content)
        }


class ToolCallFormatter:
    """
    Handles formatting and processing of tool calls for OpenAI API.
    Ensures proper structure and validation of tool call data.
    """
    
    @staticmethod
    def format_tool_calls_for_conversation(tool_calls: List[Any]) -> List[Dict[str, Any]]:
        """
        Format tool calls from OpenAI response for conversation history.
        
        Args:
            tool_calls: Raw tool calls from OpenAI API response
            
        Returns:
            List of properly formatted tool call dictionaries
        """
        if not tool_calls:
            return []
        
        formatted_calls = []
        for call in tool_calls:
            formatted_call = {
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.function.name,
                    "arguments": call.function.arguments
                }
            }
            formatted_calls.append(formatted_call)
        
        return formatted_calls
    
    @staticmethod
    def extract_tool_call_info(tool_call: Any) -> ToolCall:
        """
        Extract tool call information into a structured object.
        
        Args:
            tool_call: Raw tool call from OpenAI response
            
        Returns:
            ToolCall object with structured data
        """
        return ToolCall(
            id=tool_call.id,
            type="function",
            function=ToolCallFunction(
                name=tool_call.function.name,
                arguments=tool_call.function.arguments
            )
        )


class ConversationManager:
    """
    Manages conversation state and message history for attack sessions.
    Provides clean interface for adding different types of messages.
    """
    
    def __init__(self, initial_messages: List[Dict[str, Any]] = None):
        """Initialize conversation with optional starting messages."""
        self.messages = initial_messages.copy() if initial_messages else []
    
    def add_user_message(self, content: str) -> None:
        """Add a user message to the conversation."""
        message = MessageBuilder.create_user_message(content)
        self.messages.append(message)
    
    def add_system_message(self, content: str) -> None:
        """Add a system message to the conversation."""
        message = MessageBuilder.create_system_message(content)
        self.messages.append(message)
    
    def add_assistant_response(self, assistant_message: Any) -> bool:
        """
        Add assistant response to conversation, handling both regular and tool call responses.
        
        Args:
            assistant_message: Assistant message object from OpenAI API
            
        Returns:
            True if message contained tool calls, False otherwise
        """
        if assistant_message.tool_calls:
            message = MessageBuilder.create_assistant_message_with_tool_calls(
                assistant_message.content, 
                assistant_message.tool_calls
            )
            self.messages.append(message)
            return True  # Has tool calls
        else:
            message = MessageBuilder.create_assistant_message(assistant_message.content)
            self.messages.append(message)
            return False  # No tool calls
    
    def add_tool_responses(self, tool_response_messages: List[Dict[str, str]]) -> None:
        """Add multiple tool response messages to the conversation."""
        self.messages.extend(tool_response_messages)
    
    def add_tool_response(self, tool_call_id: str, tool_name: str, content: str) -> None:
        """Add a single tool response message to the conversation."""
        message = MessageBuilder.create_tool_response_message(tool_call_id, tool_name, content)
        self.messages.append(message)
    
    def get_messages(self) -> List[Dict[str, Any]]:
        """Get the current conversation messages."""
        return self.messages
    
    def validate_messages(self) -> None:
        """
        Validate that all messages have proper content before sending to OpenAI API.
        Raises ValueError if any message has None content for non-assistant roles.
        """
        for idx, msg in enumerate(self.messages):
            if msg.get('content') is None and msg.get('role') not in ['assistant']:
                print(f"ERROR: Message {idx} has None content: {msg}")
                print(f"All messages: {self.messages}")
                raise ValueError(f"Message at index {idx} has None content")
    
    def reset_conversation(self, initial_messages: List[Dict[str, Any]] = None) -> None:
        """Reset the conversation to initial state."""
        self.messages = initial_messages.copy() if initial_messages else []
    
    def get_message_count(self) -> int:
        """Get the total number of messages in the conversation."""
        return len(self.messages)
    
    def print_conversation_summary(self) -> None:
        """Print a summary of the current conversation state."""
        print(f"Conversation has {len(self.messages)} messages:")
        for i, msg in enumerate(self.messages):
            role = msg.get('role', 'unknown')
            has_tool_calls = 'tool_calls' in msg
            tool_info = f" (with {len(msg['tool_calls'])} tool calls)" if has_tool_calls else ""
            print(f"  {i+1}. {role}{tool_info}")
