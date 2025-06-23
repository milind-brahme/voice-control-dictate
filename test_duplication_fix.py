#!/usr/bin/env python3
"""
Test script to verify the fix for the command duplication issue
where "activate press enter" was both pressing Enter and typing "enter"
"""

import asyncio
import logging
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from command_processor import CommandProcessor
from keystroke_manager import KeystrokeManager
from config import Config

class MockKeystrokeManager:
    """Mock keystroke manager to capture what would be typed/pressed"""
    
    def __init__(self):
        self.typed_text = []
        self.pressed_keys = []
        self.key_combinations = []
    
    async def type_text(self, text):
        self.typed_text.append(text)
        print(f"📝 Would TYPE: '{text}'")
    
    async def send_key(self, key, modifiers=None):
        if modifiers:
            combination = "+".join(modifiers + [key])
            self.key_combinations.append(combination)
            print(f"🔑 Would PRESS KEY COMBINATION: {combination}")
        else:
            self.pressed_keys.append(key)
            print(f"🔑 Would PRESS KEY: {key}")
    
    async def send_key_combination(self, combination):
        self.key_combinations.append(combination)
        print(f"🔑 Would PRESS KEY COMBINATION: {combination}")
    
    def reset(self):
        """Reset all captured actions"""
        self.typed_text.clear()
        self.pressed_keys.clear()
        self.key_combinations.clear()

async def test_command_duplication():
    """Test the specific issue where 'activate press enter' duplicates actions"""
    
    # Setup logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    print("🧪 Testing Command Duplication Fix")
    print("=" * 50)
    
    # Load config
    config = Config()
    
    # Create mock keystroke manager
    mock_keystroke = MockKeystrokeManager()
    
    # Create command processor
    command_processor = CommandProcessor(config, mock_keystroke)
    
    # Test cases
    test_cases = [
        {
            "input": "activate press enter",
            "expected_actions": 1,  # Should only press Enter, not type "enter"
            "description": "Press Enter key command"
        },
        {
            "input": "activate type hello world",
            "expected_actions": 1,  # Should only type the text
            "description": "Type text command"
        },
        {
            "input": "activate press ctrl a",
            "expected_actions": 1,  # Should only press Ctrl+A
            "description": "Press key combination command"
        },
        {
            "input": "activate copy",
            "expected_actions": 1,  # Should only execute copy command
            "description": "Simple command"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['description']}")
        print(f"   Input: '{test_case['input']}'")
        
        # Reset mock
        mock_keystroke.reset()
        
        # Process command
        await command_processor.process_command(test_case["input"])
        
        # Count total actions
        total_actions = (len(mock_keystroke.typed_text) + 
                        len(mock_keystroke.pressed_keys) + 
                        len(mock_keystroke.key_combinations))
        
        print(f"   Expected actions: {test_case['expected_actions']}")
        print(f"   Actual actions: {total_actions}")
        
        if total_actions == test_case['expected_actions']:
            print("   ✅ PASS")
        else:
            print("   ❌ FAIL")
            print(f"      Typed text: {mock_keystroke.typed_text}")
            print(f"      Pressed keys: {mock_keystroke.pressed_keys}")
            print(f"      Key combinations: {mock_keystroke.key_combinations}")
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")

if __name__ == "__main__":
    asyncio.run(test_command_duplication())
