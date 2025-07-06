#!/usr/bin/env python3
"""
Test script for custom dictation commands
"""

import asyncio
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.config import Config
from src.command_processor import CommandProcessor
from src.keystroke_manager import KeystrokeManager

async def test_custom_dictation():
    """Test custom dictation commands"""
    
    # Load configuration
    config = Config()
    
    # Initialize keystroke manager and command processor
    keystroke_manager = KeystrokeManager()
    processor = CommandProcessor(config, keystroke_manager)
    
    print("=== Custom Dictation Commands Test ===")
    print(f"Dictation mode: {processor.dictation_mode}")
    
    # Start dictation mode
    await processor._start_dictation()
    print(f"Started dictation mode: {processor.dictation_mode}")
    
    # List custom commands
    print("\n=== Registered Custom Commands ===")
    custom_commands = [cmd for cmd in processor.commands.values() 
                      if cmd.category in ['custom', 'dictation']]
    
    for cmd in custom_commands:
        print(f"Command: {cmd.name}")
        print(f"  Category: {cmd.category}")
        print(f"  Description: {cmd.description}")
        print(f"  Patterns: {cmd.patterns}")
        print(f"  Handler: {cmd.handler}")
        print()
    
    # Test custom command detection
    print("=== Testing Custom Command Detection ===")
    test_phrases = [
        "insert signature",
        "email signature", 
        "insert my address",
        "meeting introduction",
        "hello world this is regular dictation",
        "insert signature please"
    ]
    
    for phrase in test_phrases:
        print(f"\nTesting phrase: '{phrase}'")
        is_custom = await processor._check_custom_commands_in_dictation(phrase)
        print(f"  Custom command detected: {is_custom}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_custom_dictation())
