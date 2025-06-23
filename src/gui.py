"""
GUI Module for Voice Control System
Provides a user-friendly interface for configuration and control
"""

import asyncio
import logging
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
from typing import Optional
import pyaudio
import numpy as np
import time

class VoiceControlGUI:
    def __init__(self, voice_recognizer, command_processor, config):
        self.voice_recognizer = voice_recognizer
        self.command_processor = command_processor
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # GUI state
        self.is_listening = False
        self.recognition_task = None
        
        # Audio meter state
        self.audio_monitor_active = False
        self.audio_monitor_thread = None
        self.current_audio_level = 0
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("Voice Control & Dictation System")
        self.root.geometry("800x600")
        
        # Configure style
        self.style = ttk.Style()
        if self.config.get('gui.theme', 'light') == 'dark':
            self.style.theme_use('clam')
        
        self._create_widgets()
        self._setup_bindings()
        
        # Configure window properties
        if self.config.get('gui.always_on_top', False):
            self.root.attributes('-topmost', True)
    
    def _create_widgets(self):
        """Create GUI widgets"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Main control tab
        self._create_control_tab()
        
        # Commands tab
        self._create_commands_tab()
        
        # Settings tab
        self._create_settings_tab()
        
        # Log tab
        self._create_log_tab()
    
    def _create_control_tab(self):
        """Create main control tab"""
        control_frame = ttk.Frame(self.notebook)
        self.notebook.add(control_frame, text="Control")
        
        # Status section
        status_frame = ttk.LabelFrame(control_frame, text="Status")
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="Ready", font=("Arial", 12))
        self.status_label.pack(pady=10)
        
        self.mode_label = ttk.Label(status_frame, text="Mode: Command", font=("Arial", 10))
        self.mode_label.pack()
        
        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.start_button = ttk.Button(
            button_frame, text="Start Listening", 
            command=self._toggle_listening
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.dictation_button = ttk.Button(
            button_frame, text="Dictation Mode",
            command=self._toggle_dictation
        )
        self.dictation_button.pack(side=tk.LEFT, padx=5)
        
        # Recognition display
        recognition_frame = ttk.LabelFrame(control_frame, text="Recognition")
        recognition_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.recognition_text = scrolledtext.ScrolledText(
            recognition_frame, height=10, wrap=tk.WORD
        )
        self.recognition_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Audio level indicator
        audio_frame = ttk.Frame(control_frame)
        audio_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(audio_frame, text="Audio Level:").pack(side=tk.LEFT)
        self.audio_level = ttk.Progressbar(
            audio_frame, mode='determinate', maximum=100
        )
        self.audio_level.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    
    def _create_commands_tab(self):
        """Create commands reference tab"""
        commands_frame = ttk.Frame(self.notebook)
        self.notebook.add(commands_frame, text="Commands")
        
        # Commands tree
        tree_frame = ttk.Frame(commands_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create treeview
        columns = ("Command", "Pattern", "Description")
        self.commands_tree = ttk.Treeview(tree_frame, columns=columns, show="tree headings")
        
        # Configure columns
        self.commands_tree.heading("#0", text="Category")
        self.commands_tree.heading("Command", text="Command")
        self.commands_tree.heading("Pattern", text="Pattern")
        self.commands_tree.heading("Description", text="Description")
        
        self.commands_tree.column("#0", width=150)
        self.commands_tree.column("Command", width=150)
        self.commands_tree.column("Pattern", width=200)
        self.commands_tree.column("Description", width=250)
        
        # Add scrollbar
        tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.commands_tree.yview)
        self.commands_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.commands_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate commands
        self._populate_commands_tree()
    
    def _create_settings_tab(self):
        """Create settings tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")
        
        # Create notebook for settings categories
        settings_notebook = ttk.Notebook(settings_frame)
        settings_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Audio settings
        audio_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(audio_frame, text="Audio")
        
        # Whisper settings
        whisper_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(whisper_frame, text="Whisper")
        
        # Commands settings
        commands_frame = ttk.Frame(settings_notebook)
        settings_notebook.add(commands_frame, text="Commands")
        
        self._create_audio_settings(audio_frame)
        self._create_whisper_settings(whisper_frame)
        self._create_commands_settings(commands_frame)
    
    def _create_audio_settings(self, parent):
        """Create audio settings widgets"""
        # Audio device selection
        ttk.Label(parent, text="Audio Input Device:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.audio_device_var = tk.StringVar()
        self.audio_device_combo = ttk.Combobox(
            parent, textvariable=self.audio_device_var,
            state="readonly", width=40
        )
        self.audio_device_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Refresh devices button
        refresh_button = ttk.Button(parent, text="Refresh Devices", command=self._refresh_audio_devices)
        refresh_button.grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Sample rate
        ttk.Label(parent, text="Sample Rate:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.sample_rate_var = tk.StringVar(value=str(self.config.get('audio.sample_rate', 16000)))
        sample_rate_combo = ttk.Combobox(
            parent, textvariable=self.sample_rate_var,
            values=["8000", "16000", "22050", "44100", "48000"],
            state="readonly"
        )
        sample_rate_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Silence threshold
        ttk.Label(parent, text="Silence Threshold:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.silence_threshold_var = tk.DoubleVar(value=self.config.get('audio.silence_threshold', 500))
        silence_threshold_scale = ttk.Scale(
            parent, from_=100, to=1000, variable=self.silence_threshold_var,
            orient=tk.HORIZONTAL, length=200
        )
        silence_threshold_scale.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Silence duration
        ttk.Label(parent, text="Silence Duration (s):").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.silence_duration_var = tk.DoubleVar(value=self.config.get('audio.silence_duration', 2.0))
        silence_duration_scale = ttk.Scale(
            parent, from_=0.5, to=5.0, variable=self.silence_duration_var,
            orient=tk.HORIZONTAL, length=200
        )
        silence_duration_scale.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Initialize device list
        self._refresh_audio_devices()
    
    def _create_whisper_settings(self, parent):
        """Create Whisper settings widgets"""
        # Model size
        ttk.Label(parent, text="Model Size:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.model_size_var = tk.StringVar(value=self.config.get('whisper.model_size', 'base'))
        model_size_combo = ttk.Combobox(
            parent, textvariable=self.model_size_var,
            values=["tiny", "base", "small", "medium", "large"],
            state="readonly"
        )
        model_size_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Language
        ttk.Label(parent, text="Language:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.language_var = tk.StringVar(value=self.config.get('whisper.language', 'en'))
        language_combo = ttk.Combobox(
            parent, textvariable=self.language_var,
            values=["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh", "auto"],
            state="readonly", width=15
        )
        language_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Language help text
        language_help = ttk.Label(
            parent, 
            text="Language codes: en=English, es=Spanish, fr=French, de=German, auto=Auto-detect",
            font=("Arial", 8)
        )
        language_help.grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=(0,10))
    
    def _create_commands_settings(self, parent):
        """Create commands settings widgets"""
        # Wake words
        ttk.Label(parent, text="Wake Words:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.wake_words_var = tk.StringVar(
            value=", ".join(self.config.get('commands.wake_words', []))
        )
        wake_words_entry = ttk.Entry(parent, textvariable=self.wake_words_var, width=40)
        wake_words_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Save button
        save_button = ttk.Button(parent, text="Save Settings", command=self._save_settings)
        save_button.grid(row=4, column=1, sticky=tk.W, padx=5, pady=20)
    
    def _create_log_tab(self):
        """Create log viewing tab"""
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="Log")
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Log controls
        log_controls = ttk.Frame(log_frame)
        log_controls.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(log_controls, text="Clear Log", command=self._clear_log).pack(side=tk.LEFT)
        ttk.Button(log_controls, text="Refresh", command=self._refresh_log).pack(side=tk.LEFT, padx=5)
    
    def _setup_bindings(self):
        """Setup event bindings"""
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _populate_commands_tree(self):
        """Populate the commands tree with available commands"""
        try:
            commands_by_category = self.command_processor.get_commands_by_category()
            
            for category, commands in commands_by_category.items():
                category_node = self.commands_tree.insert("", "end", text=category.title())
                
                for command in commands:
                    patterns = ", ".join(command.patterns[:2])  # Show first 2 patterns
                    if len(command.patterns) > 2:
                        patterns += "..."
                    
                    self.commands_tree.insert(
                        category_node, "end",
                        values=(command.name, patterns, command.description)
                    )
        except Exception as e:
            self.logger.error(f"Failed to populate commands tree: {e}")
    
    def _toggle_listening(self):
        """Toggle listening state"""
        if not self.is_listening:
            self._start_listening()
        else:
            self._stop_listening()
    
    def _start_listening(self):
        """Start voice recognition"""
        try:
            self.is_listening = True
            self.start_button.config(text="Stop Listening", style="")
            self.status_label.config(text="Listening...")
            
            # Start recognition in separate thread
            self.recognition_task = asyncio.create_task(self._recognition_loop())
            self._start_audio_monitor()
            
        except Exception as e:
            self.logger.error(f"Failed to start listening: {e}")
            messagebox.showerror("Error", f"Failed to start listening: {e}")
    
    def _stop_listening(self):
        """Stop voice recognition"""
        try:
            self.is_listening = False
            self.start_button.config(text="Start Listening")
            self.status_label.config(text="Ready")
            
            if self.recognition_task:
                self.recognition_task.cancel()
            self._stop_audio_monitor()
            
        except Exception as e:
            self.logger.error(f"Failed to stop listening: {e}")
    
    def _toggle_dictation(self):
        """Toggle dictation mode"""
        if not self.command_processor.dictation_mode:
            self.command_processor.dictation_mode = True
            self.dictation_button.config(text="Exit Dictation")
            self.mode_label.config(text="Mode: Dictation")
        else:
            self.command_processor.dictation_mode = False
            self.dictation_button.config(text="Dictation Mode")
            self.mode_label.config(text="Mode: Command")
    
    async def _recognition_loop(self):
        """Main recognition loop"""
        try:
            async for text in self.voice_recognizer.continuous_recognition():
                if not self.is_listening:
                    break
                    
                if text:
                    # Update GUI
                    self.recognition_text.insert(tk.END, f"{text}\n")
                    self.recognition_text.see(tk.END)
                    
                    # Process command
                    await self._process_recognition(text)
                    
        except Exception as e:
            self.logger.error(f"Recognition loop error: {e}")
    
    async def _process_recognition(self, text: str):
        """Process recognized text through command processor"""
        try:
            # Process the recognized text through the command processor
            await self.command_processor.process_command(text)
        except Exception as e:
            self.logger.error(f"Command processing error: {e}")
            # Show error in GUI
            self.recognition_text.insert(tk.END, f"Error processing command: {e}\n")
            self.recognition_text.see(tk.END)
    
    def _start_audio_monitor(self):
        """Start audio level monitoring"""
        if not self.audio_monitor_active:
            self.audio_monitor_active = True
            self.audio_monitor_thread = threading.Thread(target=self._audio_monitor_loop, daemon=True)
            self.audio_monitor_thread.start()
            
            # Start GUI update timer
            self._update_audio_meter()
    
    def _stop_audio_monitor(self):
        """Stop audio level monitoring"""
        self.audio_monitor_active = False
        if self.audio_monitor_thread:
            self.audio_monitor_thread.join(timeout=1.0)
    
    def _audio_monitor_loop(self):
        """Audio monitoring loop running in separate thread"""
        try:
            # Get audio settings
            sample_rate = self.config.get('audio.sample_rate', 16000)
            chunk_size = self.config.get('audio.chunk_size', 1024)
            device_index = self.config.get('audio.input_device', None)
            
            # Initialize PyAudio
            audio = pyaudio.PyAudio()
            
            try:
                # Open audio stream
                stream = audio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=sample_rate,
                    input=True,
                    input_device_index=device_index,
                    frames_per_buffer=chunk_size
                )
                
                while self.audio_monitor_active:
                    try:
                        # Read audio data
                        data = stream.read(chunk_size, exception_on_overflow=False)
                        
                        # Calculate volume level with robust error handling
                        audio_np = np.frombuffer(data, dtype=np.int16)
                        if len(audio_np) > 0:
                            try:
                                # Calculate RMS with proper error handling
                                mean_square = np.mean(audio_np.astype(np.float64)**2)
                                if mean_square < 0 or np.isnan(mean_square) or np.isinf(mean_square):
                                    rms = 0.0
                                else:
                                    rms = np.sqrt(mean_square)
                                # Normalize to 0-100 scale
                                self.current_audio_level = min(100, (rms / 3000) * 100)
                            except Exception:
                                self.current_audio_level = 0
                        else:
                            self.current_audio_level = 0
                            
                    except Exception as e:
                        self.logger.debug(f"Audio monitor read error: {e}")
                        time.sleep(0.1)
                        
            finally:
                if 'stream' in locals():
                    stream.stop_stream()
                    stream.close()
                audio.terminate()
                
        except Exception as e:
            self.logger.error(f"Audio monitor error: {e}")
            self.current_audio_level = 0
    
    def _update_audio_meter(self):
        """Update the audio meter in the GUI"""
        try:
            # Update progress bar
            self.audio_level.config(value=self.current_audio_level)
            
            # Schedule next update if monitoring is active
            if self.audio_monitor_active:
                self.root.after(50, self._update_audio_meter)  # Update every 50ms
                
        except Exception as e:
            self.logger.debug(f"Audio meter update error: {e}")
            
    def _save_settings(self):
        """Save current settings"""
        try:
            # Save audio settings
            self.config.set('audio.sample_rate', int(self.sample_rate_var.get()))
            self.config.set('audio.silence_threshold', self.silence_threshold_var.get())
            self.config.set('audio.silence_duration', self.silence_duration_var.get())
            
            # Save selected audio device
            selected_device = self._get_selected_device_index()
            self.config.set('audio.input_device', selected_device)
            if selected_device is not None:
                self.logger.info(f"Audio device set to: {selected_device}")
            else:
                self.logger.info("Audio device set to: Default")
            
            # Save Whisper settings
            self.config.set('whisper.model_size', self.model_size_var.get())
            language = self.language_var.get().strip()
            self.config.set('whisper.language', language if language != 'auto' else None)
            
            # Save command settings
            wake_words = [w.strip() for w in self.wake_words_var.get().split(',') if w.strip()]
            self.config.set('commands.wake_words', wake_words)
            
            messagebox.showinfo("Success", "Settings saved successfully!\nRestart the application to apply audio device changes.")
            
        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")
            messagebox.showerror("Error", f"Failed to save settings: {e}")
    
    def _clear_log(self):
        """Clear the log display"""
        self.log_text.delete(1.0, tk.END)
    
    def _refresh_log(self):
        """Refresh log display"""
        try:
            # Read log file if it exists
            import os
            if os.path.exists('voice_control.log'):
                with open('voice_control.log', 'r') as f:
                    log_content = f.read()
                self.log_text.delete(1.0, tk.END)
                self.log_text.insert(1.0, log_content)
                self.log_text.see(tk.END)
        except Exception as e:
            self.logger.error(f"Failed to refresh log: {e}")
    
    def _on_closing(self):
        """Handle window closing"""
        if self.is_listening:
            self._stop_listening()
        self.root.destroy()
    
    async def run(self):
        """Run the GUI"""
        def tk_update():
            try:
                self.root.update()
            except tk.TclError:
                return False
            return True
        
        try:
            while tk_update():
                await asyncio.sleep(0.01)
        except Exception as e:
            self.logger.error(f"GUI error: {e}")
    
    def _refresh_audio_devices(self):
        """Refresh the list of available audio devices"""
        try:
            devices = self.voice_recognizer.list_audio_devices()
            device_list = []
            device_values = []
            
            # Add default device option
            device_list.append("Default Device")
            device_values.append("")
            
            # Add all available devices
            for device in devices:
                device_name = f"{device['index']}: {device['name']}"
                device_list.append(device_name)
                device_values.append(str(device['index']))
                
                # Auto-select eMeet device if available
                if 'emeet' in device['name'].lower() or 'm0' in device['name'].lower():
                    self.audio_device_var.set(device_name)
            
            # Update combobox
            self.audio_device_combo['values'] = device_list
            self.device_values = device_values  # Store for mapping
            
            # Set current device if configured
            current_device = self.config.get('audio.input_device', None)
            if current_device is not None:
                for i, device in enumerate(devices):
                    if device['index'] == current_device:
                        self.audio_device_var.set(device_list[i + 1])  # +1 for default option
                        break
            
            self.logger.info(f"Found {len(devices)} audio input devices")
            
        except Exception as e:
            self.logger.error(f"Error refreshing audio devices: {e}")
            messagebox.showerror("Error", f"Could not refresh audio devices: {e}")
    
    def _get_selected_device_index(self):
        """Get the index of the currently selected audio device"""
        try:
            selected = self.audio_device_var.get()
            if selected == "Default Device" or not selected:
                return None
            
            # Extract device index from selection
            device_index = int(selected.split(':')[0])
            return device_index
            
        except (ValueError, IndexError):
            return None