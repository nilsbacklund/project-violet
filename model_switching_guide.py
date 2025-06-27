"""
QUICK MODEL SWITCHING GUIDE
===========================

This guide shows how to easily switch between different OpenAI models
for different use cases while maintaining full functionality.

AVAILABLE MODELS:
================

1. O3_MINI (Current Default)
   - Best for: Complex reasoning, attack planning
   - Speed: Slower but more thorough
   - Cost: Higher but more capable
   - Use when: You need the best attack simulation quality

2. GPT_4_1_MINI (Recommended Alternative) 
   - Best for: Fast iteration, testing, development
   - Speed: Much faster responses
   - Cost: More economical
   - Use when: You're testing or developing features

3. O4_MINI
   - Best for: Cost-sensitive operations
   - Speed: Fast
   - Cost: Most economical
   - Use when: Budget is the primary concern

HOW TO SWITCH MODELS:
====================

Method 1: Edit config.py directly
---------------------------------
1. Open /Users/nilsbacklund/Documents/Jobb/AISweden/project-violet/config.py
2. Change these lines:

   FROM:
   llm_model_sangria = LLMModel.O3_MINI
   llm_model_config = LLMModel.O3_MINI

   TO:  
   llm_model_sangria = LLMModel.GPT_4_1_MINI
   llm_model_config = LLMModel.GPT_4_1_MINI

3. Save the file
4. Run your attack: python3 main.py

Method 2: Programmatic switching
--------------------------------
You can also switch models in code:

```python
# At the top of your script
import config
from Red.model import LLMModel

# Switch to GPT_4_1_MINI
config.llm_model_sangria = LLMModel.GPT_4_1_MINI
config.llm_model_config = LLMModel.GPT_4_1_MINI

# Or switch to O4_MINI for cost savings
config.llm_model_sangria = LLMModel.O4_MINI
config.llm_model_config = LLMModel.O4_MINI
```

ENHANCED OUTPUT FEATURES:
========================

With the new enhanced output, you'll see:

✅ THINKING PROCESS: The LLM's reasoning is displayed clearly
✅ TOOL CALLS: Function calls and arguments are formatted nicely  
✅ TOOL RESPONSES: Command outputs are organized and readable
✅ PROGRESS TRACKING: Clear iteration summaries and progress indicators
✅ TOKEN USAGE: Detailed cost tracking with formatted numbers
✅ ATTACK RESULTS: Professional success/failure reporting
✅ MITRE MAPPING: Security technique identification
✅ FINAL SUMMARY: Comprehensive session overview

COMPATIBILITY NOTES:
====================

All models support:
• Function calling and tool use
• The same API interface
• Full conversation history
• Token usage tracking
• Log saving functionality

The enhanced output works with ALL models - you get the same
professional formatting regardless of which model you choose.

QUICK TEST:
==========

To test model switching:

1. Edit config.py to use GPT_4_1_MINI
2. Run: python3 test_enhanced_output.py
3. Check that it shows the new model
4. Run: python3 main.py (with a small test configuration)
5. Observe the enhanced output format

TROUBLESHOOTING:
===============

If you get model errors:
• Check that your OpenAI API key has access to the model
• Some newer models may have restricted access
• GPT_4_1_MINI is widely available and a safe fallback
• Check the OpenAI API documentation for model availability

PERFORMANCE COMPARISON:
======================

For typical attack sessions:

O3_MINI:
- Response time: 5-15 seconds per iteration
- Quality: Highest reasoning quality
- Cost: ~2-3x more tokens than GPT_4_1_MINI

GPT_4_1_MINI:
- Response time: 1-3 seconds per iteration  
- Quality: Very good, sufficient for most tasks
- Cost: Most economical option

Choose based on your priorities: quality vs speed vs cost.
"""

if __name__ == "__main__":
    print(__doc__)
    
    # Show current configuration
    try:
        import config
        print("CURRENT CONFIGURATION:")
        print("=" * 30)
        print(f"Sangria model: {config.llm_model_sangria}")
        print(f"Config model: {config.llm_model_config}")
        print(f"Print output: {config.print_output}")
        print(f"Save logs: {config.save_logs}")
        print(f"Simulate command line: {config.simulate_command_line}")
        
        print(f"\nTo switch to GPT_4_1_MINI, edit config.py and change:")
        print(f"llm_model_sangria = LLMModel.GPT_4_1_MINI")
        print(f"llm_model_config = LLMModel.GPT_4_1_MINI")
        
    except ImportError:
        print("Could not load current configuration")
        print("Make sure you're in the project directory")
