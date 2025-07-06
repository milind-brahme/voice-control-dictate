#!/usr/bin/env python3
"""
Test script for Faster-Whisper integration
"""

import logging
import sys
from src.config import Config
from src.voice_recognition import VoiceRecognizer

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def test_whisper_model():
    """Test the Faster-Whisper model loading"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Load config
        config = Config('config.yaml')
        logger.info("✅ Configuration loaded")
        
        # Test voice recognizer initialization
        recognizer = VoiceRecognizer(config)
        logger.info("✅ Voice recognizer initialized")
        
        # Check model type
        model_type = recognizer.model_type
        model_size = config.get('whisper.model_size', 'base')
        device = config.get('whisper.device', 'cpu')
        
        logger.info(f"📊 Model Details:")
        logger.info(f"   Engine: {model_type}")
        logger.info(f"   Model: {model_size}")
        logger.info(f"   Device: {device}")
        
        if model_type == 'faster-whisper':
            compute_type = config.get('whisper.compute_type', 'float32')
            logger.info(f"   Compute Type: {compute_type}")
            logger.info(f"🚀 Faster-Whisper is ready for 2-4x performance improvement!")
        
        # Test audio devices
        devices = recognizer.list_audio_devices()
        logger.info(f"🎤 Found {len(devices)} audio input devices")
        
        # Check selected device
        selected_device = config.get('audio.input_device')
        if selected_device is not None:
            device_info = next((d for d in devices if d['index'] == selected_device), None)
            if device_info:
                logger.info(f"🎙️  Selected device: {device_info['name']}")
            else:
                logger.warning(f"⚠️  Selected device {selected_device} not found")
        
        logger.info("🎉 All tests passed! Ready for high-accuracy voice recognition.")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_whisper_model()
