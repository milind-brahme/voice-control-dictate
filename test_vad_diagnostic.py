#!/usr/bin/env python3
"""
Voice Recognition Diagnostic Test
Debug tool to identify VAD and audio input issues
"""

import asyncio
import logging
import sys
import numpy as np
import pyaudio
import webrtcvad
from src.config import Config

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_audio_input():
    """Test audio input and VAD settings"""
    logger = logging.getLogger(__name__)
    
    print("🔍 Voice Recognition Diagnostic Test")
    print("=" * 50)
    
    # Load config
    config = Config('config.yaml')
    
    # Audio settings
    sample_rate = config.get('audio.sample_rate', 16000)
    input_device = config.get('audio.input_device', None)
    vad_aggressiveness = config.get('audio.vad.aggressiveness', 3)
    vad_frame_ms = config.get('audio.vad.frame_ms', 30)
    
    print(f"📊 Configuration:")
    print(f"   Sample rate: {sample_rate}")
    print(f"   Input device: {input_device}")
    print(f"   VAD aggressiveness: {vad_aggressiveness}")
    print(f"   VAD frame duration: {vad_frame_ms}ms")
    
    # Calculate frame settings
    frame_duration_samples = int(sample_rate * (vad_frame_ms / 1000.0))
    frame_size_bytes = frame_duration_samples * 2
    
    print(f"   Frame samples: {frame_duration_samples}")
    print(f"   Frame bytes: {frame_size_bytes}")
    
    # Initialize audio
    audio = pyaudio.PyAudio()
    
    # Test 1: List available devices
    print(f"\n🎤 Available Audio Devices:")
    print("-" * 30)
    for i in range(audio.get_device_count()):
        info = audio.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            marker = " ← SELECTED" if i == input_device else ""
            print(f"   {i}: {info['name']} (channels: {info['maxInputChannels']}){marker}")
    
    # Test 2: Check device accessibility
    print(f"\n🔧 Testing Device {input_device}:")
    print("-" * 30)
    
    try:
        if input_device is not None:
            device_info = audio.get_device_info_by_index(input_device)
            print(f"   ✓ Device accessible: {device_info['name']}")
        else:
            print(f"   ⚠️ Using default device")
    except Exception as e:
        print(f"   ✗ Device error: {e}")
        audio.terminate()
        return
    
    # Test 3: Test audio stream
    print(f"\n🎵 Testing Audio Stream:")
    print("-" * 30)
    
    try:
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            input=True,
            input_device_index=input_device,
            frames_per_buffer=frame_duration_samples
        )
        print(f"   ✓ Audio stream opened successfully")
        
        # Test 4: Record some frames and check levels
        print(f"\n📈 Recording Audio Levels (10 seconds):")
        print("-" * 30)
        print("   Speak into your microphone...")
        
        vad = webrtcvad.Vad(vad_aggressiveness)
        
        for i in range(100):  # 10 seconds at 10fps
            try:
                # Read audio data
                audio_data = stream.read(frame_duration_samples, exception_on_overflow=False)
                
                # Calculate volume
                audio_np = np.frombuffer(audio_data, dtype=np.int16)
                volume = np.sqrt(np.mean(audio_np.astype(np.float64)**2))
                
                # Test VAD
                try:
                    is_speech = vad.is_speech(audio_data, sample_rate)
                    speech_status = "SPEECH" if is_speech else "silence"
                except Exception as vad_error:
                    speech_status = f"VAD_ERROR: {vad_error}"
                
                # Display every 10th frame
                if i % 10 == 0:
                    print(f"   Frame {i//10 + 1}/10: Volume={volume:6.1f}, Status={speech_status}")
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"   ✗ Frame error: {e}")
                break
        
        stream.stop_stream()
        stream.close()
        
        print(f"\n💡 Diagnostic Results:")
        print("-" * 30)
        print(f"   If volume is consistently low (< 100), check:")
        print(f"     • Microphone volume/gain settings")
        print(f"     • Microphone positioning")
        print(f"     • Windows microphone privacy settings")
        print(f"   If VAD never shows 'SPEECH', try:")
        print(f"     • Lowering VAD aggressiveness (try 1 or 2)")
        print(f"     • Speaking louder/closer to microphone")
        print(f"     • Checking for background noise")
        
    except Exception as e:
        print(f"   ✗ Stream error: {e}")
    
    finally:
        audio.terminate()
    
    print(f"\n🔧 Suggested config.yaml adjustments:")
    print("-" * 30)
    print(f"   Try lowering VAD aggressiveness:")
    print(f"   audio:")
    print(f"     vad:")
    print(f"       aggressiveness: 1  # Try 1 or 2 instead of 3")

if __name__ == "__main__":
    asyncio.run(test_audio_input())
