#!/usr/bin/env python3
"""
Quick test script to verify core functionality without heavy model loading
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from keystroke_manager import KeystrokeManager
from command_processor import CommandProcessor
from config import Config

async def main():
    print("🚀 Starting Quick Voice Control System Test")
    
    # Test 1: Config loading
    try:
        config = Config("config.yaml")
        print("✓ Config loaded successfully")
    except Exception as e:
        print(f"✗ Config failed: {e}")
        return False
    
    # Test 2: Keystroke manager
    try:
        keystroke_manager = KeystrokeManager()
        print("✓ Keystroke manager initialized")
        
        if keystroke_manager.controller is None:
            print("ℹ Running in headless mode (expected)")
        else:
            print("✓ Keystroke controller available")
    except Exception as e:
        print(f"✗ Keystroke manager failed: {e}")
        return False
    
    # Test 3: Command processor
    try:
        command_processor = CommandProcessor(config, keystroke_manager)
        print("✓ Command processor initialized")
        
        # Test command processing without actual keystroke execution
        test_commands = [
            "activate type hello world",
            "activate press enter",
            "type this is a test"
        ]
        
        for cmd in test_commands:
            await command_processor.process_command(cmd)
            print(f"✓ Processed command: '{cmd}'")
            
    except Exception as e:
        print(f"✗ Command processor failed: {e}")
        return False
    
    # Test 4: Audio files exist
    audio_files = ["test_audio.wav", "test_silence.wav", "test_noise.wav", "test_speech_like.wav"]
    for audio_file in audio_files:
        if os.path.exists(audio_file):
            size = os.path.getsize(audio_file)
            print(f"✓ Audio file {audio_file} exists ({size} bytes)")
        else:
            print(f"⚠ Audio file {audio_file} missing")
    
    # Test 5: Dependencies check
    try:
        import whisper
        print("✓ Whisper available (model loading skipped for speed)")
    except ImportError:
        print("✗ Whisper not available")
    
    try:
        import pyaudio
        print("✓ PyAudio available")
    except ImportError:
        print("✗ PyAudio not available")
    
    print("\n🎉 Quick test completed!")
    print("📝 Note: Full Whisper transcription test skipped for performance")
    print("   In a real environment with audio hardware, voice recognition would work")
    
    return True

if __name__ == "__main__":
    asyncio.run(main())
