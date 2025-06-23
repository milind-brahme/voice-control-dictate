#!/usr/bin/env python3
"""
Simple eMeet Audio Meter - Shows real-time audio levels for eMeet M0
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import pyaudio
import numpy as np
import time

def simple_audio_meter():
    """Simple audio meter for eMeet M0"""
    
    print("🎤 eMeet M0 Audio Meter")
    print("=" * 40)
    
    # Audio settings optimized for eMeet M0
    DEVICE_INDEX = 38  # eMeet M0 from detection
    SAMPLE_RATE = 16000
    CHUNK_SIZE = 1024
    CHANNELS = 1
    FORMAT = pyaudio.paInt16
    
    audio = pyaudio.PyAudio()
    
    try:
        print(f"Opening eMeet M0 (Device {DEVICE_INDEX})...")
        
        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            input_device_index=DEVICE_INDEX,
            frames_per_buffer=CHUNK_SIZE
        )
        
        print("🔊 Audio meter running (Press Ctrl+C to stop)")
        print("Speak into your eMeet microphone...")
        print()
        
        while True:
            try:
                # Read audio data
                data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                
                # Convert to numpy array
                audio_data = np.frombuffer(data, dtype=np.int16)
                
                # Calculate volume (RMS)
                if len(audio_data) > 0:
                    volume = np.sqrt(np.mean(audio_data.astype(np.float64)**2))
                    
                    # Avoid NaN
                    if np.isnan(volume) or np.isinf(volume):
                        volume = 0
                else:
                    volume = 0
                
                # Create visual meter (0-30 characters)
                level = min(int(volume / 20), 30)  # Adjusted for eMeet sensitivity
                
                # Different characters for different levels
                if volume > 50:
                    char = "█"  # High volume - speaking
                    status = "🟢 SPEAKING"
                elif volume > 20:
                    char = "▓"  # Medium volume
                    status = "🟡 QUIET   "
                else:
                    char = "░"  # Low volume - silence
                    status = "🔴 SILENT "
                
                meter = char * level + "░" * (30 - level)
                
                # Display meter
                print(f"\\r{status} |{meter}| {int(volume):3d}", end="", flush=True)
                
            except Exception as e:
                print(f"\\rError reading audio: {e}")
                time.sleep(0.1)
                
    except Exception as e:
        print(f"❌ Error opening eMeet microphone: {e}")
        print("Make sure your eMeet M0 is connected and not being used by other apps.")
        
    except KeyboardInterrupt:
        print("\\n\\n🛑 Audio meter stopped")
        
    finally:
        if 'stream' in locals():
            stream.stop_stream()
            stream.close()
        audio.terminate()

if __name__ == "__main__":
    simple_audio_meter()
