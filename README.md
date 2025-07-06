# Voice Control & Dictation System

A comprehensive voice control and dictation system using OpenAI Whisper for speech recognition with bulletproof cross-platform keystroke automation capabilities.

## Features

- **High-Quality Speech Recognition**: Uses OpenAI Whisper or Faster-Whisper for accurate speech-to-text conversion
- **Enhanced Performance**: Supports Faster-Whisper for 2-4x speed improvement with same accuracy
- **Advanced Models**: Supports all Whisper models including large-v3 for best accuracy
- **GPU Acceleration**: Optimized CUDA support for RTX GPUs with float16 precision
- **Cross-Platform Support**: Works on Linux, Windows, and macOS
- **Bulletproof Keystroke Automation**: Reliable keystroke sending to any window or application
- **Voice Dictation**: Real-time text dictation in any application
- **Voice Commands**: Comprehensive set of voice commands for desktop automation
- **Press Key Commands**: Execute key commands during dictation without interruption
- **GUI Interface**: User-friendly graphical interface for easy control
- **CLI Support**: Command-line interface for headless operation
- **Customizable Commands**: Easy configuration of custom voice commands
- **Multi-Modal Operation**: Switch between command mode and dictation mode seamlessly

## Quick Start

### Installation

1. Clone the repository:
```bash
git clone https://github.com/milind-brahme/voice-control-dictate.git
cd voice-control-dictate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
# GUI mode (default)
python main.py

# CLI mode
python main.py --mode cli

# Start in dictation mode
python main.py --dictation-mode
```

## Platform-Specific Setup

### Linux

Install system dependencies:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3-dev portaudio19-dev xdotool

# Fedora/CentOS
sudo dnf install python3-devel portaudio-devel xdotool

# Arch Linux
sudo pacman -S python portaudio xdotool
```

### Windows

Install dependencies:
```bash
pip install pywin32 pygetwindow
```

Note: May require Microsoft Visual C++ Build Tools for some dependencies.

### macOS

Install dependencies:
```bash
brew install portaudio
pip install pyobjc-framework-Quartz pyobjc-framework-ApplicationServices
```

## Usage

### Voice Commands

The system responds to wake words followed by commands:

**Wake Words**: "activate", "computer", "hey assistant"

**Basic Commands**:
- "activate start dictation" - Enter dictation mode
- "activate stop dictation" - Exit dictation mode
- "activate open firefox" - Open Firefox browser
- "activate search for python tutorials" - Search web
- "activate copy" - Copy selected text
- "activate paste" - Paste text
- "activate new tab" - Open new browser tab

### Dictation Mode

In dictation mode, everything you say is converted to text and typed automatically:

1. Say "activate start dictation"
2. Speak naturally - your speech will be converted to text
3. Say "stop dictation" to return to command mode

#### Press Key Commands During Dictation

**NEW FEATURE**: While in dictation mode, you can execute key commands without interrupting the dictation flow:

- "press key enter" - Press Enter key
- "press tab" - Press Tab key  
- "hit key backspace" - Press Backspace
- "key escape" - Press Escape
- "press ctrl c" - Press Ctrl+C
- "press shift enter" - Press Shift+Enter
- "hit delete key" - Press Delete

These commands are recognized and executed as key presses instead of being typed as text, allowing seamless integration of commands within your dictation workflow.

#### Custom Dictation Commands

**NEW FEATURE**: Create custom voice shortcuts that insert predefined text during dictation mode. Simply say the trigger phrase and the system will type your predefined text instead of the spoken words.

**Example custom commands (configured in `config.yaml`):**
- "insert signature" - Types your email signature
- "insert my address" - Types your home address  
- "meeting introduction" - Types a meeting opener
- "lorem ipsum" - Types placeholder text
- "todo comment" - Inserts code comment template

Configure custom commands in `config.yaml`:
```yaml
commands:
  custom:
    email_signature:
      patterns:
        - "insert signature"
        - "email signature"
      type: "type"
      action: "Best regards,\nYour Name\nemail@example.com"
      description: "Insert email signature"
      category: "dictation"
```

**How it works:** While in dictation mode, if you say any of the configured patterns (like "insert signature"), the system will recognize it as a command and execute the associated action (typing the predefined text) instead of typing the spoken words.

### Configuration

Edit `config.yaml` to customize:

- **Audio settings**: Sample rate, silence detection, VAD sensitivity
- **Whisper engine**: Choose between 'openai-whisper' or 'faster-whisper'
- **Whisper model**: Model size (tiny, base, small, medium, large, large-v3)
- **GPU optimization**: CUDA device, compute type (float16/float32)
- **Wake words**: Customize activation phrases
- **Custom commands**: Add your own voice commands

Example configuration:
```yaml
audio:
  sample_rate: 16000
  silence_threshold: 300
  vad_aggressiveness: 1

whisper:
  engine: faster-whisper    # Use faster-whisper for better performance
  model_size: large-v3      # Best accuracy model
  device: cuda              # Use GPU acceleration
  compute_type: float16     # Optimize for modern GPUs
  language: en              # Set language for better accuracy
  beam_size: 5              # Higher beam size for better accuracy
  best_of: 5                # Generate multiple candidates

commands:
  wake_words:
    - activate
    - computer
    - hey assistant
```

Example custom command:
```yaml
commands:
  custom:
    screenshot:
      patterns:
        - "take screenshot"
        - "capture screen"
      type: "keystroke"
      action: "shift+ctrl+alt+r"
      description: "Take a screenshot"
      category: "custom"
    
    email_signature:
      patterns:
        - "insert signature"
        - "email signature"
        - "add my signature"
      type: "type"
      action: "Best regards,\nYour Name\nEmail: your.email@example.com\nPhone: (555) 123-4567"
      description: "Insert email signature"
      category: "dictation"
    
    meeting_intro:
      patterns:
        - "meeting introduction"
        - "intro text"
      type: "type"
      action: "Good morning everyone, thank you for joining today's meeting."
      description: "Insert meeting introduction"
      category: "dictation"
```

**Command Types:**
- `keystroke`: Send key combinations (works in both command and dictation mode)
- `type`: Type predefined text (perfect for dictation shortcuts)
- `command`: Run system commands

**Categories:**
- `custom`: Regular voice commands (require wake word like "activate take screenshot")
- `dictation`: Dictation shortcuts (work during dictation mode without wake words)

## Architecture

The system consists of several key components:

- **Voice Recognition** (`src/voice_recognition.py`): OpenAI Whisper integration with voice activity detection
- **Keystroke Manager** (`src/keystroke_manager.py`): Cross-platform keystroke automation
- **Command Processor** (`src/command_processor.py`): Command interpretation and execution
- **GUI** (`src/gui.py`): Graphical user interface
- **Configuration** (`src/config.py`): Settings management

## API Reference

### VoiceRecognizer

```python
recognizer = VoiceRecognizer(config)

# Single recognition
text = await recognizer.recognize_once()

# Continuous recognition
async for text in recognizer.continuous_recognition():
    print(f"Recognized: {text}")
```

### KeystrokeManager

```python
keystroke_manager = KeystrokeManager()

# Type text
await keystroke_manager.type_text("Hello, World!")

# Send key combination
await keystroke_manager.send_key_combination("ctrl+c")

# Focus window
await keystroke_manager.focus_window("Firefox")
```

### CommandProcessor

```python
processor = CommandProcessor(config, keystroke_manager)

# Process voice command
await processor.process_command("open firefox")

# Add custom command
processor._register_command(Command(...))
```

## Troubleshooting

### Audio Issues

1. **No microphone detected**:
   - Check microphone permissions
   - Verify microphone is working in other applications
   - Try different audio devices in settings

2. **Poor recognition accuracy**:
   - Use a better microphone
   - Reduce background noise
   - Adjust silence threshold in settings
   - Try a larger Whisper model

### Platform-Specific Issues

**Linux**:
- Ensure X11/Wayland permissions for input simulation
- Install `xdotool` for window management
- Check audio group membership: `sudo usermod -a -G audio $USER`

**Windows**:
- Run as administrator for some applications
- Check Windows Security settings for input simulation
- Ensure microphone privacy settings allow access

**macOS**:
- Grant Accessibility permissions in System Preferences
- Allow microphone access in Privacy settings
- Install Xcode command line tools if needed

### Performance Optimization

1. **Faster recognition**:
   - Use Faster-Whisper engine for 2-4x speed improvement
   - Use larger models (large-v3) for better accuracy without speed penalty
   - Enable CUDA GPU acceleration
   - Use float16 compute type for modern GPUs
   - Set specific language (e.g., 'en') instead of auto-detection

2. **Best accuracy**:
   - Use `large-v3` model size (latest and most accurate)
   - Set `beam_size: 5` and `best_of: 5` for better results
   - Use Faster-Whisper with `compute_type: float16`
   - Ensure good microphone and minimize background noise

3. **Lower memory usage**:
   - Use smaller models (tiny, base, small)
   - Use `compute_type: int8` instead of float16
   - Reduce audio buffer sizes
   - Close unnecessary applications

**Recommended Settings for RTX GPUs:**
```yaml
whisper:
  engine: faster-whisper
  model_size: large-v3
  device: cuda
  compute_type: float16
  language: en
  beam_size: 5
  best_of: 5
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- OpenAI for the Whisper speech recognition model
- Contributors to pynput, pyaudio, and other dependencies
- The open-source community for cross-platform automation libraries