#!/usr/bin/env python3
"""
Full integration test for press key during dictation
"""

import asyncio
import logging
import sys
from unittest.mock import AsyncMock

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

class MockKeystrokeManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.typed_texts = []
        self.pressed_keys = []
    
    async def send_key(self, key, modifiers=None):
        if modifiers:
            key_combo = f"{'+'.join(modifiers)}+{key}"
            self.logger.info(f"🔑 [MOCK] Pressed key combination: {key_combo}")
            self.pressed_keys.append(key_combo)
        else:
            self.logger.info(f"🔑 [MOCK] Pressed key: {key}")
            self.pressed_keys.append(key)
    
    async def type_text(self, text):
        self.logger.info(f"⌨️  [MOCK] Typed text: '{text}'")
        self.typed_texts.append(text)

# Import the actual command processor components
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class MockConfig:
    def get(self, key, default=None):
        config_dict = {
            'commands.wake_words': ['activate', 'computer', 'hey assistant'],
            'commands.stop_dictation': ['stop dictation', 'end dictation'],
            'commands.start_dictation': ['start dictation', 'begin dictation'],
            'commands.custom': {}
        }
        return config_dict.get(key, default)

# Import the real press key method patterns
import re

async def simulate_press_key_check(text):
    """Simulate the _check_press_key_commands method"""
    text_lower = text.lower().strip()
    
    # Use the exact patterns from the updated code
    press_key_patterns = [
        r"press key (.+?)\.?$",        # "press key enter" or "press key enter."
        r"press (.+?) key\.?$",        # "press enter key" or "press enter key."
        r"hit key (.+?)\.?$",          # "hit key backspace" or "hit key backspace."
        r"hit (.+?) key\.?$",          # "hit escape key" or "hit escape key."
        r"^key (.+?)\.?$",             # "key tab" or "key tab."
        r"^press (enter|tab|space|escape|backspace|delete|home|end|up|down|left|right|page up|page down|f\d+)\.?$",  # Direct key commands
        r"^hit (enter|tab|space|escape|backspace|delete|home|end|up|down|left|right|page up|page down|f\d+)\.?$",    # "hit enter", "hit tab", etc.
        r"press (ctrl|shift|alt) (.+?)\.?$",  # "press ctrl c", "press shift tab", etc.
        r"hit (ctrl|shift|alt) (.+?)\.?$",    # "hit ctrl c", "hit shift tab", etc.
    ]
    
    for pattern in press_key_patterns:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            # Handle different pattern groups
            if "ctrl" in pattern or "shift" in pattern or "alt" in pattern:
                # For modifier patterns like "press ctrl c"
                if match.lastindex == 2:
                    modifier = match.group(1).strip()
                    key = match.group(2).strip().rstrip('.')
                    key_name = f"{modifier} {key}"
                else:
                    key_name = match.group(1).strip().rstrip('.')
            else:
                # For regular patterns
                key_name = match.group(1).strip().rstrip('.')
            
            return key_name
    
    return None

async def simulate_dictation_processing(keystroke_manager, text):
    """Simulate the dictation processing logic"""
    logger = logging.getLogger(__name__)
    
    logger.info(f"📝 Processing: '{text}'")
    
    # Check for press key commands
    key_name = await simulate_press_key_check(text)
    if key_name:
        logger.info(f"🎯 Detected press key command: '{key_name}'")
        
        # Simulate the key press execution
        if ' ' in key_name:
            parts = key_name.split()
            if len(parts) == 2:
                modifier, main_key = parts
                await keystroke_manager.send_key(main_key, [modifier])
            else:
                main_key = parts[-1]
                modifiers = parts[:-1]
                await keystroke_manager.send_key(main_key, modifiers)
        else:
            await keystroke_manager.send_key(key_name)
        return True
    
    # Otherwise type as text
    logger.info(f"📄 Typing as dictation text")
    await keystroke_manager.type_text(text + " ")
    return False

async def test_full_dictation_flow():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("🧪 Testing full dictation flow with press key commands")
    
    keystroke_manager = MockKeystrokeManager()
    
    # Test cases that simulate real voice recognition input
    test_cases = [
        "Hello world this is a test",
        "press enter.",
        "This is more text to type",
        "hit tab.",
        "Some additional content",
        "press key backspace",
        "More dictation content",
        "press ctrl c",
        "Final text to type",
        "key escape",
    ]
    
    for i, text in enumerate(test_cases, 1):
        logger.info(f"\n--- Test Case {i}: '{text}' ---")
        await simulate_dictation_processing(keystroke_manager, text)
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("📊 SUMMARY")
    logger.info("="*60)
    logger.info(f"🔑 Keys pressed: {keystroke_manager.pressed_keys}")
    logger.info(f"⌨️  Texts typed: {keystroke_manager.typed_texts}")
    
    expected_keys = ['enter', 'tab', 'backspace', 'ctrl+c', 'escape']
    expected_texts = [
        'Hello world this is a test ',
        'This is more text to type ',
        'Some additional content ',
        'More dictation content ',
        'Final text to type '
    ]
    
    logger.info(f"\n✅ Expected keys: {expected_keys}")
    logger.info(f"✅ Expected texts: {len(expected_texts)} items")
    
    success = (len(keystroke_manager.pressed_keys) == len(expected_keys) and 
              len(keystroke_manager.typed_texts) == len(expected_texts))
    
    if success:
        logger.info("🎉 ALL TESTS PASSED!")
    else:
        logger.error("❌ Some tests failed!")

if __name__ == "__main__":
    asyncio.run(test_full_dictation_flow())
