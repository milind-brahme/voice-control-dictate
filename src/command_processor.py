"""
Command Processing Module
Handles interpretation and execution of voice commands
"""

import asyncio
import logging
import re
import subprocess
import webbrowser
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
import platform

@dataclass
class Command:
    """Data class for command definition"""
    name: str
    patterns: List[str]
    handler: Callable
    description: str
    category: str = "general"

class CommandProcessor:
    def __init__(self, config, keystroke_manager):
        self.config = config
        self.keystroke_manager = keystroke_manager
        self.logger = logging.getLogger(__name__)
        
        # Command state
        self.dictation_mode = False
        self.listening_for_commands = True
        
        # Wake words and stop words
        self.wake_words = config.get('commands.wake_words', ['activate', 'computer', 'hey assistant'])
        self.stop_dictation_words = config.get('commands.stop_dictation', ['stop dictation', 'end dictation'])
        self.start_dictation_words = config.get('commands.start_dictation', ['start dictation', 'begin dictation'])
        
        # Initialize command registry
        self.commands: Dict[str, Command] = {}
        self._register_default_commands()
        self._load_custom_commands()
        
    def _register_default_commands(self):
        """Register default system commands"""
        
        # Dictation control
        self._register_command(Command(
            "start_dictation",
            self.start_dictation_words + ["dictation mode", "start typing"],
            self._start_dictation,
            "Start dictation mode",
            "dictation"
        ))
        
        self._register_command(Command(
            "stop_dictation", 
            self.stop_dictation_words + ["dictation off", "stop typing"],
            self._stop_dictation,
            "Stop dictation mode",
            "dictation"
        ))
        
        # Application control
        self._register_command(Command(
            "open_application",
            [r"open (\w+)", r"launch (\w+)", r"start (\w+)"],
            self._open_application,
            "Open an application",
            "applications"
        ))
        
        self._register_command(Command(
            "close_application",
            [r"close (\w+)", r"quit (\w+)", r"exit (\w+)"],
            self._close_application,
            "Close an application",
            "applications"
        ))
        
        # Browser control
        self._register_command(Command(
            "open_website",
            [r"open website (.+)", r"go to (.+)", r"browse (.+)", r"visit (.+)"],
            self._open_website,
            "Open a website in browser",
            "browser"
        ))
        
        self._register_command(Command(
            "search_web",
            [r"search for (.+)", r"google (.+)", r"look up (.+)"],
            self._search_web,
            "Search the web",
            "browser"
        ))
        
        # Window management
        self._register_command(Command(
            "switch_window",
            [r"switch to (.+)", r"focus (.+)", r"show (.+)"],
            self._switch_window,
            "Switch to a specific window",
            "windows"
        ))
        
        self._register_command(Command(
            "minimize_window",
            ["minimize", "minimize window"],
            self._minimize_window,
            "Minimize current window",
            "windows"
        ))
        
        self._register_command(Command(
            "maximize_window",
            ["maximize", "maximize window"],
            self._maximize_window,
            "Maximize current window", 
            "windows"
        ))
        
        # Keyboard shortcuts
        self._register_command(Command(
            "copy",
            ["copy", "copy text"],
            lambda: self.keystroke_manager.send_key_combination("ctrl+c"),
            "Copy selected text",
            "shortcuts"
        ))
        
        self._register_command(Command(
            "paste",
            ["paste", "paste text"],
            lambda: self.keystroke_manager.send_key_combination("ctrl+v"),
            "Paste text",
            "shortcuts"
        ))
        
        self._register_command(Command(
            "cut",
            ["cut", "cut text"],
            lambda: self.keystroke_manager.send_key_combination("ctrl+x"),
            "Cut selected text",
            "shortcuts"
        ))
        
        self._register_command(Command(
            "undo",
            ["undo", "undo that"],
            lambda: self.keystroke_manager.send_key_combination("ctrl+z"),
            "Undo last action",
            "shortcuts"
        ))        
        self._register_command(Command(
            "redo",
            ["redo", "redo that"],
            lambda: self.keystroke_manager.send_key_combination("ctrl+y"),
            "Redo last action",
            "shortcuts"
        ))
        
        self._register_command(Command(
            "select_all",
            ["select all", "select everything"],
            lambda: self.keystroke_manager.send_key_combination("ctrl+a"),
            "Select all text",
            "shortcuts"
        ))        
        # Text input
        self._register_command(Command(
            "type_text",
            [r"type (.+)", r"write (.+)", r"input (.+)"],
            self._type_text,
            "Type the specified text",
            "text"
        ))
        
        # Navigation
        self._register_command(Command(
            "new_tab",
            ["new tab", "open tab"],
            lambda: self.keystroke_manager.send_key_combination("ctrl+t"),
            "Open new tab",
            "navigation"
        ))
        
        self._register_command(Command(
            "close_tab",
            ["close tab"],
            lambda: self.keystroke_manager.send_key_combination("ctrl+w"),
            "Close current tab",
            "navigation"
        ))
        
        self._register_command(Command(
            "next_tab",
            ["next tab", "switch tab"],
            lambda: self.keystroke_manager.send_key_combination("ctrl+tab"),
            "Switch to next tab",
            "navigation"
        ))
        
        # System control
        self._register_command(Command(
            "lock_screen",
            ["lock screen", "lock computer"],
            self._lock_screen,
            "Lock the screen",
            "system"
        ))
        
        # Help and status
        self._register_command(Command(
            "help",
            ["help", "show commands", "what can you do"],
            self._show_help,
            "Show available commands",
            "help"
        ))
        
        self._register_command(Command(
            "status",
            ["status", "current mode"],
            self._show_status,
            "Show current status",
            "help"
        ))
    
        # Text input commands
        self._register_command(Command(
            "type_text",
            [r"type (.+)", r"write (.+)", r"input (.+)"],
            self._type_text,
            "Type the specified text",
            "input"
        ))
        
        self._register_command(Command(
            "press_key",
            [r"press (.+)", r"hit (.+)", r"key (.+)"],
            self._press_key,
            "Press the specified key",
            "input"
        ))
        
    def _register_command(self, command: Command):
        """Register a command in the command registry"""
        self.commands[command.name] = command
        self.logger.debug(f"Registered command: {command.name}")
    
    def _load_custom_commands(self):
        """Load custom commands from configuration"""
        custom_commands = self.config.get('commands.custom', {})
        
        for cmd_name, cmd_data in custom_commands.items():
            try:
                command = Command(
                    name=cmd_name,
                    patterns=cmd_data.get('patterns', []),
                    handler=self._create_custom_handler(cmd_data),
                    description=cmd_data.get('description', ''),
                    category=cmd_data.get('category', 'custom')
                )
                self._register_command(command)
            except Exception as e:
                self.logger.error(f"Failed to load custom command '{cmd_name}': {e}")
    
    def _create_custom_handler(self, cmd_data):
        """Create handler for custom command"""
        action_type = cmd_data.get('type', 'keystroke')
        action_data = cmd_data.get('action', '')
        
        if action_type == 'keystroke':
            async def handler():
                await self.keystroke_manager.send_key_combination(action_data)
            return handler
        elif action_type == 'type':
            async def handler():
                await self.keystroke_manager.type_text(action_data)
            return handler
        elif action_type == 'command':
            def handler():
                return subprocess.run(action_data, shell=True)
            return handler
        else:
            def handler():
                self.logger.warning(f"Unknown command type: {action_type}")
            return handler
    
    async def process_command(self, text: str):
        """Process a voice command"""
        text = text.strip().lower()
        
        if not text:
            return
            
        self.logger.info(f"Processing: {text}")
        
        # Check if in dictation mode
        if self.dictation_mode:
            self.logger.info(f"Dictation mode: Processing '{text}'")
            
            # Check for stop dictation commands
            if any(stop_word in text for stop_word in self.stop_dictation_words):
                await self._stop_dictation()
                return
            
            # Check for "press key" commands during dictation
            key_command_executed = await self._check_press_key_commands(text)
            if key_command_executed:
                self.logger.info(f"Key command executed successfully for: '{text}'")
                return
            
            # Check for custom commands during dictation
            custom_command_executed = await self._check_custom_commands_in_dictation(text)
            if custom_command_executed:
                self.logger.info(f"Custom command executed successfully for: '{text}'")
                return
            
            # Otherwise, type the text
            self.logger.info(f"Typing as dictation text: '{text}'")
            await self.keystroke_manager.type_text(text + " ")
            return
          # Check for wake word activation
        if not self._has_wake_word(text):
            self.logger.debug(f"No wake word found in: '{text}' - ignoring")
            return
              # Remove wake words from text
        command_text = self._remove_wake_words(text)
        self.logger.debug(f"After removing wake words: '{command_text}'")
        
        # Try to match and execute command
        command_executed = await self._execute_command(command_text)
        
        # If no command was executed and we're not in dictation mode, 
        # do NOT type the remaining text as that causes the duplication issue
        if not command_executed:
            self.logger.debug(f"No command matched for '{command_text}' - not typing as text")
    
    def _has_wake_word(self, text: str) -> bool:
        """Check if text contains a wake word"""
        text_words = text.split()
        for wake_word in self.wake_words:
            wake_word_parts = wake_word.split()
            # Check if all parts of the wake word are present in sequence
            for i in range(len(text_words) - len(wake_word_parts) + 1):
                if text_words[i:i+len(wake_word_parts)] == wake_word_parts:
                    self.logger.debug(f"Found wake word '{wake_word}' in text")
                    return True
        return False
    
    def _remove_wake_words(self, text: str) -> str:
        """Remove wake words from text"""
        text_words = text.split()
        for wake_word in self.wake_words:
            wake_word_parts = wake_word.split()
            # Find and remove wake word sequence
            for i in range(len(text_words) - len(wake_word_parts) + 1):
                if text_words[i:i+len(wake_word_parts)] == wake_word_parts:
                    # Remove the wake word parts
                    text_words = text_words[:i] + text_words[i+len(wake_word_parts):]
                    break
        return " ".join(text_words).strip()
    
    async def _execute_command(self, text: str):
        """Execute a matched command"""
        command_executed = False
        
        for command in self.commands.values():
            for pattern in command.patterns:
                # Try regex match first
                if '(' in pattern:  # Regex pattern
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        try:
                            self.logger.debug(f"Regex match found for pattern '{pattern}' in command '{command.name}'")
                            if asyncio.iscoroutinefunction(command.handler):
                                await command.handler(*match.groups())
                            else:
                                await asyncio.get_event_loop().run_in_executor(
                                    None, command.handler, *match.groups()
                                )
                            self.logger.info(f"Successfully executed command: {command.name} with args: {match.groups()}")
                            command_executed = True
                            return True  # Return True to indicate command was executed
                        except Exception as e:
                            self.logger.error(f"Error executing command '{command.name}': {e}")
                            return False
                
                # Try exact match
                elif pattern in text:
                    try:
                        self.logger.debug(f"Exact match found for pattern '{pattern}' in command '{command.name}'")
                        if asyncio.iscoroutinefunction(command.handler):
                            await command.handler()
                        else:
                            await asyncio.get_event_loop().run_in_executor(
                                None, command.handler
                            )
                        self.logger.info(f"Successfully executed command: {command.name}")
                        command_executed = True
                        return True  # Return True to indicate command was executed
                    except Exception as e:
                        self.logger.error(f"Error executing command '{command.name}': {e}")
                        return False
        
        if not command_executed:
            self.logger.debug(f"No command found for: '{text}'")
        return False  # Return False to indicate no command was executed
    
    # Command handlers
    async def _start_dictation(self):
        """Start dictation mode"""
        self.dictation_mode = True
        self.logger.info("Dictation mode started")
    
    async def _stop_dictation(self):
        """Stop dictation mode"""
        self.dictation_mode = False
        self.logger.info("Dictation mode stopped")
    
    async def _open_application(self, app_name: str):
        """Open an application"""
        try:
            system = platform.system().lower()
            
            if system == "linux":
                # Try common application names
                subprocess.Popen([app_name])
            elif system == "windows":
                subprocess.Popen([app_name])
            elif system == "darwin":  # macOS
                subprocess.Popen(["open", "-a", app_name])
                
            self.logger.info(f"Opened application: {app_name}")
        except Exception as e:
            self.logger.error(f"Failed to open application '{app_name}': {e}")
    
    async def _close_application(self, app_name: str):
        """Close an application"""
        try:
            system = platform.system().lower()
            
            if system == "linux":
                subprocess.run(["pkill", "-f", app_name])
            elif system == "windows":
                subprocess.run(["taskkill", "/f", "/im", f"{app_name}.exe"])
            elif system == "darwin":  # macOS
                subprocess.run(["pkill", "-f", app_name])
                
            self.logger.info(f"Closed application: {app_name}")
        except Exception as e:
            self.logger.error(f"Failed to close application '{app_name}': {e}")
    
    async def _open_website(self, url: str):
        """Open a website in the default browser"""
        try:
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                if '.' in url:
                    url = f"https://{url}"
                else:
                    url = f"https://www.google.com/search?q={url}"
            
            webbrowser.open(url)
            self.logger.info(f"Opened website: {url}")
        except Exception as e:
            self.logger.error(f"Failed to open website '{url}': {e}")
    
    async def _search_web(self, query: str):
        """Search the web"""
        try:
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            webbrowser.open(search_url)
            self.logger.info(f"Searched for: {query}")
        except Exception as e:
            self.logger.error(f"Failed to search for '{query}': {e}")
    
    async def _switch_window(self, window_name: str):
        """Switch to a specific window"""
        success = await self.keystroke_manager.focus_window(window_name)
        if success:
            self.logger.info(f"Switched to window: {window_name}")
        else:
            self.logger.warning(f"Could not find window: {window_name}")
    
    async def _minimize_window(self):
        """Minimize current window"""
        system = platform.system().lower()
        if system == "windows":
            await self.keystroke_manager.send_key_combination("win+down")
        else:
            await self.keystroke_manager.send_key_combination("ctrl+alt+9")
    
    async def _maximize_window(self):
        """Maximize current window"""
        system = platform.system().lower()
        if system == "windows":
            await self.keystroke_manager.send_key_combination("win+up")
        else:
            await self.keystroke_manager.send_key_combination("ctrl+alt+0")
    
    async def _lock_screen(self):
        """Lock the screen"""
        system = platform.system().lower()
        try:
            if system == "linux":
                subprocess.run(["gnome-screensaver-command", "-l"])
            elif system == "windows":
                await self.keystroke_manager.send_key_combination("win+l")
            elif system == "darwin":  # macOS
                subprocess.run(["/System/Library/CoreServices/Menu Extras/User.menu/Contents/Resources/CGSession", "-suspend"])
        except Exception as e:
            self.logger.error(f"Failed to lock screen: {e}")
    
    async def _show_help(self):
        """Show available commands"""
        help_text = "Available commands:\n\n"
        
        categories = {}
        for command in self.commands.values():
            if command.category not in categories:
                categories[command.category] = []
            categories[command.category].append(command)
        
        for category, cmds in categories.items():
            help_text += f"{category.upper()}:\n"
            for cmd in cmds:
                help_text += f"  - {cmd.description}\n"
            help_text += "\n"
        
        self.logger.info("Help requested")
        print(help_text)
    
    async def _show_status(self):
        """Show current status"""
        mode = "Dictation" if self.dictation_mode else "Command"
        window_info = self.keystroke_manager.get_active_window_info()
        
        status = f"Mode: {mode}\n"
        if window_info:
            status += f"Active Window: {window_info.get('title', 'Unknown')}\n"
        
        self.logger.info("Status requested")
        print(status)
    
    def get_commands_by_category(self) -> Dict[str, List[Command]]:
        """Get commands organized by category"""
        categories = {}
        for command in self.commands.values():
            if command.category not in categories:
                categories[command.category] = []
            categories[command.category].append(command)
        return categories
    
    async def _type_text(self, text: str):
        """Type the specified text"""
        try:
            await self.keystroke_manager.type_text(text)
            self.logger.info(f"Typed text: {text}")
        except Exception as e:
            self.logger.error(f"Failed to type text '{text}': {e}")
    
    async def _press_key(self, key: str):
        """Press the specified key or key combination"""
        try:
            # Handle key combinations like "ctrl a", "shift enter", etc.
            if ' ' in key:
                parts = key.split()
                if len(parts) == 2:
                    modifier, main_key = parts
                    await self.keystroke_manager.send_key(main_key, [modifier])
                else:
                    # Multiple modifiers: ctrl shift a
                    main_key = parts[-1]
                    modifiers = parts[:-1]
                    await self.keystroke_manager.send_key(main_key, modifiers)
            else:
                # Single key
                await self.keystroke_manager.send_key(key)
            
            self.logger.info(f"Pressed key: {key}")
        except Exception as e:
            self.logger.error(f"Failed to press key '{key}': {e}")
    
    async def _check_press_key_commands(self, text: str) -> bool:
        """
        Check if the text contains a "press key" command during dictation mode.
        Returns True if a key command was executed, False otherwise.
        """
        text_lower = text.lower().strip()
        
        # Define more specific patterns for "press key" commands to avoid false positives
        # These patterns handle punctuation and are more flexible
        press_key_patterns = [
            r"press key (.+?)\.?$",        # "press key enter" or "press key enter."
            r"press (.+?) key\.?$",        # "press enter key" or "press enter key."
            r"hit key (.+?)\.?$",          # "hit key backspace" or "hit key backspace."
            r"hit (.+?) key\.?$",          # "hit escape key" or "hit escape key."
            r"^key (.+?)\.?$",             # "key tab" or "key tab."
            r"^press (enter|tab|space|escape|backspace|delete|home|end|up|down|left|right|page up|page down|f\d+)\.?$",  # Direct key commands
            r"^hit (enter|tab|space|escape|backspace|delete|home|end|up|down|left|right|page up|page down|f\d+)\.?$",    # "hit enter", "hit tab", etc.
            r"press (ctrl|shift|alt) (.+?)\.?$",  # "press ctrl c", "press shift tab", etc.
            r"hit (ctrl|shift|alt) (.+?)\.?$",    # "hit ctrl c", "hit shift tab", etc.
        ]
        
        for pattern in press_key_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                # Handle different pattern groups
                if "ctrl" in pattern or "shift" in pattern or "alt" in pattern:
                    # For modifier patterns like "press ctrl c"
                    if match.lastindex == 2:
                        modifier = match.group(1).strip()
                        key = match.group(2).strip().rstrip('.')
                        key_name = f"{modifier} {key}"
                    else:
                        key_name = match.group(1).strip().rstrip('.')
                else:
                    # For regular patterns
                    key_name = match.group(1).strip().rstrip('.')
                
                self.logger.info(f"Detected press key command during dictation: '{key_name}'")
                
                try:
                    # Execute the key press
                    await self._press_key(key_name)
                    return True
                except Exception as e:
                    self.logger.error(f"Error executing press key command '{key_name}': {e}")
                    return False
        
        return False
    
    async def _check_custom_commands_in_dictation(self, text: str) -> bool:
        """Check if the text matches any custom commands during dictation mode"""
        text_lower = text.lower().strip()
        
        # Iterate through all registered commands to find custom ones
        for command_name, command in self.commands.items():
            # Only check custom commands or commands with 'dictation' category
            if command.category not in ['custom', 'dictation']:
                continue
                
            # Check if any pattern matches
            for pattern in command.patterns:
                pattern_lower = pattern.lower()
                
                # Check for exact match or if the pattern is contained in the text
                if pattern_lower == text_lower or pattern_lower in text_lower:
                    self.logger.info(f"Custom command matched during dictation: '{pattern}' -> '{command.description}'")
                    
                    try:
                        # Execute the custom command
                        if asyncio.iscoroutinefunction(command.handler):
                            await command.handler()
                        else:
                            result = command.handler()
                            if asyncio.iscoroutine(result):
                                await result
                        
                        return True
                    except Exception as e:
                        self.logger.error(f"Error executing custom command '{pattern}': {e}")
                        return False
        
        return False