#!/usr/bin/env python3
"""
Test updated press key patterns
"""

import asyncio
import logging
import sys
import re

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

async def test_updated_patterns():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("🔧 Testing updated press key patterns...")
    
    # Updated patterns from the code
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
    
    test_cases = [
        "press enter.",      # Should match pattern 6
        "hit tab.",          # Should match pattern 7  
        "enter.",            # Should NOT match
        "press key enter",   # Should match pattern 1
        "press enter key",   # Should match pattern 2
        "hit key backspace", # Should match pattern 3
        "press ctrl c",      # Should match pattern 8
        "hit shift tab",     # Should match pattern 9
        "key escape",        # Should match pattern 5
        "some random text",  # Should NOT match
    ]
    
    for text in test_cases:
        logger.info(f"\n--- Testing: '{text}' ---")
        text_lower = text.lower().strip()
        
        found_match = False
        for i, pattern in enumerate(press_key_patterns):
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
                
                logger.info(f"✅ MATCH with pattern {i+1}: '{pattern}' -> key: '{key_name}'")
                found_match = True
                break
        
        if not found_match:
            logger.info(f"❌ NO MATCH for '{text_lower}'")

if __name__ == "__main__":
    asyncio.run(test_updated_patterns())
