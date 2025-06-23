# Voice Control & Dictation System

A comprehensive voice control and dictation system using OpenAI Whisper for speech recognition with bulletproof cross-platform keystroke automation capabilities.

## Features

- **High-Quality Speech Recognition**: Uses OpenAI Whisper for accurate speech-to-text conversion
- **Cross-Platform Support**: Works on Linux, Windows, and macOS
- **Bulletproof Keystroke Automation**: Reliable keystroke sending to any window or application
- **Voice Dictation**: Real-time text dictation in any application
- **Voice Commands**: Comprehensive set of voice commands for desktop automation
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

### Configuration

Edit `config.yaml` to customize:

- **Audio settings**: Sample rate, silence detection
- **Whisper model**: Model size (tiny, base, small, medium, large)
- **Wake words**: Customize activation phrases
- **Custom commands**: Add your own voice commands

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
```

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
   - Use smaller Whisper models (tiny, base)
   - Reduce audio sample rate
   - Use GPU acceleration if available

2. **Lower memory usage**:
   - Use "tiny" Whisper model
   - Reduce audio buffer sizes
   - Close unnecessary applications

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