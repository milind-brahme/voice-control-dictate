"""
Enhanced Voice Recognition Module with multiple Whisper options
Supports standard Whisper, Faster-Whisper, and other high-accuracy models
"""

import asyncio
import logging
import numpy as np
import pyaudio
import wave
import tempfile
import threading
from queue import Queue, Empty
from typing import AsyncGenerator, Optional
import torch

class EnhancedVoiceRecognizer:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Audio settings
        self.sample_rate = config.get('audio.sample_rate', 16000)
        self.chunk_size = config.get('audio.chunk_size', 1024)
        self.channels = config.get('audio.channels', 1)
        self.format = pyaudio.paInt16
        self.input_device = config.get('audio.input_device', None)
        
        # Enhanced Whisper settings
        self.model_type = config.get('whisper.model_type', 'faster-whisper')  # 'whisper', 'faster-whisper'
        self.model_size = config.get('whisper.model_size', 'large-v3')
        self.language = config.get('whisper.language', None)  # Auto-detect if None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Initialize the appropriate model
        self._initialize_model()
        
        # Audio processing
        self.audio = pyaudio.PyAudio()
        self.audio_queue = Queue()
        self.is_recording = False
        
        # Enhanced VAD settings
        self.silence_threshold = config.get('audio.silence_threshold', 500)
        self.silence_duration = config.get('audio.silence_duration', 2.0)
        self.min_audio_length = config.get('audio.min_audio_length', 1.0)
        self.vad_padding_ms = config.get('audio.vad_padding_ms', 300)
        
        # Log configuration
        self.logger.info(f"Initialized {self.model_type} with model '{self.model_size}' on {self.device}")
        if self.input_device is not None:
            try:
                device_info = self.audio.get_device_info_by_index(self.input_device)
                self.logger.info(f"Using audio device: {device_info['name']}")
            except Exception as e:
                self.logger.error(f"Error getting device info: {e}")
    
    def _initialize_model(self):
        """Initialize the appropriate Whisper model"""
        self.logger.info(f"Loading {self.model_type} model '{self.model_size}' on {self.device}")
        
        if self.model_type == 'faster-whisper':
            try:
                from faster_whisper import WhisperModel
                
                # Determine device for faster-whisper
                device = "cuda" if torch.cuda.is_available() else "cpu"
                compute_type = "float16" if device == "cuda" else "float32"
                
                self.model = WhisperModel(
                    self.model_size,
                    device=device,
                    compute_type=compute_type,
                    download_root=None,
                    local_files_only=False
                )
                self.logger.info(f"✅ Faster-Whisper model loaded successfully (compute_type: {compute_type})")
                
            except ImportError:
                self.logger.warning("Faster-Whisper not available, falling back to standard Whisper")
                self.model_type = 'whisper'
                self._initialize_standard_whisper()
                
        elif self.model_type == 'whisper':
            self._initialize_standard_whisper()
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
    
    def _initialize_standard_whisper(self):
        """Initialize standard OpenAI Whisper"""
        try:
            import whisper
            self.model = whisper.load_model(self.model_size, device=self.device)
            self.logger.info("✅ Standard Whisper model loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load Whisper model: {e}")
            raise
    
    async def recognize_once(self) -> Optional[str]:
        """Record and recognize a single audio segment"""
        try:
            # Start recording
            stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.input_device,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
            
            self.is_recording = True
            stream.start_stream()
            
            # Wait for speech and silence
            audio_data = await self._wait_for_speech()
            
            if audio_data is None:
                return None
            
            # Convert to audio file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                self._save_audio_data(audio_data, temp_file.name)
                
                # Transcribe using the selected model
                text = await self._transcribe_audio(temp_file.name)
                
                # Clean up
                import os
                os.unlink(temp_file.name)
                
                return text.strip() if text else None
                
        except Exception as e:
            self.logger.error(f"Recognition error: {e}")
            return None
        finally:
            self.is_recording = False
            if 'stream' in locals():
                stream.stop_stream()
                stream.close()
    
    async def _transcribe_audio(self, file_path: str) -> str:
        """Transcribe audio using the selected model"""
        try:
            if self.model_type == 'faster-whisper':
                return await self._transcribe_faster_whisper(file_path)
            else:
                return await self._transcribe_standard_whisper(file_path)
        except Exception as e:
            self.logger.error(f"Transcription error: {e}")
            return ""
    
    async def _transcribe_faster_whisper(self, file_path: str) -> str:
        """Transcribe using Faster-Whisper"""
        loop = asyncio.get_event_loop()
        
        def transcribe():
            segments, info = self.model.transcribe(
                file_path,
                language=self.language,
                beam_size=5,
                best_of=5,
                temperature=0.0,
                condition_on_previous_text=False,
                initial_prompt=None,
                word_timestamps=False
            )
            
            # Extract text from segments
            text_segments = []
            for segment in segments:
                text_segments.append(segment.text)
            
            return " ".join(text_segments).strip()
        
        result = await loop.run_in_executor(None, transcribe)
        self.logger.debug(f"Faster-Whisper result: {result}")
        return result
    
    async def _transcribe_standard_whisper(self, file_path: str) -> str:
        """Transcribe using standard Whisper"""
        loop = asyncio.get_event_loop()
        
        def transcribe():
            result = self.model.transcribe(
                file_path,
                language=self.language,
                temperature=0.0,
                best_of=5,
                beam_size=5,
                condition_on_previous_text=False,
                initial_prompt=None,
                word_timestamps=False
            )
            return result["text"]
        
        result = await loop.run_in_executor(None, transcribe)
        self.logger.debug(f"Standard Whisper result: {result}")
        return result
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Audio callback function"""
        if self.is_recording:
            self.audio_queue.put(in_data)
        return (None, pyaudio.paContinue)
    
    async def _wait_for_speech(self):
        """Wait for speech and return audio data"""
        audio_frames = []
        silence_frames = 0
        speaking_started = False
        
        try:
            while True:
                try:
                    data = self.audio_queue.get(timeout=0.1)
                    volume = self._calculate_volume(data)
                    
                    if volume > self.silence_threshold:
                        speaking_started = True
                        silence_frames = 0
                        audio_frames.append(data)
                    else:
                        if speaking_started:
                            silence_frames += 1
                            audio_frames.append(data)
                            
                            silence_duration = (silence_frames * self.chunk_size) / self.sample_rate
                            if silence_duration > self.silence_duration:
                                break
                        
                except Empty:
                    await asyncio.sleep(0.01)
                    continue
                    
        finally:
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
    
    def _calculate_volume(self, data):
        """Calculate volume level of audio data"""
        audio_data = np.frombuffer(data, dtype=np.int16)
        return np.sqrt(np.mean(audio_data**2))
    
    def _save_audio_data(self, audio_data, filename):
        """Save audio data to WAV file"""
        with wave.open(filename, 'wb') as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(self.audio.get_sample_size(self.format))
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_data)
    
    async def continuous_recognition(self) -> AsyncGenerator[str, None]:
        """Continuously recognize speech"""
        while True:
            try:
                text = await self.recognize_once()
                if text:
                    yield text
            except Exception as e:
                self.logger.error(f"Recognition error: {e}")
                await asyncio.sleep(1)
    
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
    
    def get_model_info(self):
        """Get information about the current model"""
        return {
            'model_type': self.model_type,
            'model_size': self.model_size,
            'device': self.device,
            'language': self.language
        }
