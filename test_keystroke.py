#!/usr/bin/env python3
"""
Simple test script to verify keystroke functionality
"""

import asyncio
import logging
from src.keystroke_manager import KeystrokeManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_keystroke_manager():
    """Test the keystroke manager functionality"""
    logger.info("Testing KeystrokeManager...")
    
    try:
        # Initialize the keystroke manager
        keystroke_manager = KeystrokeManager()
        logger.info(f"KeystrokeManager initialized for platform: {keystroke_manager.system}")
        
        # Check if controller is available
        if keystroke_manager.controller is None:
            logger.warning("Controller not available - this is expected in headless environments")
            logger.info("KeystrokeManager created successfully but cannot control input devices")
            return True
        
        # Test typing some text
        test_text = "Hello, this is a test from the voice control system!"
        logger.info(f"Attempting to type: {test_text}")
        
        # Give user time to focus on an empty file
        logger.info("Please focus on an empty text file/editor within 5 seconds...")
        await asyncio.sleep(5)
        
        # Type the test text
        await keystroke_manager.type_text(test_text)
        logger.info("Text typing completed successfully!")
        
        # Test sending special keys
        await asyncio.sleep(1)
        await keystroke_manager.send_key("enter")
        await keystroke_manager.type_text("This is on a new line!")
        
        # Test key combination
        await asyncio.sleep(1)
        await keystroke_manager.send_key("a", modifiers=["ctrl"])  # Select all
        
        logger.info("Keystroke test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False

async def main():
    """Main test function"""
    logger.info("Starting keystroke functionality test...")
    
    success = await test_keystroke_manager()
    
    if success:
        logger.info("✅ Test completed successfully!")
    else:
        logger.error("❌ Test failed!")
        
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
