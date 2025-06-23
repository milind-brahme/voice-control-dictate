#!/usr/bin/env python3
"""
Generate test audio files for voice recognition testing
"""

import numpy as np
import soundfile as sf
import logging

logger = logging.getLogger(__name__)

def generate_test_audio():
    """Generate simple test audio files"""
    
    # Audio parameters
    sample_rate = 16000  # Standard for speech recognition
    duration = 3.0  # 3 seconds
    
    try:
        # Generate a simple sine wave tone (simulating speech frequency)
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # Mix of frequencies common in human speech
        freq1 = 440  # A4 note
        freq2 = 880  # A5 note
        
        # Create a simple tone that could represent speech
        audio = (np.sin(2 * np.pi * freq1 * t) * 0.3 + 
                np.sin(2 * np.pi * freq2 * t) * 0.2)
        
        # Add some envelope to make it more speech-like
        envelope = np.exp(-t * 0.5)  # Decay envelope
        audio = audio * envelope
        
        # Normalize
        audio = audio / np.max(np.abs(audio)) * 0.8
        
        # Save as WAV file
        sf.write('test_audio.wav', audio, sample_rate)
        logger.info("✓ Generated test_audio.wav")
        
        # Generate silence for testing
        silence = np.zeros(int(sample_rate * 2.0))  # 2 seconds of silence
        sf.write('test_silence.wav', silence, sample_rate)
        logger.info("✓ Generated test_silence.wav")
        
        # Generate white noise
        noise = np.random.normal(0, 0.1, int(sample_rate * 2.0))
        sf.write('test_noise.wav', noise, sample_rate)
        logger.info("✓ Generated test_noise.wav")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to generate test audio: {e}")
        return False

def generate_speech_like_audio():
    """Generate more speech-like audio patterns"""
    
    sample_rate = 16000
    duration = 4.0
    
    try:
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # Speech-like pattern: varying frequency and amplitude
        audio = np.zeros_like(t)
        
        # Simulate phonemes with different frequencies
        phoneme_duration = 0.2  # 200ms per phoneme
        num_phonemes = int(duration / phoneme_duration)
        
        for i in range(num_phonemes):
            start_idx = int(i * phoneme_duration * sample_rate)
            end_idx = int((i + 1) * phoneme_duration * sample_rate)
            
            if end_idx > len(t):
                break
                
            # Vary frequency for different "phonemes"
            base_freq = 200 + (i % 5) * 100  # 200-600 Hz range
            formant1 = base_freq * 2
            formant2 = base_freq * 3
            
            # Create formant-like structure
            phoneme_t = t[start_idx:end_idx]
            phoneme_audio = (
                np.sin(2 * np.pi * base_freq * phoneme_t) * 0.4 +
                np.sin(2 * np.pi * formant1 * phoneme_t) * 0.2 +
                np.sin(2 * np.pi * formant2 * phoneme_t) * 0.1
            )
            
            # Add envelope
            envelope = np.hanning(len(phoneme_audio))
            phoneme_audio *= envelope
            
            audio[start_idx:end_idx] = phoneme_audio
        
        # Normalize
        audio = audio / np.max(np.abs(audio)) * 0.7
        
        # Save
        sf.write('test_speech_like.wav', audio, sample_rate)
        logger.info("✓ Generated test_speech_like.wav")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to generate speech-like audio: {e}")
        return False

def main():
    """Generate all test audio files"""
    logging.basicConfig(level=logging.INFO)
    
    logger.info("🎵 Generating test audio files...")
    
    success1 = generate_test_audio()
    success2 = generate_speech_like_audio()
    
    if success1 and success2:
        logger.info("🎉 All test audio files generated successfully!")
        logger.info("Files created:")
        logger.info("  - test_audio.wav (simple tones)")
        logger.info("  - test_silence.wav (silence)")
        logger.info("  - test_noise.wav (white noise)")
        logger.info("  - test_speech_like.wav (speech-like patterns)")
    else:
        logger.error("❌ Failed to generate some audio files")

if __name__ == "__main__":
    main()
