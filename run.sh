#!/bin/bash

# Voice Control & Dictation System Launcher Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Voice Control & Dictation System${NC}"
echo "=================================="

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    echo -e "${GREEN}✓${NC} Python $python_version detected"
else
    echo -e "${RED}✗${NC} Python $required_version or higher required. Found: $python_version"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install/upgrade dependencies
if [ ! -f "venv/installed" ] || [ "requirements.txt" -nt "venv/installed" ]; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install --upgrade pip
    pip install -r requirements.txt
    touch venv/installed
    echo -e "${GREEN}✓${NC} Dependencies installed"
else
    echo -e "${GREEN}✓${NC} Dependencies up to date"
fi

# Platform-specific setup
case "$(uname -s)" in
    Linux*)
        echo -e "${YELLOW}Checking Linux dependencies...${NC}"
        
        # Check for required system packages
        missing_packages=()
        
        if ! command -v xdotool &> /dev/null; then
            missing_packages+=("xdotool")
        fi
        
        if ! ldconfig -p | grep -q libportaudio; then
            missing_packages+=("portaudio19-dev")
        fi
        
        if [ ${#missing_packages[@]} -ne 0 ]; then
            echo -e "${RED}Missing system packages: ${missing_packages[*]}${NC}"
            echo "Please install them using:"
            echo "  Ubuntu/Debian: sudo apt install ${missing_packages[*]}"
            echo "  Fedora: sudo dnf install portaudio-devel xdotool"
            echo "  Arch: sudo pacman -S portaudio xdotool"
            exit 1
        fi
        
        echo -e "${GREEN}✓${NC} Linux dependencies OK"
        ;;
    Darwin*)
        echo -e "${YELLOW}Checking macOS dependencies...${NC}"
        if ! command -v brew &> /dev/null; then
            echo -e "${YELLOW}Warning: Homebrew not found. Some features may not work.${NC}"
        fi
        echo -e "${GREEN}✓${NC} macOS setup complete"
        ;;
    CYGWIN*|MINGW32*|MSYS*|MINGW*)
        echo -e "${YELLOW}Windows environment detected${NC}"
        echo -e "${GREEN}✓${NC} Windows setup complete"
        ;;
    *)
        echo -e "${YELLOW}Unknown platform: $(uname -s)${NC}"
        ;;
esac

# Check microphone access
echo -e "${YELLOW}Testing microphone access...${NC}"
python3 -c "
import pyaudio
try:
    p = pyaudio.PyAudio()
    devices = []
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            devices.append(info['name'])
    p.terminate()
    if devices:
        print('✓ Audio devices found:', len(devices))
    else:
        print('✗ No audio input devices found')
        exit(1)
except Exception as e:
    print('✗ Audio test failed:', e)
    exit(1)
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Microphone access OK"
else
    echo -e "${RED}✗${NC} Microphone access failed"
    echo "Please check:"
    echo "  - Microphone is connected and working"
    echo "  - Audio permissions are granted"
    echo "  - Audio drivers are installed"
    exit 1
fi

# Launch application
echo ""
echo -e "${GREEN}Starting Voice Control & Dictation System...${NC}"
echo "Press Ctrl+C to stop"
echo ""

# Parse command line arguments
MODE="gui"
ARGS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --cli)
            MODE="cli"
            ARGS="$ARGS --mode cli"
            shift
            ;;
        --dictation)
            ARGS="$ARGS --dictation-mode"
            shift
            ;;
        --config)
            ARGS="$ARGS --config $2"
            shift 2
            ;;
        --log-level)
            ARGS="$ARGS --log-level $2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --cli              Run in CLI mode"
            echo "  --dictation        Start in dictation mode"
            echo "  --config FILE      Use custom config file"
            echo "  --log-level LEVEL  Set log level (DEBUG, INFO, WARNING, ERROR)"
            echo "  -h, --help         Show this help"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Run the application
exec python3 main.py $ARGS