"""
Cross-platform keystroke management system
Handles sending keystrokes to any active window with bulletproof reliability
"""

import asyncio
import logging
import platform
import time
from typing import Dict, List, Optional, Union

# Platform-specific imports
system = platform.system().lower()

if system == "linux":
    try:
        import pynput
        from pynput import keyboard as pynput_keyboard
        from pynput.keyboard import Key, KeyCode
        import subprocess
        import Xlib
        from Xlib import X, display
        from Xlib.ext import record
        from Xlib.protocol import rq
    except ImportError as e:
        logging.warning(f"Linux dependencies not available: {e}")

elif system == "windows":
    try:
        import win32api
        import win32con
        import win32gui
        import win32process
        import ctypes
        from ctypes import wintypes
    except ImportError as e:
        logging.warning(f"Windows dependencies not available: {e}")

elif system == "darwin":  # macOS
    try:
        import pynput
        from pynput import keyboard as pynput_keyboard
        from pynput.keyboard import Key, KeyCode
        import subprocess
    except ImportError as e:
        logging.warning(f"macOS dependencies not available: {e}")

class KeystrokeManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.system = platform.system().lower()
        
        # Initialize platform-specific components
        if self.system == "linux":
            self._init_linux()
        elif self.system == "windows":
            self._init_windows()
        elif self.system == "darwin":
            self._init_macos()
        else:
            raise RuntimeError(f"Unsupported platform: {self.system}")
            
        # Common key mappings
        self.key_mappings = self._build_key_mappings()
        
    def _init_linux(self):
        """Initialize Linux-specific components"""
        try:
            self.display = display.Display()
            self.controller = pynput.keyboard.Controller()
            self.logger.info("Linux keystroke manager initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Linux components: {e}")
            raise
    
    def _init_windows(self):
        """Initialize Windows-specific components"""
        try:
            # Get user32 and kernel32 for low-level operations
            self.user32 = ctypes.windll.user32
            self.kernel32 = ctypes.windll.kernel32
            self.controller = pynput.keyboard.Controller()
            self.logger.info("Windows keystroke manager initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Windows components: {e}")
            raise
    
    def _init_macos(self):
        """Initialize macOS-specific components"""
        try:
            self.controller = pynput.keyboard.Controller()
            self.logger.info("macOS keystroke manager initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize macOS components: {e}")
            raise
    
    def _build_key_mappings(self) -> Dict[str, Union[str, Key]]:
        """Build key mappings for special keys"""
        mappings = {
            'enter': Key.enter,
            'return': Key.enter,
            'tab': Key.tab,
            'space': Key.space,
            'backspace': Key.backspace,
            'delete': Key.delete,
            'escape': Key.esc,
            'esc': Key.esc,
            'shift': Key.shift,
            'ctrl': Key.ctrl,
            'control': Key.ctrl,
            'alt': Key.alt,
            'cmd': Key.cmd if hasattr(Key, 'cmd') else Key.ctrl,
            'command': Key.cmd if hasattr(Key, 'cmd') else Key.ctrl,
            'win': Key.cmd if hasattr(Key, 'cmd') else Key.ctrl,
            'windows': Key.cmd if hasattr(Key, 'cmd') else Key.ctrl,
            'up': Key.up,
            'down': Key.down,
            'left': Key.left,
            'right': Key.right,
            'home': Key.home,
            'end': Key.end,
            'page_up': Key.page_up,
            'page_down': Key.page_down,
            'f1': Key.f1, 'f2': Key.f2, 'f3': Key.f3, 'f4': Key.f4,
            'f5': Key.f5, 'f6': Key.f6, 'f7': Key.f7, 'f8': Key.f8,
            'f9': Key.f9, 'f10': Key.f10, 'f11': Key.f11, 'f12': Key.f12,
        }
        return mappings
    
    async def type_text(self, text: str, delay: float = 0.01):
        """Type text character by character with optional delay"""
        try:
            self.logger.debug(f"Typing text: {text[:50]}...")
            
            # Use thread executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._type_text_sync, text, delay)
            
        except Exception as e:
            self.logger.error(f"Error typing text: {e}")
            raise
    
    def _type_text_sync(self, text: str, delay: float):
        """Synchronous text typing implementation"""
        for char in text:
            try:
                self.controller.type(char)
                if delay > 0:
                    time.sleep(delay)
            except Exception as e:
                self.logger.warning(f"Failed to type character '{char}': {e}")
    
    async def send_key(self, key: str, modifiers: Optional[List[str]] = None):
        """Send a single key with optional modifiers"""
        try:
            # Parse key
            if key.lower() in self.key_mappings:
                key_obj = self.key_mappings[key.lower()]
            else:
                key_obj = KeyCode.from_char(key) if len(key) == 1 else key
            
            # Parse modifiers
            modifier_keys = []
            if modifiers:
                for mod in modifiers:
                    if mod.lower() in self.key_mappings:
                        modifier_keys.append(self.key_mappings[mod.lower()])
            
            # Send key combination
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, self._send_key_sync, key_obj, modifier_keys
            )
            
        except Exception as e:
            self.logger.error(f"Error sending key '{key}': {e}")
            raise
    
    def _send_key_sync(self, key, modifiers):
        """Synchronous key sending implementation"""
        try:
            # Press modifiers
            for mod in modifiers:
                self.controller.press(mod)
            
            # Press and release main key
            if isinstance(key, str):
                self.controller.type(key)
            else:
                self.controller.press(key)
                self.controller.release(key)
            
            # Release modifiers
            for mod in reversed(modifiers):
                self.controller.release(mod)
                
        except Exception as e:
            self.logger.error(f"Failed to send key combination: {e}")
            raise
    
    async def send_key_combination(self, combination: str):
        """Send key combination from string like 'ctrl+c' or 'alt+tab'"""
        try:
            parts = [part.strip().lower() for part in combination.split('+')]
            if len(parts) < 2:
                await self.send_key(parts[0])
                return
            
            modifiers = parts[:-1]
            key = parts[-1]
            
            await self.send_key(key, modifiers)
            
        except Exception as e:
            self.logger.error(f"Error sending key combination '{combination}': {e}")
            raise
    
    def get_active_window_info(self) -> Dict:
        """Get information about the currently active window"""
        try:
            if self.system == "linux":
                return self._get_active_window_linux()
            elif self.system == "windows":
                return self._get_active_window_windows()
            elif self.system == "darwin":
                return self._get_active_window_macos()
        except Exception as e:
            self.logger.error(f"Error getting active window info: {e}")
            return {}
    
    def _get_active_window_linux(self) -> Dict:
        """Get active window info on Linux"""
        try:
            result = subprocess.run(
                ['xdotool', 'getactivewindow', 'getwindowname'],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                return {'title': result.stdout.strip()}
        except:
            pass
        return {}
    
    def _get_active_window_windows(self) -> Dict:
        """Get active window info on Windows"""
        try:
            hwnd = self.user32.GetForegroundWindow()
            if hwnd:
                # Get window title
                length = self.user32.GetWindowTextLengthW(hwnd)
                buff = ctypes.create_unicode_buffer(length + 1)
                self.user32.GetWindowTextW(hwnd, buff, length + 1)
                
                # Get process info
                pid = wintypes.DWORD()
                self.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                
                return {
                    'title': buff.value,
                    'hwnd': hwnd,
                    'pid': pid.value
                }
        except:
            pass
        return {}
    
    def _get_active_window_macos(self) -> Dict:
        """Get active window info on macOS"""
        try:
            result = subprocess.run([
                'osascript', '-e',
                'tell application "System Events" to get name of first application process whose frontmost is true'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                return {'title': result.stdout.strip()}
        except:
            pass
        return {}
    
    async def focus_window(self, window_title: str) -> bool:
        """Focus a window by title (partial match)"""
        try:
            if self.system == "linux":
                return await self._focus_window_linux(window_title)
            elif self.system == "windows":
                return await self._focus_window_windows(window_title)
            elif self.system == "darwin":
                return await self._focus_window_macos(window_title)
        except Exception as e:
            self.logger.error(f"Error focusing window '{window_title}': {e}")
        return False
    
    async def _focus_window_linux(self, window_title: str) -> bool:
        """Focus window on Linux"""
        try:
            result = subprocess.run([
                'xdotool', 'search', '--name', window_title, 'windowactivate'
            ], capture_output=True)
            return result.returncode == 0
        except:
            return False
    
    async def _focus_window_windows(self, window_title: str) -> bool:
        """Focus window on Windows"""
        def enum_windows_callback(hwnd, windows):
            if self.user32.IsWindowVisible(hwnd):
                length = self.user32.GetWindowTextLengthW(hwnd)
                buff = ctypes.create_unicode_buffer(length + 1)
                self.user32.GetWindowTextW(hwnd, buff, length + 1)
                windows.append((hwnd, buff.value))
            return True
        
        try:
            windows = []
            enum_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.POINTER(ctypes.c_int))
            self.user32.EnumWindows(enum_proc(enum_windows_callback), ctypes.byref(ctypes.c_int()))
            
            for hwnd, title in windows:
                if window_title.lower() in title.lower():
                    self.user32.SetForegroundWindow(hwnd)
                    return True
        except:
            pass
        return False
    
    async def _focus_window_macos(self, window_title: str) -> bool:
        """Focus window on macOS"""
        try:
            result = subprocess.run([
                'osascript', '-e',
                f'tell application "{window_title}" to activate'
            ], capture_output=True)
            return result.returncode == 0
        except:
            return False