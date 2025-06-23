#!/usr/bin/env python3
"""
Voice Control and Dictation System
Main entry point for the application
"""

import asyncio
import argparse
import sys
import logging
from pathlib import Path

from src.voice_recognition import VoiceRecognizer
from src.command_processor import CommandProcessor
from src.keystroke_manager import KeystrokeManager
from src.config import Config
from src.gui import VoiceControlGUI

def setup_logging(log_level="INFO"):
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('voice_control.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

async def main():
    parser = argparse.ArgumentParser(description='Voice Control and Dictation System')
    parser.add_argument('--mode', choices=['gui', 'cli'], default='gui',
                       help='Run in GUI or CLI mode')
    parser.add_argument('--config', type=str, default='config.yaml',
                       help='Configuration file path')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Logging level')
    parser.add_argument('--dictation-mode', action='store_true',
                       help='Start in dictation mode')
    
    args = parser.parse_args()
    
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration
        config = Config(args.config)
        
        # Initialize components
        voice_recognizer = VoiceRecognizer(config)
        keystroke_manager = KeystrokeManager()
        command_processor = CommandProcessor(config, keystroke_manager)
        
        if args.mode == 'gui':
            # Run GUI mode
            gui = VoiceControlGUI(voice_recognizer, command_processor, config)
            await gui.run()
        else:
            # Run CLI mode
            logger.info("Starting Voice Control System in CLI mode")
            
            if args.dictation_mode:
                await run_dictation_mode(voice_recognizer, keystroke_manager)
            else:
                await run_command_mode(voice_recognizer, command_processor)
                
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)

async def run_dictation_mode(voice_recognizer, keystroke_manager):
    """Run in continuous dictation mode"""
    logger = logging.getLogger(__name__)
    logger.info("Starting dictation mode. Press Ctrl+C to stop.")
    
    try:
        async for text in voice_recognizer.continuous_recognition():
            if text.strip():
                logger.info(f"Dictating: {text}")
                await keystroke_manager.type_text(text)
    except KeyboardInterrupt:
        logger.info("Dictation mode stopped by user")

async def run_command_mode(voice_recognizer, command_processor):
    """Run in command recognition mode"""
    logger = logging.getLogger(__name__)
    logger.info("Starting command mode. Say 'activate' followed by your command.")
    
    try:
        async for text in voice_recognizer.continuous_recognition():
            if text.strip():
                await command_processor.process_command(text)
    except KeyboardInterrupt:
        logger.info("Command mode stopped by user")

if __name__ == "__main__":
    asyncio.run(main())