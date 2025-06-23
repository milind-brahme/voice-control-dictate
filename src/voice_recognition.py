"""
Voice Recognition Module using OpenAI Whisper
Handles speech-to-text conversion with robust audio processing
"""

import asyncio
import logging
import numpy as np
import whisper
import pyaudio
import wave
import tempfile
import threading
from queue import Queue, Empty
from typing import AsyncGenerator, Optional
import torch

class VoiceRecognizer:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Audio settings
        self.sample_rate = config.get('audio.sample_rate', 16000)
        self.chunk_size = config.get('audio.chunk_size', 1024)
        self.channels = config.get('audio.channels', 1)
        self.format = pyaudio.paInt16
        
        # Whisper settings
        model_size = config.get('whisper.model_size', 'base')
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        self.logger.info(f"Loading Whisper model '{model_size}' on {self.device}")
        self.model = whisper.load_model(model_size, device=self.device)
        
        # Audio processing
        self.audio = pyaudio.PyAudio()
        self.audio_queue = Queue()
        self.is_recording = False
        
        # Voice activity detection settings
        self.silence_threshold = config.get('audio.silence_threshold', 500)
        self.silence_duration = config.get('audio.silence_duration', 2.0)
        self.min_audio_length = config.get('audio.min_audio_length', 1.0)
        
    def __del__(self):
        """Cleanup audio resources"""
        if hasattr(self, 'audio'):
            self.audio.terminate()
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for audio stream"""
        if self.is_recording:
            self.audio_queue.put(in_data)
        return (None, pyaudio.paContinue)
    
    def _calculate_volume(self, audio_data):
        """Calculate RMS volume of audio data"""
        audio_np = np.frombuffer(audio_data, dtype=np.int16)
        return np.sqrt(np.mean(audio_np**2))
    
    async def _record_audio_segment(self) -> Optional[bytes]:
        """Record an audio segment with voice activity detection"""
        stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=self._audio_callback
        )
        
        self.is_recording = True
        stream.start_stream()
        
        audio_frames = []
        silence_frames = 0
        speaking_started = False
        
        try:
            while True:
                try:
                    # Get audio data with timeout
                    data = self.audio_queue.get(timeout=0.1)
                    volume = self._calculate_volume(data)
                    
                    if volume > self.silence_threshold:
                        # Voice detected
                        speaking_started = True
                        silence_frames = 0
                        audio_frames.append(data)
                    else:
                        # Silence detected
                        if speaking_started:
                            silence_frames += 1
                            audio_frames.append(data)
                            
                            # Check if silence duration exceeded
                            silence_duration = (silence_frames * self.chunk_size) / self.sample_rate
                            if silence_duration > self.silence_duration:
                                break
                        
                except Empty:
                    await asyncio.sleep(0.01)
                    continue
                    
        finally:
            self.is_recording = False
            stream.stop_stream()
            stream.close()
            
            # Clear remaining queue
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                except Empty:
                    break
        
        if not audio_frames:
            return None
            
        # Check minimum audio length
        total_duration = (len(audio_frames) * self.chunk_size) / self.sample_rate
        if total_duration < self.min_audio_length:
            return None
            
        return b''.join(audio_frames)
    
    async def _transcribe_audio(self, audio_data: bytes) -> str:
        """Transcribe audio data using Whisper"""
        try:
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                # Create WAV file
                with wave.open(temp_file.name, 'wb') as wav_file:
                    wav_file.setnchannels(self.channels)
                    wav_file.setsampwidth(self.audio.get_sample_size(self.format))
                    wav_file.setframerate(self.sample_rate)
                    wav_file.writeframes(audio_data)
                
                # Transcribe in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, 
                    lambda: self.model.transcribe(
                        temp_file.name,
                        language=self.config.get('whisper.language', None),
                        task='transcribe'
                    )
                )
                
                return result['text'].strip()
                
        except Exception as e:
            self.logger.error(f"Transcription error: {e}")
            return ""
    
    async def recognize_once(self) -> str:
        """Recognize speech once and return transcribed text"""
        self.logger.debug("Starting single recognition")
        
        audio_data = await self._record_audio_segment()
        if not audio_data:
            return ""
            
        text = await self._transcribe_audio(audio_data)
        self.logger.info(f"Recognized: {text}")
        return text
    
    async def continuous_recognition(self) -> AsyncGenerator[str, None]:
        """Continuously recognize speech and yield transcribed text"""
        self.logger.info("Starting continuous recognition")
        
        while True:
            try:
                text = await self.recognize_once()
                if text:
                    yield text
            except Exception as e:
                self.logger.error(f"Recognition error: {e}")
                await asyncio.sleep(1)  # Brief pause before retrying
    
    def list_audio_devices(self):
        """List available audio input devices"""
        devices = []
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                devices.append({
                    'index': i,
                    'name': info['name'],
                    'channels': info['maxInputChannels'],
                    'sample_rate': info['defaultSampleRate']
                })
        return devices