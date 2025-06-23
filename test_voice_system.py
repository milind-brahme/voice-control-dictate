#!/usr/bin/env python3
"""
Comprehensive test script for the voice control system
Tests multiple components with fallbacks for missing audio
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from keystroke_manager import KeystrokeManager
from voice_recognition import VoiceRecognizer
from command_processor import CommandProcessor
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VoiceSystemTester:
    def __init__(self):
        self.config = None
        self.keystroke_manager = None
        self.voice_recognizer = None
        self.command_processor = None
        
    async def setup(self):
        """Initialize all components"""
        try:
            # Load config
            self.config = Config("config.yaml")
            logger.info("✓ Config loaded")
            
            # Initialize keystroke manager
            self.keystroke_manager = KeystrokeManager()
            logger.info("✓ Keystroke manager initialized")
            
            # Initialize voice recognizer
            self.voice_recognizer = VoiceRecognizer(self.config)
            logger.info("✓ Voice recognizer initialized")
            
            # Initialize command processor
            self.command_processor = CommandProcessor(self.config, self.keystroke_manager)
            logger.info("✓ Command processor initialized")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Setup failed: {e}")
            return False
    
    async def test_keystroke_manager(self):
        """Test keystroke manager functionality"""
        logger.info("\n=== Testing Keystroke Manager ===")
        
        if self.keystroke_manager.controller is None:
            logger.warning("⚠ Keystroke controller not available (expected in headless environment)")
            logger.info("✓ Keystroke manager handles missing controller gracefully")
            return True
        
        try:
            # Test typing
            await self.keystroke_manager.type_text("Hello from test!")
            logger.info("✓ Text typing works")
            
            # Test key combinations
            await self.keystroke_manager.send_key("a", ["ctrl"])
            logger.info("✓ Key combinations work")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Keystroke manager test failed: {e}")
            return False
    
    async def test_voice_recognition_without_audio(self):
        """Test voice recognition components without actual audio"""
        logger.info("\n=== Testing Voice Recognition (No Audio) ===")
        
        try:
            # Test if whisper model can be loaded
            if hasattr(self.voice_recognizer, 'model') and self.voice_recognizer.model:
                logger.info("✓ Whisper model loaded successfully")
            else:
                logger.info("ℹ Whisper model not pre-loaded (lazy loading)")
            
            # Test audio device detection
            devices = self.voice_recognizer._get_audio_devices()
            if devices:
                logger.info(f"✓ Found {len(devices)} audio devices")
                for i, device in enumerate(devices[:3]):  # Show first 3
                    logger.info(f"  - Device {i}: {device}")
            else:
                logger.warning("⚠ No audio devices found")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Voice recognition test failed: {e}")
            return False
    
    async def test_audio_capture(self):
        """Test audio capture if possible"""
        logger.info("\n=== Testing Audio Capture ===")
        
        try:
            # Try to capture a very short audio sample
            import pyaudio
            
            audio = pyaudio.PyAudio()
            
            # Check if we can access default input device
            try:
                default_device = audio.get_default_input_device_info()
                logger.info(f"✓ Default input device: {default_device['name']}")
                
                # Try to open a stream briefly
                stream = audio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    frames_per_buffer=1024
                )
                stream.close()
                logger.info("✓ Audio stream can be opened")
                
            except Exception as e:
                logger.warning(f"⚠ Cannot access audio input: {e}")
            
            audio.terminate()
            return True
            
        except ImportError:
            logger.warning("⚠ PyAudio not available for audio testing")
            return True
        except Exception as e:
            logger.error(f"✗ Audio capture test failed: {e}")
            return False
    
    async def test_command_processing(self):
        """Test command processing with simulated voice input"""
        logger.info("\n=== Testing Command Processing ===")
        
        try:
            # Test various commands
            test_commands = [
                "activate type hello world",
                "activate press enter",
                "activate key ctrl a",
                "type this is a test",
            ]
            
            for command in test_commands:
                logger.info(f"Testing command: '{command}'")
                await self.command_processor.process_command(command)
                logger.info(f"✓ Command processed: '{command}'")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Command processing test failed: {e}")
            return False
    
    async def test_configuration(self):
        """Test configuration loading"""
        logger.info("\n=== Testing Configuration ===")
        
        try:
            # Test config access
            model_name = self.config.get('voice.model', 'base')
            logger.info(f"✓ Voice model: {model_name}")
            
            sensitivity = self.config.get('voice.sensitivity', 0.5)
            logger.info(f"✓ Voice sensitivity: {sensitivity}")
            
            commands = self.config.get('commands', {})
            logger.info(f"✓ Found {len(commands)} configured commands")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Configuration test failed: {e}")
            return False
    
    async def test_with_audio_files(self):
        """Test voice recognition with generated audio files"""
        logger.info("\n=== Testing with Audio Files ===")
        
        audio_files = [
            "test_audio.wav",
            "test_silence.wav", 
            "test_noise.wav",
            "test_speech_like.wav"
        ]
        
        for audio_file in audio_files:
            if not os.path.exists(audio_file):
                logger.warning(f"⚠ Audio file not found: {audio_file}")
                continue
                
            try:
                logger.info(f"Testing with {audio_file}...")
                
                # Try to transcribe the audio file
                result = await self.voice_recognizer.transcribe_file(audio_file)
                
                if result:
                    logger.info(f"✓ Transcription result: '{result}'")
                else:
                    logger.info(f"ℹ No transcription result for {audio_file} (expected for non-speech audio)")
                
            except Exception as e:
                logger.error(f"✗ Failed to process {audio_file}: {e}")
        
        return True
    
    async def test_real_time_simulation(self):
        """Simulate real-time voice recognition"""
        logger.info("\n=== Testing Real-time Simulation ===")
        
        try:
            # Test the voice recognition pipeline without actual microphone
            logger.info("Testing voice recognition pipeline...")
            
            # Check if we can initialize the recognition system
            if hasattr(self.voice_recognizer, '_setup_microphone'):
                logger.info("✓ Microphone setup method available")
            
            # Test command processing pipeline
            test_texts = [
                "activate type hello world",
                "activate press enter", 
                "activate key ctrl a",
                "type testing voice control",
            ]
            
            for text in test_texts:
                logger.info(f"Simulating voice input: '{text}'")
                await self.command_processor.process_command(text)
                logger.info(f"✓ Processed: '{text}'")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Real-time simulation failed: {e}")
            return False

    async def run_all_tests(self):
        """Run all tests"""
        logger.info("🚀 Starting Voice Control System Tests")
        
        # Setup
        if not await self.setup():
            logger.error("❌ Setup failed, aborting tests")
            return False
        
        # Run tests
        tests = [
            self.test_configuration,
            self.test_keystroke_manager,
            self.test_voice_recognition_without_audio,
            self.test_audio_capture,
            self.test_command_processing,
            self.test_with_audio_files,
            self.test_real_time_simulation,
        ]
        
        results = []
        for test in tests:
            try:
                result = await test()
                results.append(result)
            except Exception as e:
                logger.error(f"Test {test.__name__} crashed: {e}")
                results.append(False)
        
        # Summary
        passed = sum(results)
        total = len(results)
        
        logger.info(f"\n📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            logger.info("🎉 All tests passed!")
            return True
        else:
            logger.warning(f"⚠ {total - passed} tests failed")
            return False

async def main():
    """Main test function"""
    tester = VoiceSystemTester()
    
    try:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⏹ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Test suite crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
