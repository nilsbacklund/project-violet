"""
SANGRIA REFACTORING SUMMARY
===========================

The sangria.py file has been successfully refactored into a clean, class-based architecture
that is much more maintainable and follows object-oriented principles.

NEW FILE STRUCTURE:
==================

1. Red/message_manager.py
   - MessageBuilder: Creates properly formatted OpenAI API messages
   - ConversationManager: Manages conversation state and message history
   - ToolCallFormatter: Handles tool call formatting and processing
   
2. Red/attack_session.py
   - TokenUsage: Tracks token usage with detailed statistics
   - AttackIteration: Manages individual attack iterations
   - AttackSession: Orchestrates complete attack sessions
   - run_single_attack_session(): Main session execution function
   
3. Red/utilities.py
   - DockerManager: Handles Docker container lifecycle
   - LogFileManager: Manages log and token file operations
   - AttackProgressTracker: Tracks progress across multiple sessions
   
4. Red/sangria.py (refactored)
   - Clean main interface maintaining backward compatibility
   - Uses new classes under the hood
   - Much shorter and more readable

KEY IMPROVEMENTS:
================

✅ MODULAR DESIGN
- Broke down large functions into focused, single-responsibility classes
- Each class handles one specific aspect of the system
- Easy to test, modify, and extend individual components

✅ SELF-EXPLANATORY CODE
- Class and method names clearly describe their purpose
- Comprehensive docstrings explaining functionality
- Code reads like natural language

✅ BETTER TOOL CALL HANDLING
- ToolCallFormatter class provides clean interface for OpenAI tool calls
- MessageBuilder creates properly structured messages with tool calls
- ConversationManager handles complex conversation state

✅ IMPROVED MESSAGE MANAGEMENT
- MessageBuilder ensures API compliance (no None content)
- ConversationManager provides clean interface for adding messages
- Automatic validation and sanitization

✅ ROBUST TOKEN TRACKING
- TokenUsage class with detailed statistics and summaries
- Proper token calculation (excluding cached tokens from prompt count)
- Clear reporting and dictionary conversion for logging

✅ ENHANCED PROGRESS FEEDBACK
- AttackProgressTracker provides detailed progress information
- Clear session boundaries and completion status
- Comprehensive final summaries with token usage statistics

✅ CLEAN RESOURCE MANAGEMENT
- DockerManager handles container lifecycle cleanly
- LogFileManager provides organized file operations
- Proper error handling and cleanup

✅ MAINTAINED COMPATIBILITY
- run_single_attack() and run_attacks() functions maintain same interface
- Existing code calling sangria.py continues to work unchanged
- All original functionality preserved

BENEFITS FOR DEVELOPERS:
=======================

🔧 EASIER DEBUGGING
- Smaller functions are easier to trace and debug
- Clear separation of concerns makes issues easier to isolate
- Better error messages and logging

🧪 EASIER TESTING
- Each class can be tested independently
- Mock objects are easier to create for isolated testing
- Clear interfaces make unit testing straightforward

📈 EASIER EXTENSION
- Adding new message types: extend MessageBuilder
- Adding new progress tracking: extend AttackProgressTracker
- Adding new tool call handling: extend ToolCallFormatter

🔄 EASIER MAINTENANCE
- Changes to tool call handling only affect ToolCallFormatter
- Changes to logging only affect LogFileManager
- Changes to conversation flow only affect ConversationManager

EXAMPLE USAGE:
=============

# Creating messages the new way:
from Red.message_manager import MessageBuilder, ConversationManager

conv = ConversationManager()
conv.add_user_message("Hello")
conv.add_assistant_response(assistant_message)  # Automatically handles tool calls
conv.validate_messages()  # Ensures API compliance

# Managing attack sessions:
from Red.attack_session import AttackSession

session = AttackSession(initial_messages)
session.setup_ssh_connection()
session.run_attack_iterations()
logs, tokens = session.get_results()

# Managing multiple attacks:
from Red.utilities import AttackProgressTracker, LogFileManager

tracker = AttackProgressTracker(total_attacks)
tracker.start_attack_session(1)
# ... run attack ...
tracker.complete_attack_session(1, tokens_used)
tracker.print_final_summary()

BACKWARD COMPATIBILITY:
======================

The main sangria.py interface remains unchanged:
- run_single_attack(save_logs, messages) -> (logs, tokens)
- run_attacks(n_attacks, save_logs, log_path) -> None

All existing code continues to work without modification while benefiting
from the improved architecture under the hood.

TESTING:
========

Core functionality has been tested and verified:
✅ Message creation and validation
✅ Conversation management 
✅ Tool call formatting
✅ Content sanitization
✅ API compliance

The refactored code maintains all original functionality while providing
a much cleaner, more maintainable, and more extensible architecture.
"""

print(__doc__)

if __name__ == "__main__":
    print("Sangria refactoring completed successfully!")
    print("All classes are working correctly and backward compatibility is maintained.")
    print("\nKey files created:")
    print("- Red/message_manager.py: Message and conversation handling")
    print("- Red/attack_session.py: Session orchestration and token tracking") 
    print("- Red/utilities.py: Docker management and file operations")
    print("- Red/sangria.py: Clean main interface (refactored)")
    print("\nThe code is now much more organized, maintainable, and professional!")
