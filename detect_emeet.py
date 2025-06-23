#!/usr/bin/env python3
"""
Audio Device Detection - Find and test eMeet microphone
Simple script to detect available audio devices and test eMeet microphone
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    import pyaudio
    import numpy as np
    import time
    from config import Config
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all dependencies are installed.")
    sys.exit(1)

def list_audio_devices():
    """List all available audio devices"""
    print("🎤 Detecting Audio Devices...")
    print("=" * 60)
    
    audio = pyaudio.PyAudio()
    emeet_devices = []
    all_input_devices = []
    
    try:
        device_count = audio.get_device_count()
        print(f"Total devices found: {device_count}\n")
        
        for i in range(device_count):
            try:
                info = audio.get_device_info_by_index(i)
                name = info['name']
                
                # Check if it's an input device
                if info['maxInputChannels'] > 0:
                    all_input_devices.append((i, info))
                    
                    # Check if it's an eMeet device
                    if 'emeet' in name.lower() or 'meet' in name.lower():
                        emeet_devices.append((i, info))
                        print(f"🎯 FOUND eMeet Device:")
                    else:
                        print(f"📱 Input Device:")
                    
                    print(f"   Index: {i}")
                    print(f"   Name: {name}")
                    print(f"   Max Input Channels: {info['maxInputChannels']}")
                    print(f"   Default Sample Rate: {int(info['defaultSampleRate'])} Hz")
                    print(f"   Host API: {info['hostApi']}")
                    print()
                    
            except Exception as e:
                print(f"   Error reading device {i}: {e}")
                continue
                
    except Exception as e:
        print(f"❌ Error accessing audio system: {e}")
        return [], []
    finally:
        audio.terminate()
    
    return emeet_devices, all_input_devices

def test_microphone(device_index, duration=3):
    """Test a specific microphone for a few seconds"""
    print(f"\n🔊 Testing device {device_index} for {duration} seconds...")
    
    audio = pyaudio.PyAudio()
    
    try:
        # Audio settings
        sample_rate = 16000
        chunk_size = 1024
        channels = 1
        format = pyaudio.paInt16
        
        # Open stream
        stream = audio.open(
            format=format,
            channels=channels,
            rate=sample_rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=chunk_size
        )
        
        print("🎵 Recording... (speak into the microphone)")
        
        volumes = []
        for i in range(int(sample_rate * duration / chunk_size)):
            data = stream.read(chunk_size)
            audio_data = np.frombuffer(data, dtype=np.int16)
            volume = np.sqrt(np.mean(audio_data**2))
            volumes.append(volume)
            
            # Simple volume meter
            level = min(int(volume / 100), 20)
            meter = "█" * level + "░" * (20 - level)
            print(f"\r   Volume: |{meter}| {int(volume):4d}", end="", flush=True)
            
        stream.stop_stream()
        stream.close()
        
        avg_volume = np.mean(volumes)
        max_volume = np.max(volumes)
        
        print(f"\n   ✅ Test complete!")
        print(f"   Average Volume: {int(avg_volume)}")
        print(f"   Peak Volume: {int(max_volume)}")
        
        if max_volume > 100:
            print("   🟢 Microphone is working well!")
        elif max_volume > 10:
            print("   🟡 Microphone is working but may be quiet")
        else:
            print("   🔴 No significant audio detected")
            
        return True
        
    except Exception as e:
        print(f"   ❌ Error testing microphone: {e}")
        return False
    finally:
        audio.terminate()

def update_config_for_emeet(device_index, config_file="config.yaml"):
    """Update config file to use eMeet microphone"""
    try:
        config = Config(config_file)
        
        # Update audio input device
        print(f"\n🔧 Updating config to use device {device_index}...")
        
        # Read current config file
        with open(config_file, 'r') as f:
            lines = f.readlines()
        
        # Update input_device line
        updated = False
        for i, line in enumerate(lines):
            if 'input_device:' in line:
                lines[i] = f"  input_device: {device_index}  # eMeet microphone\n"
                updated = True
                break
        
        if not updated:
            # Add input_device to audio section
            for i, line in enumerate(lines):
                if line.strip() == 'audio:':
                    lines.insert(i + 1, f"  input_device: {device_index}  # eMeet microphone\n")
                    break
        
        # Write updated config
        with open(config_file, 'w') as f:
            f.writelines(lines)
            
        print(f"   ✅ Config updated to use device {device_index}")
        return True
        
    except Exception as e:
        print(f"   ❌ Error updating config: {e}")
        return False

def main():
    print("🎯 eMeet Microphone Detection & Setup")
    print("=" * 50)
    
    # List all devices
    emeet_devices, all_devices = list_audio_devices()
    
    if not all_devices:
        print("❌ No audio input devices found!")
        return
    
    # Handle eMeet devices
    if emeet_devices:
        print(f"🎉 Found {len(emeet_devices)} eMeet device(s)!")
        
        for device_index, info in emeet_devices:
            print(f"\n🧪 Testing eMeet device {device_index}: {info['name']}")
            if test_microphone(device_index):
                response = input(f"\n❓ Use this eMeet device ({device_index}) as default? (y/n): ").strip().lower()
                if response in ['y', 'yes']:
                    update_config_for_emeet(device_index)
                    print(f"\n✅ eMeet microphone configured! Device {device_index} is now the default.")
                    break
    else:
        print("⚠️  No eMeet devices detected by name.")
        print("Your eMeet microphone might be listed under a different name.")
        print("\nLet's test all available input devices:\n")
        
        for device_index, info in all_devices:
            print(f"🧪 Testing device {device_index}: {info['name']}")
            if test_microphone(device_index):
                response = input(f"\n❓ Is this your eMeet microphone? Use as default? (y/n): ").strip().lower()
                if response in ['y', 'yes']:
                    update_config_for_emeet(device_index)
                    print(f"\n✅ Microphone configured! Device {device_index} is now the default.")
                    break
            print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
