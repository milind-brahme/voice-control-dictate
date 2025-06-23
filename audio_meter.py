#!/usr/bin/env python3
"""
Audio Meter - Real-time audio level monitoring for voice control system
Shows visual audio meter in command line to help with microphone setup
"""

import asyncio
import logging
import sys
import os
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import Config
import pyaudio
import numpy as np
import threading
from queue import Queue, Empty

class AudioMeter:
    def __init__(self, config_file="config.yaml"):
        """Initialize audio meter with configuration"""
        self.config = Config(config_file)
        
        # Audio settings from config
        self.sample_rate = self.config.get('audio.sample_rate', 16000)
        self.chunk_size = self.config.get('audio.chunk_size', 1024)
        self.channels = self.config.get('audio.channels', 1)
        self.format = pyaudio.paInt16
        
        # Threshold from config
        self.silence_threshold = self.config.get('audio.silence_threshold', 500)
        
        # Audio processing
        self.audio = pyaudio.PyAudio()
        self.audio_queue = Queue()
        self.is_monitoring = False
        self.stream = None
        
        # Display settings
        self.meter_width = 50
        self.max_volume = 5000  # Adjust based on your microphone
        
    def __del__(self):
        """Cleanup audio resources"""
        if hasattr(self, 'audio'):
            self.audio.terminate()
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for audio stream"""
        if self.is_monitoring:
            self.audio_queue.put(in_data)
        return (None, pyaudio.paContinue)
    
    def _calculate_volume(self, audio_data):
        """Calculate RMS volume of audio data"""
        try:
            audio_np = np.frombuffer(audio_data, dtype=np.int16)
            return np.sqrt(np.mean(audio_np**2))
        except:
            return 0
    
    def list_audio_devices(self):
        """List available audio input devices"""
        print("\\n📋 Available Audio Input Devices:")
        print("-" * 60)
        
        devices = []
        for i in range(self.audio.get_device_count()):
            try:
                info = self.audio.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    devices.append({
                        'index': i,
                        'name': info['name'],
                        'channels': info['maxInputChannels'],
                        'sample_rate': int(info['defaultSampleRate'])
                    })
                    print(f"{i:2d}: {info['name']}")
                    print(f"    Channels: {info['maxInputChannels']}, Sample Rate: {int(info['defaultSampleRate'])} Hz")
            except Exception as e:
                continue
        
        print("-" * 60)
        return devices
    
    def start_monitoring(self, device_index=None):
        """Start audio monitoring"""
        try:
            print(f"\\n🎤 Starting audio meter...")
            print(f"Sample Rate: {self.sample_rate} Hz")
            print(f"Chunk Size: {self.chunk_size}")
            print(f"Silence Threshold: {self.silence_threshold}")
            print(f"Device: {device_index if device_index is not None else 'Default'}")
            
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
            
            self.is_monitoring = True
            self.stream.start_stream()
            
            print("\\n🔊 Audio Meter (Press Ctrl+C to stop)")
            print("=" * 70)
            
            return True
            
        except Exception as e:
            print(f"❌ Error starting audio stream: {e}")
            return False
    
    def stop_monitoring(self):
        """Stop audio monitoring"""
        self.is_monitoring = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        # Clear queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except Empty:
                break
    
    def _create_meter_display(self, volume, is_speaking):
        """Create visual meter display"""
        # Calculate meter level (0 to meter_width)
        level = min(int((volume / self.max_volume) * self.meter_width), self.meter_width)
        
        # Create meter bar
        meter_char = "█" if is_speaking else "▓"
        meter = meter_char * level + "░" * (self.meter_width - level)
        
        # Status indicator
        status = "🟢 SPEAKING" if is_speaking else "🔴 SILENT "
        
        # Volume percentage
        volume_pct = min(int((volume / self.max_volume) * 100), 100)
        
        return f"{status} |{meter}| {volume_pct:3d}% (Vol: {int(volume):4d})"
    
    async def monitor_loop(self):
        """Main monitoring loop"""
        try:
            while self.is_monitoring:
                try:
                    # Get audio data with timeout
                    data = self.audio_queue.get(timeout=0.1)
                    volume = self._calculate_volume(data)
                    
                    # Check if speaking (above threshold)
                    is_speaking = volume > self.silence_threshold
                    
                    # Create and display meter
                    meter_display = self._create_meter_display(volume, is_speaking)
                    
                    # Clear line and print meter
                    print(f"\\r{meter_display}", end="", flush=True)
                    
                except Empty:
                    await asyncio.sleep(0.01)
                    continue
                    
        except Exception as e:
            print(f"\\n❌ Monitoring error: {e}")

async def main():
    """Main function"""
    print("🎵 Voice Control Audio Meter")
    print("=" * 50)
    
    meter = AudioMeter()
    
    # List available devices
    devices = meter.list_audio_devices()
    
    if not devices:
        print("❌ No audio input devices found!")
        return
    
    # Ask user to select device (optional)
    print(f"\\n📟 Press Enter to use default device, or enter device number (0-{len(devices)-1}):")
    try:
        user_input = input().strip()
        device_index = None if user_input == "" else int(user_input)
        
        if device_index is not None and (device_index < 0 or device_index >= len(devices)):
            print(f"❌ Invalid device number. Using default device.")
            device_index = None
            
    except (ValueError, KeyboardInterrupt):
        device_index = None
    
    # Start monitoring
    if not meter.start_monitoring(device_index):
        return
    
    try:
        await meter.monitor_loop()
    except KeyboardInterrupt:
        print("\\n\\n🛑 Audio monitoring stopped by user")
    finally:
        meter.stop_monitoring()
        print("\\n✅ Audio meter stopped")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\n\\n👋 Goodbye!")
