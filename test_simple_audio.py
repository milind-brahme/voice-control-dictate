#!/usr/bin/env python3
"""
Simple volume-based voice detection test
Bypasses WebRTC VAD to test basic audio input
"""

import asyncio
import logging
import numpy as np
import pyaudio
import sys
from src.config import Config

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

async def test_simple_audio():
    """Test simple volume-based voice detection"""
    print("🎤 Simple Audio Input Test")
    print("=" * 40)
    
    config = Config('config.yaml')
    sample_rate = config.get('audio.sample_rate', 16000)
    input_device = config.get('audio.input_device', None)
    
    print(f"Sample rate: {sample_rate}")
    print(f"Input device: {input_device}")
    print("Speak into your microphone for 10 seconds...")
    print("-" * 40)
    
    audio = pyaudio.PyAudio()
    
    try:
        # Test if device exists
        if input_device is not None:
            try:
                device_info = audio.get_device_info_by_index(input_device)
                print(f"Using device: {device_info['name']}")
            except:
                print(f"Device {input_device} not found, using default")
                input_device = None
        
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            input=True,
            input_device_index=input_device,
            frames_per_buffer=1024
        )
        
        volumes = []
        for i in range(100):  # 10 seconds
            try:
                data = stream.read(1024, exception_on_overflow=False)
                audio_np = np.frombuffer(data, dtype=np.int16)
                volume = np.sqrt(np.mean(audio_np.astype(np.float64)**2))
                volumes.append(volume)
                
                if i % 10 == 0:  # Every second
                    status = "LOUD" if volume > 500 else "quiet"
                    print(f"Second {i//10 + 1}: Volume = {volume:.1f} ({status})")
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"Error reading audio: {e}")
                break
        
        stream.stop_stream()
        stream.close()
        
        print("-" * 40)
        if volumes:
            avg_vol = np.mean(volumes)
            max_vol = np.max(volumes)
            print(f"Average volume: {avg_vol:.1f}")
            print(f"Maximum volume: {max_vol:.1f}")
            
            if max_vol < 100:
                print("⚠️  Volume is very low - check microphone settings")
            elif max_vol < 500:
                print("⚠️  Volume is low - try speaking louder")
            else:
                print("✓ Volume levels look good")
        
    except Exception as e:
        print(f"Audio error: {e}")
    finally:
        audio.terminate()

if __name__ == "__main__":
    asyncio.run(test_simple_audio())
