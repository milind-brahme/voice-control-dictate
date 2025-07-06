#!/usr/bin/env python3
"""
Debug script to test actual voice recognition and press key detection
"""

import asyncio
import logging
import sys
import re

def setup_logging():
    """Setup logging for debugging"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

async def debug_press_key_detection():
    """Debug the press key detection with actual input examples"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("🔍 Debugging press key detection...")
    
    # Test the actual text that was typed
    problematic_texts = [
        "press enter.",
        "hit tab.",
        "enter.",
        "press enter",
        "hit tab", 
        "enter",
        "press key enter",
        "press key enter.",
        "Press Enter",
        "PRESS ENTER",
        "press enter key",
        "hit key backspace",
    ]
    
    # Define the patterns used in the actual code
    press_key_patterns = [
        r"^press key (.+)$",           # "press key enter"
        r"^press (.+) key$",           # "press enter key"  
        r"^hit key (.+)$",             # "hit key backspace"
        r"^hit (.+) key$",             # "hit escape key"
        r"^key (.+)$",                 # "key tab" (only if it's the whole phrase)
        r"^press (enter|tab|space|escape|backspace|delete|home|end|up|down|left|right|ctrl \w+|shift \w+|alt \w+)$"  # Specific keys only
    ]
    
    for text in problematic_texts:
        logger.info(f"\n--- Testing: '{text}' ---")
        text_lower = text.lower().strip()
        logger.info(f"Processed text: '{text_lower}'")
        
        found_match = False
        for i, pattern in enumerate(press_key_patterns):
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                key_name = match.group(1).strip()
                logger.info(f"✅ MATCH found with pattern {i+1}: '{pattern}' -> key: '{key_name}'")
                found_match = True
                break
        
        if not found_match:
            logger.info(f"❌ NO MATCH found for '{text_lower}'")
    
    # Test with better patterns that handle punctuation
    logger.info("\n🔧 Testing improved patterns...")
    
    improved_patterns = [
        r"press key (.+?)\.?$",        # "press key enter" or "press key enter."
        r"press (.+?) key\.?$",        # "press enter key" or "press enter key."
        r"hit key (.+?)\.?$",          # "hit key backspace" or "hit key backspace."
        r"hit (.+?) key\.?$",          # "hit escape key" or "hit escape key."
        r"^key (.+?)\.?$",             # "key tab" or "key tab."
        r"^press (enter|tab|space|escape|backspace|delete|home|end|up|down|left|right)\.?$"  # Direct key commands
    ]
    
    for text in problematic_texts:
        logger.info(f"\n--- Testing improved patterns for: '{text}' ---")
        text_lower = text.lower().strip()
        
        found_match = False
        for i, pattern in enumerate(improved_patterns):
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                if match.lastindex and match.lastindex >= 1:
                    key_name = match.group(1).strip()
                    logger.info(f"✅ IMPROVED MATCH with pattern {i+1}: '{pattern}' -> key: '{key_name}'")
                    found_match = True
                    break
        
        if not found_match:
            logger.info(f"❌ Still no match for '{text_lower}'")

if __name__ == "__main__":
    asyncio.run(debug_press_key_detection())
