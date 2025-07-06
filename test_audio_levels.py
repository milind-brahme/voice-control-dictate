#!/usr/bin/env python3
"""
Audio Level Test - Check if microphone is working and at what levels
"""

import sys
import os
sys.path.insert(0, '.')

import numpy as np
import pyaudio
import time
from src.config import Config

def test_audio_levels():
    """Test audio input levels from the configured microphone"""
    
    print("🎤 Audio Level Test")
    print("=" * 50)
    
    # Load config
    config = Config('config.yaml')
    
    # Audio settings
    sample_rate = config.get('audio.sample_rate', 16000)
    chunk_size = 1024
    device_id = config.get('audio.input_device', 4)
    
    print(f"Testing device {device_id} at {sample_rate}Hz")
    print("Speak into the microphone for 10 seconds...")
    print("You should see volume levels if the microphone is working.\n")
    
    # Initialize PyAudio
    audio = pyaudio.PyAudio()
    
    try:
        # Open stream
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            input=True,
            input_device_index=device_id,
            frames_per_buffer=chunk_size
        )
        
        print("Recording... (10 seconds)")
        max_volume = 0
        min_volume = float('inf')
        
        for i in range(int(sample_rate / chunk_size * 10)):  # 10 seconds
            data = stream.read(chunk_size)
            
            # Calculate volume
            audio_data = np.frombuffer(data, dtype=np.int16)
            volume = np.sqrt(np.mean(audio_data.astype(np.float64)**2))
            
            max_volume = max(max_volume, volume)
            min_volume = min(min_volume, volume)
            
            # Print volume bar every 0.5 seconds
            if i % int(sample_rate / chunk_size / 2) == 0:
                bar_length = int(volume / 1000)  # Scale down
                bar = "█" * min(bar_length, 50)
                print(f"Volume: {volume:6.1f} |{bar:<50}|")
            
            time.sleep(0.01)
        
        stream.stop_stream()
        stream.close()
        
        print(f"\n📊 Results:")
        print(f"Max volume: {max_volume:.1f}")
        print(f"Min volume: {min_volume:.1f}")
        print(f"Range: {max_volume - min_volume:.1f}")
        
        if max_volume < 100:
            print("⚠️  Very low audio levels - microphone may be muted or too quiet")
        elif max_volume < 500:
            print("⚠️  Low audio levels - may need to increase microphone volume")
        elif max_volume > 10000:
            print("⚠️  Very high audio levels - may cause distortion")
        else:
            print("✅ Audio levels look good!")
            
    except Exception as e:
        print(f"❌ Error testing audio: {e}")
    finally:
        audio.terminate()

if __name__ == "__main__":
    test_audio_levels()
