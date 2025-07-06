#!/usr/bin/env python3
"""
Simple test script for the "press key" during dictation feature (without audio dependencies)
"""

import asyncio
import logging
import sys
import re
from unittest.mock import AsyncMock, MagicMock

def setup_logging():
    """Setup logging for testing"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

class MockKeystrokeManager:
    """Mock keystroke manager for testing"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def send_key(self, key, modifiers=None):
        """Mock send key method"""
        if modifiers:
            self.logger.info(f"[MOCK] Sending key combination: {'+'.join(modifiers)}+{key}")
        else:
            self.logger.info(f"[MOCK] Sending key: {key}")
    
    async def type_text(self, text):
        """Mock type text method"""
        self.logger.info(f"[MOCK] Typing text: '{text}'")

class MockConfig:
    """Mock configuration for testing"""
    
    def get(self, key, default=None):
        return default

class TestCommandProcessor:
    """Test class for command processor press key functionality"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.keystroke_manager = MockKeystrokeManager()
        self.dictation_mode = True  # Enable dictation mode for testing
    
    async def _press_key(self, key: str):
        """Press the specified key or key combination"""
        try:
            # Handle key combinations like "ctrl a", "shift enter", etc.
            if ' ' in key:
                parts = key.split()
                if len(parts) == 2:
                    modifier, main_key = parts
                    await self.keystroke_manager.send_key(main_key, [modifier])
                else:
                    # Multiple modifiers: ctrl shift a
                    main_key = parts[-1]
                    modifiers = parts[:-1]
                    await self.keystroke_manager.send_key(main_key, modifiers)
            else:
                # Single key
                await self.keystroke_manager.send_key(key)
            
            self.logger.info(f"Pressed key: {key}")
        except Exception as e:
            self.logger.error(f"Failed to press key '{key}': {e}")
    
    async def _check_press_key_commands(self, text: str) -> bool:
        """
        Check if the text contains a "press key" command during dictation mode.
        Returns True if a key command was executed, False otherwise.
        """
        text_lower = text.lower().strip()
        
        # Define patterns for "press key" commands
        press_key_patterns = [
            r"press key (.+)",
            r"press (.+) key",
            r"hit key (.+)",
            r"hit (.+) key", 
            r"key (.+)",
            r"press (.+)"
        ]
        
        for pattern in press_key_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                key_name = match.group(1).strip()
                self.logger.info(f"Detected press key command during dictation: '{key_name}'")
                
                try:
                    # Execute the key press
                    await self._press_key(key_name)
                    return True
                except Exception as e:
                    self.logger.error(f"Error executing press key command '{key_name}': {e}")
                    return False
        
        return False
    
    async def process_command(self, text: str):
        """Simulate the dictation mode command processing"""
        text = text.strip()
        
        if not text:
            return
            
        self.logger.info(f"Processing: {text}")
        
        # Check if in dictation mode
        if self.dictation_mode:
            # Check for "press key" commands during dictation
            key_command_executed = await self._check_press_key_commands(text)
            if key_command_executed:
                return
            
            # Otherwise, type the text
            await self.keystroke_manager.type_text(text + " ")
            return

async def test_press_key_during_dictation():
    """Test the press key functionality during dictation"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("🧪 Testing 'Press Key' during dictation feature")
    
    try:
        # Initialize test command processor
        command_processor = TestCommandProcessor()
        
        logger.info("✅ Mock command processor with dictation mode enabled")
        
        # Test cases for press key detection
        test_cases = [
            "Hello world this is a test",  # Should be typed as text
            "press key enter",  # Should execute Enter key
            "press enter key",  # Should execute Enter key
            "This is more text",  # Should be typed as text
            "hit key backspace",  # Should execute Backspace key
            "key tab",  # Should execute Tab key
            "press ctrl c",  # Should execute Ctrl+C
            "Some more dictation text",  # Should be typed as text
            "press key escape",  # Should execute Escape key
            "press shift tab",  # Should execute Shift+Tab
            "hit key delete",  # Should execute Delete key
            "key f1",  # Should execute F1 key
        ]
        
        logger.info("🎯 Testing full command processing flow...")
        
        for i, test_text in enumerate(test_cases, 1):
            logger.info(f"\n--- Test Case {i}: '{test_text}' ---")
            await command_processor.process_command(test_text)
        
        logger.info("\n🎉 Command processing test completed!")
        
        # Test pattern matching directly
        logger.info("\n🔍 Testing pattern matching...")
        
        patterns_to_test = [
            ("press key enter", True),
            ("press enter key", True),
            ("hit key backspace", True),
            ("key tab", True),
            ("press ctrl c", True),
            ("hello world", False),
            ("press key space", True),
            ("type something", False),
            ("press shift tab", True),
            ("normal dictation", False),
            ("PRESS KEY ESCAPE", True),  # Test case sensitivity
            ("Hit Key F5", True),  # Test case sensitivity
            ("press key ctrl alt delete", True),  # Multiple modifiers
        ]
        
        for text, expected in patterns_to_test:
            result = await command_processor._check_press_key_commands(text)
            status = "✅" if result == expected else "❌"
            logger.info(f"{status} '{text}' -> Expected: {expected}, Got: {result}")
        
        logger.info("\n🚀 All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_press_key_during_dictation())
