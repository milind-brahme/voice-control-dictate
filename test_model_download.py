#!/usr/bin/env python3
"""
Test script to download and verify the large-v3 faster-whisper model
"""

import logging
import sys
import torch
from src.config import Config

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def test_faster_whisper_model():
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("🚀 Testing Faster-Whisper Large-v3 Model Download and Initialization")
    
    try:
        # Check CUDA availability
        cuda_available = torch.cuda.is_available()
        if cuda_available:
            gpu_name = torch.cuda.get_device_name(0)
            logger.info(f"✅ CUDA available: {gpu_name}")
        else:
            logger.warning("⚠️  CUDA not available, will use CPU")
        
        # Import faster-whisper
        try:
            from faster_whisper import WhisperModel
            logger.info("✅ Faster-Whisper imported successfully")
        except ImportError as e:
            logger.error(f"❌ Failed to import faster-whisper: {e}")
            logger.info("💡 Install it with: pip install faster-whisper")
            return False
        
        # Load configuration
        config = Config('config.yaml')
        
        # Get model settings from config
        model_size = config.get('whisper.model_size', 'large-v3')
        device = config.get('whisper.device', 'cuda' if cuda_available else 'cpu')
        compute_type = config.get('whisper.compute_type', 'float16')
        
        logger.info(f"📥 Downloading/Loading model: {model_size}")
        logger.info(f"🎯 Device: {device}")
        logger.info(f"🔧 Compute type: {compute_type}")
        
        # Initialize the model (this will download it if not cached)
        model = WhisperModel(
            model_size, 
            device=device, 
            compute_type=compute_type
        )
        
        logger.info("✅ Model loaded successfully!")
        
        # Test with a simple audio file or show model info
        logger.info("📊 Model Information:")
        logger.info(f"   - Model size: {model_size}")
        logger.info(f"   - Device: {device}")
        logger.info(f"   - Compute type: {compute_type}")
        
        # Check model memory usage
        if cuda_available:
            torch.cuda.empty_cache()
            memory_allocated = torch.cuda.memory_allocated() / 1024**3  # GB
            memory_reserved = torch.cuda.memory_reserved() / 1024**3   # GB
            logger.info(f"   - GPU Memory Allocated: {memory_allocated:.2f} GB")
            logger.info(f"   - GPU Memory Reserved: {memory_reserved:.2f} GB")
        
        logger.info("🎉 Large-v3 model is ready for use!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing model: {e}")
        return False

if __name__ == "__main__":
    success = test_faster_whisper_model()
    if success:
        print("\n✅ Model download and test completed successfully!")
        print("🚀 Your voice control system is now using the most accurate Whisper model!")
    else:
        print("\n❌ Model test failed. Please check the error messages above.")
