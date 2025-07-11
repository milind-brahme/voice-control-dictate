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
        self.input_device = config.get('audio.input_device', None)  # Add device selection
        
        # Whisper settings
        self.model_type = config.get('whisper.engine', 'whisper')  # Support both engines
        model_size = config.get('whisper.model_size', 'base')
        self.language = config.get('whisper.language', None)
        self.device = config.get('whisper.device', "cuda" if torch.cuda.is_available() else "cpu")
        
        self.logger.info(f"Loading {self.model_type} model '{model_size}' on {self.device}")
        
        # Initialize the appropriate model
        if self.model_type == 'faster-whisper':
            self._initialize_faster_whisper(model_size)
        else:
            self._initialize_standard_whisper(model_size)
        
        # Audio processing
        self.audio = pyaudio.PyAudio()
        self.audio_queue = Queue()
        self.is_recording = False
        
        # Voice activity detection settings
        self.silence_threshold = config.get('audio.silence_threshold', 500)
        self.silence_duration = config.get('audio.silence_duration', 2.0)
        self.min_audio_length = config.get('audio.min_audio_length', 1.0)
        
        # Log selected audio device
        if self.input_device is not None:
            try:
                device_info = self.audio.get_device_info_by_index(self.input_device)
                self.logger.info(f"Using audio input device {self.input_device}: {device_info['name']}")
            except Exception as e:
                self.logger.warning(f"Could not get info for device {self.input_device}: {e}")
                self.input_device = None
        
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
        try:
            if not audio_data:
                return 0.0
            
            audio_np = np.frombuffer(audio_data, dtype=np.int16)
            if len(audio_np) == 0:
                return 0.0
            
            # Calculate RMS with proper error handling
            mean_square = np.mean(audio_np.astype(np.float64)**2)
            if mean_square < 0 or np.isnan(mean_square) or np.isinf(mean_square):
                return 0.0
            
            return np.sqrt(mean_square)
        except Exception as e:
            self.logger.warning(f"Error calculating volume: {e}")
            return 0.0
    
    async def _record_audio_segment(self) -> Optional[bytes]:
        """Record an audio segment with voice activity detection"""
        stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            input_device_index=self.input_device,  # Use selected device
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
        """Transcribe audio data using the configured Whisper engine"""
        try:
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                # Create WAV file
                with wave.open(temp_file.name, 'wb') as wav_file:
                    wav_file.setnchannels(self.channels)
                    wav_file.setsampwidth(self.audio.get_sample_size(self.format))
                    wav_file.setframerate(self.sample_rate)
                    wav_file.writeframes(audio_data)
                
                # Transcribe based on the engine type
                loop = asyncio.get_event_loop()
                
                if self.model_type == 'faster-whisper':
                    result = await loop.run_in_executor(None, self._transcribe_faster_whisper, temp_file.name)
                else:
                    result = await loop.run_in_executor(None, self._transcribe_standard_whisper, temp_file.name)
                
                return result
                
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
    
    def _get_audio_devices(self):
        """Get list of available audio input devices"""
        devices = []
        try:
            for i in range(self.audio.get_device_count()):
                device_info = self.audio.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:  # Input device
                    devices.append({
                        'index': i,
                        'name': device_info['name'],
                        'channels': device_info['maxInputChannels']
                    })
        except Exception as e:
            self.logger.error(f"Error getting audio devices: {e}")
        return devices
    
    async def transcribe_file(self, file_path: str) -> str:
        """Transcribe audio from a file"""
        try:
            self.logger.info(f"Transcribing file: {file_path}")
            
            if self.model_type == 'faster-whisper':
                return await self._transcribe_faster_whisper(file_path)
            else:
                return await self._transcribe_standard_whisper(file_path)
            
        except Exception as e:
            self.logger.error(f"Error transcribing file {file_path}: {e}")
            return ""
    
    def _transcribe_faster_whisper(self, file_path: str) -> str:
        """Transcribe using Faster-Whisper"""
        try:
            beam_size = self.config.get('whisper.beam_size', 5)
            best_of = self.config.get('whisper.best_of', 5)
            
            segments, info = self.model.transcribe(
                file_path,
                language=self.language,
                beam_size=beam_size,
                best_of=best_of,
                temperature=0.0,
                condition_on_previous_text=False,
                word_timestamps=False
            )
            
            # Extract text from segments
            text_segments = []
            for segment in segments:
                text_segments.append(segment.text)
            
            result = " ".join(text_segments).strip()
            self.logger.info(f"Faster-Whisper transcription result: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Faster-Whisper transcription error: {e}")
            return ""
    
    def _transcribe_standard_whisper(self, file_path: str) -> str:
        """Transcribe using standard Whisper"""
        try:
            result = self.model.transcribe(
                file_path,
                language=self.language,
                temperature=0.0,
                best_of=5,
                beam_size=5,
                condition_on_previous_text=False,
                word_timestamps=False
            )
            text = result["text"]
            self.logger.info(f"Standard Whisper transcription result: {text}")
            return text
        except Exception as e:
            self.logger.error(f"Standard Whisper transcription error: {e}")
            return ""
    
    def _initialize_faster_whisper(self, model_size):
        """Initialize Faster-Whisper model"""
        try:
            from faster_whisper import WhisperModel
            
            compute_type = self.config.get('whisper.compute_type', 'float16' if self.device == 'cuda' else 'float32')
            
            self.model = WhisperModel(
                model_size,
                device=self.device,
                compute_type=compute_type,
                download_root=None,
                local_files_only=False
            )
            self.logger.info(f"✅ Faster-Whisper model loaded successfully (compute_type: {compute_type})")
            
        except ImportError:
            self.logger.warning("Faster-Whisper not available, falling back to standard Whisper")
            self.model_type = 'whisper'
            self._initialize_standard_whisper(model_size)
    
    def _initialize_standard_whisper(self, model_size):
        """Initialize standard OpenAI Whisper"""
        try:
            import whisper
            self.model = whisper.load_model(model_size, device=self.device)
            self.logger.info("✅ Standard Whisper model loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load Whisper model: {e}")
            raise
