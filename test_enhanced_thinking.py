#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced thinking process in the LLM output.
This test shows the difference between the original and enhanced prompts.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Red.enhanced_prompts import get_enhanced_prompt
import Red.attacker_prompts as original_prompts

def main():
    print("=" * 70)
    print("ENHANCED THINKING PROCESS TEST")
    print("=" * 70)
    
    print("\n1. ORIGINAL PROMPT (first 300 chars):")
    print("-" * 50)
    print(original_prompts.general[:300] + "...")
    
    print("\n2. ENHANCED PROMPT (first 500 chars):")
    print("-" * 50)
    enhanced = get_enhanced_prompt("general")
    print(enhanced[:500] + "...")
    
    print("\n3. KEY DIFFERENCES:")
    print("-" * 50)
    
    # Check for thinking process requirements
    thinking_requirements = [
        "ALWAYS EXPLAIN YOUR REASONING FIRST",
        "🧠 **Current Analysis:**",
        "🎯 **Next Step Plan:**",
        "🔍 **Rationale:**",
        "Before using any tool, you MUST:"
    ]
    
    for req in thinking_requirements:
        in_enhanced = req in enhanced
        in_original = req in original_prompts.general
        status = "✅ ADDED" if in_enhanced and not in_original else "❌ MISSING"
        print(f"{status}: {req}")
    
    print("\n4. EXPECTED BEHAVIOR:")
    print("-" * 50)
    print("With the enhanced prompt, the LLM should:")
    print("• Provide detailed analysis before each action")
    print("• Use the structured response format with emojis")
    print("• Explain reasoning before using tools")
    print("• Show step-by-step thinking process")
    
    print("\n5. CONFIGURATION STATUS:")
    print("-" * 50)
    try:
        from Red.sangria_config import attacker_prompt
        if "ALWAYS EXPLAIN YOUR REASONING FIRST" in attacker_prompt:
            print("✅ Enhanced prompt is ACTIVE in sangria_config.py")
        else:
            print("❌ Original prompt is still being used in sangria_config.py")
    except Exception as e:
        print(f"❌ Error checking configuration: {e}")
    
    print("\n" + "=" * 70)
    print("To see the enhanced thinking in action:")
    print("1. Run: python main.py")
    print("2. Watch for structured reasoning before each tool call")
    print("3. Look for 🧠 🎯 🔍 emojis in the output")
    print("=" * 70)

if __name__ == "__main__":
    main()
