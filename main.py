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
    parser.add_argument('--list-devices', action='store_true',
                       help='List available audio input devices and exit')
    parser.add_argument('--device', type=int, default=None,
                       help='Audio input device index to use')
    
    args = parser.parse_args()
    
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Handle device listing
    if args.list_devices:
        config = Config(args.config)
        recognizer = VoiceRecognizer(config)
        devices = recognizer.list_audio_devices()
        
        print("\n🎤 Available Audio Input Devices:")
        print("-" * 60)
        for device in devices:
            print(f"{device['index']:2d}: {device['name']}")
            print(f"    Channels: {device['channels']}, Sample Rate: {int(device['sample_rate'])} Hz")
        print("-" * 60)
        print("Use --device <number> to select a specific device")
        return
    
    try:
        # Load configuration
        config = Config(args.config)
        
        # Set audio device if specified
        if args.device is not None:
            config.set('audio.input_device', args.device)
            logger.info(f"Using audio device: {args.device}")
        
        # CLI device selection if in CLI mode and no device specified
        if args.mode == 'cli' and args.device is None:
            selected_device = await select_audio_device_cli(config)
            if selected_device is not None:
                config.set('audio.input_device', selected_device)
        
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
                # Enable dictation mode in command processor
                command_processor.dictation_mode = True
                await run_enhanced_dictation_mode(voice_recognizer, command_processor)
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

async def run_enhanced_dictation_mode(voice_recognizer, command_processor):
    """Run in enhanced dictation mode with press key command support"""
    logger = logging.getLogger(__name__)
    logger.info("Starting enhanced dictation mode with press key command support. Press Ctrl+C to stop.")
    logger.info("You can say 'press key enter', 'press tab', 'hit escape', etc. during dictation")
    
    try:
        async for text in voice_recognizer.continuous_recognition():
            if text.strip():
                logger.info(f"Processing: {text}")
                await command_processor.process_command(text)
    except KeyboardInterrupt:
        logger.info("Enhanced dictation mode stopped by user")

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

async def select_audio_device_cli(config):
    """CLI function to select audio device interactively"""
    
    try:
        recognizer = VoiceRecognizer(config)
        devices = recognizer.list_audio_devices()
        
        if not devices:
            print("❌ No audio input devices found!")
            return None
        
        print("\n🎤 Available Audio Input Devices:")
        print("-" * 60)
        for device in devices:
            print(f"{device['index']:2d}: {device['name']}")
            print(f"    Channels: {device['channels']}, Sample Rate: {int(device['sample_rate'])} Hz")
        print("-" * 60)
        
        # Auto-detect eMeet microphone
        emeet_device = None
        for device in devices:
            if 'emeet' in device['name'].lower() or 'm0' in device['name'].lower():
                emeet_device = device
                break
        
        if emeet_device:
            print(f"🎙️  eMeet microphone detected: {emeet_device['name']} (Device {emeet_device['index']})")
            response = input("Use eMeet microphone? (Y/n): ").strip().lower()
            if response in ['', 'y', 'yes']:
                return emeet_device['index']
        
        # Manual selection
        default_msg = "default device" if not emeet_device else f"eMeet device ({emeet_device['index']})"
        prompt = f"\nEnter device number (0-{len(devices)-1}) or press Enter for {default_msg}: "
        
        user_input = input(prompt).strip()
        
        if user_input == "":
            return emeet_device['index'] if emeet_device else None
        
        device_index = int(user_input)
        if 0 <= device_index < len(devices):
            selected_device = devices[device_index]
            print(f"✅ Selected: {selected_device['name']}")
            return device_index
        else:
            print(f"❌ Invalid device number. Using default.")
            return None
            
    except (ValueError, KeyboardInterrupt, Exception) as e:
        print(f"❌ Device selection error: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(main())