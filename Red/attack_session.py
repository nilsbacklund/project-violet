"""
Attack Session Management

This module handles the orchestration of individual attack sessions,
including token tracking, iteration management, and termination logic.
"""

from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from Red.message_manager import ConversationManager, ToolCallFormatter
from Red.model import MitreMethodUsed, DataLogObject
from Red.schema import response, start_ssh, get_new_hp_logs
from Red.tools import handle_tool_call
import Red.sangria_config as sangria_config
import config


@dataclass
class TokenUsage:
    """Tracks token usage for an attack session."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cached_tokens: int = 0
    
    def add_response_tokens(self, assistant_response: Any) -> None:
        """Add tokens from an assistant response."""
        self.prompt_tokens += assistant_response.prompt_tokens - assistant_response.cached_tokens
        self.completion_tokens += assistant_response.completion_tokens
        self.cached_tokens += assistant_response.cached_tokens
    
    def print_current_usage(self, assistant_response: Any) -> None:
        """Print current iteration token usage."""
        print(f"Prompt tokens: {assistant_response.prompt_tokens}, "
              f"Completion tokens: {assistant_response.completion_tokens}, "
              f"Cached tokens: {assistant_response.cached_tokens}")
    
    def print_session_summary(self) -> None:
        """Print total session token usage."""
        print(f"Total prompt tokens: {self.prompt_tokens}")
        print(f"Total completion tokens: {self.completion_tokens}")
        print(f"Total cached tokens: {self.cached_tokens}")
    
    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary format for logging."""
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "cached_tokens": self.cached_tokens
        }


class AttackIteration:
    """Manages a single iteration within an attack session."""
    
    def __init__(self, iteration_number: int):
        self.iteration_number = iteration_number
        self.data_log = DataLogObject(iteration_number)
        self.mitre_method_used = MitreMethodUsed()
        self.should_terminate = False
    
    def process_llm_response(self, conversation: ConversationManager, token_usage: TokenUsage, ssh: Any) -> bool:
        """
        Process the LLM response and handle tool calls.
        
        Returns:
            True if attack should terminate, False to continue
        """
        print(f'Iteration {self.iteration_number + 1} / {config.max_session_length}')
        
        # Validate messages before API call
        conversation.validate_messages()
        
        # Get LLM response
        assistant_response, assistant_message = response(
            sangria_config.model_host,
            config.llm_model_sangria,
            conversation.get_messages(),
            sangria_config.tools
        )
        
        # Update token tracking
        token_usage.add_response_tokens(assistant_response)
        token_usage.print_current_usage(assistant_response)
        self.data_log.llm_response = assistant_response
        
        # Add assistant response to conversation
        has_tool_calls = conversation.add_assistant_response(assistant_message)
        
        # Process tool calls if present
        if has_tool_calls:
            return self._process_tool_calls(assistant_message, conversation, ssh)
        
        return False  # No termination
    
    def _process_tool_calls(self, assistant_message: Any, 
                          conversation: ConversationManager, ssh: Any) -> bool:
        """
        Process tool calls and check for termination.
        
        Returns:
            True if attack should terminate, False to continue
        """
        # Handle tool calls
        tool_response_messages, self.mitre_method_used = handle_tool_call(assistant_message, ssh)
        conversation.add_tool_responses(tool_response_messages)
        
        # Store tool responses in log
        self.data_log.tool_response = tool_response_messages
        
        # Debug output
        print(f"Tool response messages: {tool_response_messages}")
        print(f"Total conversation messages: {conversation.get_message_count()}")
        
        # Check for termination
        return self._check_for_termination(tool_response_messages)
    
    def _check_for_termination(self, tool_response_messages: List[Dict[str, Any]]) -> bool:
        """
        Check if any tool response indicates attack termination.
        
        Returns:
            True if attack should terminate, False to continue
        """
        for message in tool_response_messages:
            if message.get('name') == "terminate":
                success = message.get('content') == 'True'
                print(f"The attack was {'successful' if success else 'unsuccessful'} "
                      f"after {self.iteration_number + 1} iterations.")
                if success:
                    self.data_log.attack_success = True
                return True  # Should terminate
        
        return False  # Continue
    
    def print_debug_output(self) -> None:
        """Print comprehensive debug output for this iteration."""
        if not config.print_output:
            return
        
        assistant_response = self.data_log.llm_response
        tool_responses = getattr(self.data_log, 'tool_response', [])
        
        print("\n" + "="*60)
        print(f"🤖 ITERATION {self.iteration_number + 1} - LLM RESPONSE")
        print("="*60)
        
        # Print the raw response object for debugging
        print(f"📊 Response Object: {assistant_response}")
        
        # Check if we have thinking process/content
        has_thinking_content = assistant_response.message and assistant_response.message.strip()
        
        if has_thinking_content:
            print(f"\n💭 THINKING PROCESS:")
            print("-" * 30)
            print(f"{assistant_response.message}")
            print("-" * 30)
        else:
            # LLM went straight to tool use without thinking text
            print(f"\n⚡ DIRECT ACTION:")
            print("-" * 30)
            print("LLM proceeded directly to tool execution without explanatory text.")
            print("This usually happens when the model is very confident about the next step.")
            print("-" * 30)
        
        # Print tool calls if any
        if assistant_response.function:
            print(f"\n🔧 TOOL CALL:")
            print(f"Function: {assistant_response.function}")
            print(f"Arguments: {assistant_response.arguments}")
            
            # Print tool responses
            if tool_responses:
                print(f"\n📝 TOOL RESPONSES:")
                for i, response in enumerate(tool_responses, 1):
                    tool_name = response.get('name', 'unknown')
                    content = response.get('content', 'No content')
                    # Truncate very long responses for readability
                    if len(content) > 200:
                        content = content[:200] + "... [truncated]"
                    print(f"  {i}. {tool_name}: {content}")
            else:
                print("  No tool responses received")
        else:
            print(f"\n🗣️ TEXT-ONLY RESPONSE:")
            print("LLM provided only text without tool calls.")
        
        # Print MITRE method information
        if self.mitre_method_used:
            print(f"\n🎯 MITRE METHOD USED:")
            print(f"  {self.mitre_method_used}")
        else:
            print(f"\n🎯 MITRE METHOD: None identified")
        
        print("="*60)
    
    def print_iteration_summary(self) -> None:
        """Print a concise summary of this iteration."""
        assistant_response = self.data_log.llm_response
        tool_responses = getattr(self.data_log, 'tool_response', [])
        
        # Check if LLM provided thinking text
        has_thinking = assistant_response.message and assistant_response.message.strip()
        
        print(f"\n📋 Iteration {self.iteration_number + 1} Summary:")
        print(f"   � Thinking text: {'Yes' if has_thinking else 'No (direct action)'}")
        print(f"   🔧 Tool calls: {len(tool_responses) if tool_responses else 0}")
        print(f"   🎯 MITRE method: {'Yes' if self.mitre_method_used else 'No'}")
        
        # Check if this iteration resulted in termination
        if tool_responses:
            for response in tool_responses:
                if response.get('name') == 'terminate':
                    success = response.get('content') == 'True'
                    print(f"   🏁 Attack result: {'SUCCESS' if success else 'FAILED'}")
                    break
    
    def collect_honeypot_logs(self) -> None:
        """Collect honeypot logs if not in simulation mode."""
        if not config.simulate_command_line:
            beelzebub_logs = get_new_hp_logs()
            self.data_log.beelzebub_response = beelzebub_logs
    
    def get_data_log(self) -> DataLogObject:
        """Get the data log for this iteration."""
        return self.data_log
    
    def get_mitre_method(self) -> MitreMethodUsed:
        """Get the MITRE method used in this iteration."""
        return self.mitre_method_used


class AttackSession:
    """Manages a complete attack session with multiple iterations."""
    
    def __init__(self, initial_messages: List[Dict[str, Any]]):
        self.conversation = ConversationManager(initial_messages)
        self.token_usage = TokenUsage()
        self.ssh_connection = None
        self.full_logs = []
        self.mitre_methods_used = []
    
    def setup_ssh_connection(self) -> None:
        """Set up SSH connection if not in simulation mode."""
        if not config.simulate_command_line:
            self.ssh_connection = start_ssh()
        else:
            self.ssh_connection = None
    
    def run_attack_iterations(self) -> None:
        """Run the main attack loop with multiple iterations."""
        for i in range(config.max_session_length):
            iteration = AttackIteration(i)
            
            # Process LLM response and tool calls
            should_terminate = iteration.process_llm_response(
                self.conversation, self.token_usage, self.ssh_connection
            )
            
            # Print debug output (detailed)
            iteration.print_debug_output()
            
            # Print iteration summary (concise)
            iteration.print_iteration_summary()
            
            # Collect honeypot logs
            iteration.collect_honeypot_logs()
            
            # Store logs and MITRE methods
            self.full_logs.append(iteration.get_data_log())
            self.mitre_methods_used.append(iteration.get_mitre_method())
            
            # Check for termination
            if should_terminate:
                print(f"\n🏁 Attack session terminated after {i + 1} iterations")
                break
    
    def print_session_summary(self) -> None:
        """Print comprehensive summary of the attack session."""
        print(f"\n{'='*80}")
        print(f"🎯 ATTACK SESSION SUMMARY")
        print(f"{'='*80}")
        
        # Basic session info
        print(f"📊 Session Statistics:")
        print(f"   Total iterations: {len(self.full_logs)}")
        print(f"   Total conversation messages: {self.conversation.get_message_count()}")
        
        # Token usage summary
        print(f"\n💰 Token Usage:")
        token_dict = self.token_usage.to_dict()
        print(f"   Prompt tokens: {token_dict['prompt_tokens']:,}")
        print(f"   Completion tokens: {token_dict['completion_tokens']:,}")
        print(f"   Cached tokens: {token_dict['cached_tokens']:,}")
        total_tokens = token_dict['prompt_tokens'] + token_dict['completion_tokens']
        print(f"   Total tokens used: {total_tokens:,}")
        
        # Attack outcome
        print(f"\n🎯 Attack Outcome:")
        successful_attack = any(log.attack_success for log in self.full_logs if hasattr(log, 'attack_success') and log.attack_success)
        print(f"   Result: {'✅ SUCCESS' if successful_attack else '❌ UNSUCCESSFUL'}")
        
        # MITRE methods used
        mitre_methods = [method for method in self.mitre_methods_used if method]
        if mitre_methods:
            print(f"\n🛡️ MITRE ATT&CK Methods:")
            for i, method in enumerate(mitre_methods, 1):
                print(f"   {i}. {method}")
        else:
            print(f"\n🛡️ MITRE ATT&CK Methods: None identified")
        
        # Tool usage summary
        tool_calls_count = sum(1 for log in self.full_logs 
                              if hasattr(log, 'tool_response') and log.tool_response)
        print(f"\n🔧 Tool Usage:")
        print(f"   Tool calls made: {tool_calls_count}")
        
        print(f"{'='*80}")
    
    def print_final_attack_output(self) -> None:
        """Print the final output and conclusion of the attack."""
        print(f"\n{'🏆' if self._was_attack_successful() else '💥'} FINAL ATTACK RESULT")
        print(f"{'='*80}")
        
        if self._was_attack_successful():
            print("✅ ATTACK SUCCESSFUL!")
            print("The cybersecurity simulation achieved its objectives.")
        else:
            print("❌ ATTACK UNSUCCESSFUL")
            print("The cybersecurity simulation did not achieve its objectives.")
        
        # Print key insights
        print(f"\n📋 Key Insights:")
        print(f"   • Attack duration: {len(self.full_logs)} iterations")
        
        total_tokens = (self.token_usage.prompt_tokens + 
                       self.token_usage.completion_tokens)
        print(f"   • Computational cost: {total_tokens:,} tokens")
        
        # Find the most recent tool responses to show final commands
        final_commands = []
        for log in reversed(self.full_logs):
            if hasattr(log, 'tool_response') and log.tool_response:
                for response in log.tool_response:
                    if response.get('name') == 'run_command':
                        final_commands.append(response.get('content', 'No output'))
                if final_commands:
                    break
        
        if final_commands:
            print(f"   • Final command output: {final_commands[0][:100]}{'...' if len(final_commands[0]) > 100 else ''}")
        
        print(f"{'='*80}")
    
    def _was_attack_successful(self) -> bool:
        """Check if the attack was successful."""
        return any(log.attack_success for log in self.full_logs 
                  if hasattr(log, 'attack_success') and log.attack_success)
    
    def get_results(self) -> Tuple[List[DataLogObject], Dict[str, int]]:
        """
        Get the results of the attack session.
        
        Returns:
            Tuple of (full_logs, tokens_used_dict)
        """
        return self.full_logs, self.token_usage.to_dict()
    
    def get_conversation_summary(self) -> None:
        """Print conversation summary for debugging."""
        self.conversation.print_conversation_summary()


def run_single_attack_session(save_logs: bool, initial_messages: List[Dict[str, Any]]) -> Tuple[List[DataLogObject], Dict[str, int]]:
    """
    Execute a single attack session using the new class-based approach.
    
    This function creates and manages an AttackSession, handling all the
    complexity of message management, token tracking, and iteration logic.
    Enhanced with comprehensive console output including thinking process.
    
    Args:
        save_logs: Whether logs are being collected (used for compatibility)
        initial_messages: Starting conversation messages
        
    Returns:
        Tuple of (full_logs, tokens_used_dict)
    """
    print(f"\nSTARTING ATTACK SESSION")
    print(f"{'='*80}")
    
    # Create and configure attack session
    session = AttackSession(initial_messages)
    session.setup_ssh_connection()
    
    # Run the attack iterations with enhanced output
    session.run_attack_iterations()
    
    # Print comprehensive session summary
    session.print_session_summary()
    
    # Print final attack result
    session.print_final_attack_output()
    
    # Return results
    return session.get_results()
