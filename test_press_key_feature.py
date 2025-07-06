#!/usr/bin/env python3
"""
Test script for the "press key" during dictation feature
"""

import asyncio
import logging
import sys
from src.voice_recognition import VoiceRecognizer
from src.command_processor import CommandProcessor
from src.keystroke_manager import KeystrokeManager
from src.config import Config

def setup_logging():
    """Setup logging for testing"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

async def test_press_key_during_dictation():
    """Test the press key functionality during dictation"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("🧪 Testing 'Press Key' during dictation feature")
    
    try:
        # Initialize components
        config = Config('config.yaml')
        voice_recognizer = VoiceRecognizer(config)
        keystroke_manager = KeystrokeManager()
        command_processor = CommandProcessor(config, keystroke_manager)
        
        # Enable dictation mode
        command_processor.dictation_mode = True
        logger.info("✅ Dictation mode enabled")
        
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
        ]
        
        logger.info("🎯 Testing press key command detection...")
        
        for i, test_text in enumerate(test_cases, 1):
            logger.info(f"\n--- Test Case {i}: '{test_text}' ---")
            
            # Test the _check_press_key_commands method directly
            is_key_command = await command_processor._check_press_key_commands(test_text)
            
            if is_key_command:
                logger.info(f"✅ Detected as KEY COMMAND: '{test_text}'")
            else:
                logger.info(f"📝 Detected as DICTATION TEXT: '{test_text}'")
                # Simulate typing the text (but don't actually type it during test)
                logger.info(f"   Would type: '{test_text} '")
        
        logger.info("\n🎉 Press key detection test completed!")
        
        # Test pattern matching
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
        ]
        
        for text, expected in patterns_to_test:
            result = await command_processor._check_press_key_commands(text)
            status = "✅" if result == expected else "❌"
            logger.info(f"{status} '{text}' -> Expected: {expected}, Got: {result}")
        
        logger.info("\n🚀 All tests completed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_press_key_during_dictation())
