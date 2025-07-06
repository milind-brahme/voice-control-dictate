"""
Configuration management module
Handles loading and validation of configuration settings
"""

import logging
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

class Config:
    def __init__(self, config_path: str = "config.yaml"):
        self.logger = logging.getLogger(__name__)
        self.config_path = Path(config_path)
        self.config_data = {}
        
        self._load_config()
        self._validate_config()
    
    def _load_config(self):
        """Load configuration from file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self.config_data = yaml.safe_load(f) or {}
                self.logger.info(f"Loaded configuration from {self.config_path}")
            else:
                self.logger.warning(f"Configuration file {self.config_path} not found, using defaults")
                self._create_default_config()
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            self.config_data = {}
    
    def _create_default_config(self):
        """Create default configuration"""
        default_config = {
            'audio': {
                'sample_rate': 16000,
                'chunk_size': 1024,
                'channels': 1,
                'silence_threshold': 500,
                'silence_duration': 2.0,
                'min_audio_length': 1.0
            },
            'whisper': {
                'model_size': 'base',
                'language': None,
                'device': 'auto'
            },
            'commands': {
                'wake_words': ['activate', 'computer', 'hey assistant'],
                'stop_dictation': ['stop dictation', 'end dictation'],
                'start_dictation': ['start dictation', 'begin dictation']
            }
        }
        
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False)
            self.config_data = default_config
            self.logger.info(f"Created default configuration at {self.config_path}")
        except Exception as e:
            self.logger.error(f"Failed to create default configuration: {e}")
    
    def _validate_config(self):
        """Validate configuration values"""
        # Validate audio settings
        audio = self.config_data.get('audio', {})
        if audio.get('sample_rate', 16000) not in [8000, 16000, 22050, 44100, 48000]:
            self.logger.warning("Invalid sample rate, using default 16000")
            self.config_data.setdefault('audio', {})['sample_rate'] = 16000
        
        # Validate Whisper model
        whisper = self.config_data.get('whisper', {})
        valid_models = ['tiny', 'base', 'small', 'medium', 'large', 'large-v2', 'large-v3']
        if whisper.get('model_size') not in valid_models:
            self.logger.warning(f"Invalid model size '{whisper.get('model_size')}', using 'base'")
            self.config_data.setdefault('whisper', {})['model_size'] = 'base'
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        try:
            keys = key.split('.')
            value = self.config_data
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
        except Exception:
            return default
    
    def set(self, key: str, value: Any):
        """Set configuration value using dot notation"""
        try:
            keys = key.split('.')
            config = self.config_data
            
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            config[keys[-1]] = value
            self._save_config()
        except Exception as e:
            self.logger.error(f"Failed to set configuration {key}: {e}")
    
    def _save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config_data, f, default_flow_style=False)
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
    
    def reload(self):
        """Reload configuration from file"""
        self._load_config()
        self._validate_config()