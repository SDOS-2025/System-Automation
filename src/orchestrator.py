#!/usr/bin/env python
"""Orchestrates the components: Wake Word -> STT -> Core Logic -> TTS."""

import time
import logging
from typing import Dict, Any, Optional
import threading

# Import QObject and pyqtSignal for GUI communication
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

# Use absolute imports based on package structure
from .audio.wake_word import WakeWordDetector, WakeWordDetectorError
from .audio.stt import OpenAiSttEngine, SpeechToTextError
from .audio.tts import OpenAiTtsEngine, SystemTtsEngine, TextToSpeechError
from .core.task_processor import TaskProcessor
from .utils.config_loader import get_config_value

# Utilities
from .utils.logging_setup import get_logger

# Get logger instance (consider making it accessible for signal emission?)
logger = logging.getLogger(__name__)

class Orchestrator(QObject): # Inherit from QObject
    """Manages the main loop: Wake Word -> STT -> Core -> TTS."""

    # --- Signals for GUI Communication ---
    log_signal = pyqtSignal(str)        # To send general log messages/status updates
    response_signal = pyqtSignal(str)   # To send the final text response
    error_signal = pyqtSignal(str)      # To send critical errors
    task_step_signal = pyqtSignal(str)  # NEW: Signal to send individual task steps
    # Signal to indicate core processing started/finished?

    def __init__(self, config: Dict[str, Any], task_processor: TaskProcessor):
        """Initializes all components."""
        super().__init__() # Use super() for QObject initialization
        self.log_signal.emit("Initializing orchestrator components...")
        logger.info("Initializing orchestrator components...") # Keep logging too
        self.config = config
        self.task_processor = task_processor # Use the passed TaskProcessor
        self.log_signal.emit("Task Processor initialized.")
        logger.info("Task Processor initialized.")

        # State for mic input toggle
        self.mic_input_enabled = False # Start disabled by default
        self.is_gui_mode = False # Set based on how it's run (e.g., from assistant.py)

        # --- Initialize Audio Components ---
        # Store init status for checks
        self.wake_word_detector: Optional[WakeWordDetector] = None
        self.stt_engine: Optional[OpenAiSttEngine] = None
        self.tts_engine: Optional[object] = None # Type depends on engine
        self._wake_word_init_ok = False
        self._stt_init_ok = False
        self._tts_init_ok = False

        # Check wake word enabled status *before* initializing
        self.wake_word_enabled = get_config_value("wake_word.enabled", False)

        if self.wake_word_enabled:
            self.wake_word_detector = self._init_wake_word()
            self._wake_word_init_ok = self.wake_word_detector is not None
        else:
            self.log_signal.emit("Wake word detection is disabled in config.")
            logger.info("Wake word detection is disabled in config.")
            self._wake_word_init_ok = True # Considered OK if disabled

        self.stt_engine = self._init_stt()
        self._stt_init_ok = self.stt_engine is not None

        self.tts_engine = self._init_tts()
        self._tts_init_ok = self.tts_engine is not None

        # --- Critical Component Check ---
        # STT and TTS must succeed. Wake word must succeed *if enabled*.
        init_failed = False
        error_msg = "Orchestrator initialization failed:"
        if self.wake_word_enabled and not self._wake_word_init_ok:
            error_msg += " Wake word detector failed."
            init_failed = True
        if not self._stt_init_ok:
            error_msg += " STT engine failed."
            init_failed = True
        if not self._tts_init_ok:
            error_msg += " TTS engine failed."
            init_failed = True

        if init_failed:
            self.error_signal.emit(error_msg)
            logger.critical(error_msg)
            raise RuntimeError(error_msg)

        self.log_signal.emit("Orchestrator initialized successfully.")
        logger.info("Orchestrator initialized successfully.")
        self.stop_event = threading.Event()

    # --- Slot for GUI Control --- #
    @pyqtSlot(bool)
    def set_mic_input_enabled(self, enabled: bool):
        """Slot to enable/disable the microphone listening loop."""
        self.mic_input_enabled = enabled
        status = "enabled" if enabled else "disabled"
        self.log_signal.emit(f"Microphone input loop {status} by GUI request.")
        logger.info(f"Microphone input loop {status} by GUI request.")

    def _init_wake_word(self) -> Optional[WakeWordDetector]:
        """Initializes the Wake Word Detector based on config."""
        if not self.wake_word_enabled:
             return None # Skip if disabled
        try:
            self.log_signal.emit("Initializing Wake Word Detector...")
            access_key = get_config_value("wake_word.access_key") # Renamed from picovoice.*
            if not access_key or "YOUR_PICOVOICE" in access_key:
                 msg = "Picovoice access key not found or invalid in config (wake_word.access_key). Wake word detector disabled."
                 self.error_signal.emit(msg)
                 logger.error(msg)
                 return None

            keyword_paths = get_config_value("wake_word.keyword_paths")
            if not keyword_paths or not isinstance(keyword_paths, list):
                 msg = "Keyword paths list not found or invalid in config (wake_word.keyword_paths). Wake word detector disabled."
                 self.error_signal.emit(msg)
                 logger.error(msg)
                 return None

            sensitivities = get_config_value("wake_word.sensitivity") # Single value or list?
            # Adjust sensitivities if single value is given for multiple keywords
            if isinstance(sensitivities, float):
                sensitivities = [sensitivities] * len(keyword_paths)
            elif not isinstance(sensitivities, list):
                sensitivities = [0.5] * len(keyword_paths) # Default if missing/invalid

            model_path = get_config_value("wake_word.model_path")
            library_path = get_config_value("wake_word.library_path")
            device_index = get_config_value("audio.input_device_index")

            detector = WakeWordDetector(
                access_key=access_key,
                library_path=library_path,
                model_path=model_path,
                keyword_paths=keyword_paths,
                sensitivities=sensitivities,
                input_device_index=device_index
            )
            self.log_signal.emit("Wake Word Detector initialized.")
            logger.info("Wake Word Detector initialized.")
            return detector
        except (ValueError, WakeWordDetectorError) as e:
            msg = f"Failed to initialize Wake Word Detector: {e}"
            self.error_signal.emit(msg)
            logger.error(msg)
            return None
        except Exception as e:
            msg = f"Unexpected error initializing Wake Word Detector: {e}"
            self.error_signal.emit(msg)
            logger.error(msg, exc_info=True)
            return None

    def _init_stt(self) -> Optional[OpenAiSttEngine]:
        """Initializes the STT Engine based on config."""
        try:
            self.log_signal.emit("Initializing STT Engine...")
            stt_api_key = get_config_value("openai.api_key")
            stt_model = get_config_value("openai.stt_model", "whisper-1")
            stt_language = get_config_value("openai.stt_language", None) # Read language, default to None
            input_device_index = get_config_value("audio.input_device_index")

            if not stt_api_key:
                msg = "Missing OpenAI API key for STT in config (openai.api_key)"
                self.error_signal.emit(msg)
                logger.error(msg)
                raise ValueError(msg)

            stt_engine_instance = OpenAiSttEngine(
                api_key=stt_api_key,
                model=stt_model,
                language=stt_language, # Pass language to engine
                input_device_index=input_device_index
            )
            lang_info = f" (Language: {stt_language})" if stt_language else ""
            self.log_signal.emit(f"OpenAI STT Engine ({stt_model}{lang_info}) initialized.")
            logger.info(f"OpenAI STT Engine ({stt_model}{lang_info}) initialized.")
            return stt_engine_instance
        except (ValueError, SpeechToTextError) as e:
            msg = f"Failed to initialize STT Engine: {e}"
            self.error_signal.emit(msg)
            logger.error(msg)
            return None
        except Exception as e:
            msg = f"Unexpected error initializing STT Engine: {e}"
            self.error_signal.emit(msg)
            logger.error(msg, exc_info=True)
            return None

    def _init_tts(self) -> Optional[object]: # Return type depends on engine class
        """Initializes the TTS Engine based on config."""
        tts_engine_type = get_config_value("tts.engine", "system")
        self.log_signal.emit(f"Initializing TTS engine: {tts_engine_type}")
        logger.info(f"Initializing TTS engine: {tts_engine_type}")

        try:
            if tts_engine_type == "openai":
                api_key = get_config_value("openai.api_key")
                if not api_key:
                    msg = "OpenAI API key not found in config (openai.api_key). Cannot init OpenAI TTS."
                    self.error_signal.emit(msg)
                    logger.error(msg)
                    return None
                model = get_config_value("openai.tts_model", "tts-1")
                voice = get_config_value("openai.tts_voice", "alloy")
                engine = OpenAiTtsEngine(api_key=api_key, model=model, voice=voice)
                msg = f"TTS Engine (OpenAI TTS - {model}, {voice}) initialized."
                self.log_signal.emit(msg)
                logger.info(msg)
                return engine

            elif tts_engine_type == "system":
                rate = get_config_value("tts.system.rate")
                volume = get_config_value("tts.system.volume")
                voice_id = get_config_value("tts.system.voice_id")
                engine = SystemTtsEngine(rate=rate, volume=volume, voice_id=voice_id)
                msg = "TTS Engine (System/pyttsx3) initialized."
                self.log_signal.emit(msg)
                logger.info(msg)
                return engine
            else:
                msg = f"Unsupported TTS engine specified in config: {tts_engine_type}"
                self.error_signal.emit(msg)
                logger.error(msg)
                return None
        except (ValueError, TextToSpeechError) as e:
            msg = f"Failed to initialize {tts_engine_type} TTS Engine: {e}"
            self.error_signal.emit(msg)
            logger.error(msg)
            return None
        except Exception as e:
            msg = f"Unexpected error initializing {tts_engine_type} TTS Engine: {e}"
            self.error_signal.emit(msg)
            logger.error(msg, exc_info=True)
            return None

    def run(self):
        """Starts the main assistant loop (typically run in a thread for GUI mode)."""
        if (self.wake_word_enabled and not self._wake_word_init_ok) or \
           (not self._stt_init_ok) or \
           (not self._tts_init_ok):
            msg = "Cannot run orchestrator because STT, TTS, or enabled Wake Word detector failed to initialize."
            self.error_signal.emit(msg)
            logger.error(msg)
            return

        self.log_signal.emit("Orchestrator starting main loop.")
        logger.info("Orchestrator starting main loop.")
        try:
            while not self.stop_event.is_set():
                # Check if mic input is enabled by the GUI
                if not self.mic_input_enabled:
                    time.sleep(0.5) # Sleep briefly and check again
                    continue

                # --- Microphone Input Steps --- #
                # 1. Wait for Wake Word (if enabled)
                if self.wake_word_enabled:
                    self.log_signal.emit("Waiting for wake word...")
                    logger.info("Waiting for wake word...")
                    try:
                        if not self.wake_word_detector:
                             msg = "Wake word detector not initialized, cannot run."
                             self.error_signal.emit(msg)
                             logger.error(msg)
                             break
                        keyword_index = self.wake_word_detector.run()
                        if keyword_index < 0:
                             msg = "Wake word detection stopped or errored out."
                             self.log_signal.emit(msg)
                             logger.info(msg)
                             break
                        # Optional: Play a sound or emit signal
                    except WakeWordDetectorError as e:
                        msg = f"Wake word detection failed: {e}. Retrying after delay..."
                        self.error_signal.emit(msg)
                        logger.error(msg)
                        time.sleep(5)
                        continue # Retry listening
                    except Exception as e:
                         msg = f"Unexpected error during wake word detection: {e}. Stopping."
                         self.error_signal.emit(msg)
                         logger.error(msg, exc_info=True)
                         break
                    self.log_signal.emit("Wake word detected! Listening for command...")
                    logger.info("Wake word detected! Listening for command...")
                else:
                    # If wake word is globally disabled via config, still need to listen for STT
                    # If only GUI toggle is off, this part is skipped by the check above
                    self.log_signal.emit("Wake word disabled (config). Proceeding directly to listen...")
                    logger.info("Wake word disabled (config). Proceeding directly to listen...")

                # 2. Listen for Command (STT)
                transcription = None
                try:
                    if not self.stt_engine:
                        msg = "STT engine not initialized. Cannot listen."
                        self.error_signal.emit(msg)
                        logger.error(msg)
                        break
                    record_duration = float(get_config_value("stt.record_duration", 5.0))
                    self.log_signal.emit(f"Listening for command ({record_duration}s max)...")
                    transcription = self.stt_engine.listen_and_transcribe(record_duration=record_duration)
                except Exception as e:
                    msg = f"Speech-to-text failed: {e}"
                    self.error_signal.emit(msg)
                    logger.error(msg, exc_info=True)
                    self._speak_response("Sorry, I couldn't understand that.")
                    continue

                if not transcription:
                    msg = "STT returned no transcription."
                    self.log_signal.emit(msg)
                    logger.warning(msg)
                    continue

                self.log_signal.emit(f"Transcription: '{transcription}'")
                logger.info(f"Transcription: '{transcription}'")

                # 3. Process Command (Core Logic)
                self._process_and_respond(transcription)

        except KeyboardInterrupt:
            self.log_signal.emit("Orchestrator loop interrupted by user (Ctrl+C).")
            logger.info("Orchestrator loop interrupted by user.")
        finally:
            self.shutdown() # Ensure cleanup happens

    def process_text_command(self, text: str):
        """Processes a command received as text (e.g., from GUI)."""
        if not text:
            return
        logger.info(f"Processing text command: '{text}'") # Keep logger info
        # Run processing in a separate thread? Or assume GUI runs this in a non-blocking way?
        # For now, run synchronously within the caller's thread (likely GUI thread if called directly)
        # Consider emitting signals for start/end of processing?
        self._process_and_respond(text)

    def _process_and_respond(self, command_text: str):
        """Helper function to run TaskProcessor and handle response/TTS."""
        self.log_signal.emit(f"Processing command: {command_text}...")
        logger.info(f"Processing command: {command_text}...")
        response_text = "Sorry, I encountered an error while processing your request." # Default
        try:
            tasks = self.task_processor.run_plan(command_text)
            if tasks:
                task_count = len(tasks)
                self.log_signal.emit(f"Plan generated with {task_count} steps. Executing...")
                
                # NEW: Emit each task as a step for the UI
                for i, task in enumerate(tasks):
                    step_msg = f"Step {i+1}/{task_count}: {task}"
                    self.task_step_signal.emit(step_msg)
                    logger.info(step_msg)
                
                # Execute the tasks
                self.task_processor.execute_tasks()
                
                # TODO: Get better final summary from TaskProcessor
                response_text = "Okay, I've completed the requested tasks."
                self.log_signal.emit("Task execution finished.")
                logger.info("Task execution finished.")
            else:
                msg = "I couldn't create a plan for that request."
                self.log_signal.emit(msg)
                logger.warning("Task planning failed or returned no tasks.")
                response_text = msg

        except Exception as e:
            msg = f"Error during task processing: {e}"
            self.error_signal.emit(msg)
            logger.error(msg, exc_info=True)
            response_text = f"Sorry, I encountered an error: {e}"

        # 4. Speak/Send Response
        self.log_signal.emit(f"Generated response: '{response_text}'")
        logger.info(f"Generated response: '{response_text}'")
        self.response_signal.emit(response_text) # Send text to GUI
        self._speak_response(response_text)      # Speak it via TTS as well

    def _speak_response(self, text: str):
        """Handles sending text to the TTS engine."""
        if not self.tts_engine:
            msg = "TTS engine not initialized. Cannot speak response."
            self.error_signal.emit(msg)
            logger.error(msg)
            return
        try:
            self.tts_engine.synthesize_and_play(text)
        except Exception as e:
            msg = f"Text-to-speech failed: {e}"
            self.error_signal.emit(msg)
            logger.error(msg, exc_info=True)

    def shutdown(self):
        """Cleans up resources."""
        if self.stop_event.is_set(): # Prevent double shutdown
             return
        self.log_signal.emit("Orchestrator shutting down...")
        logger.info("Orchestrator shutting down... ")
        self.stop_event.set() # Signal loops to stop

        # Cleanup components safely
        if hasattr(self, 'wake_word_detector') and self.wake_word_detector:
            logger.debug("Deleting wake word detector...")
            self.wake_word_detector.delete()
            self.wake_word_detector = None
        if hasattr(self, 'stt_engine') and self.stt_engine:
            logger.debug("Closing STT engine...")
            self.stt_engine.close()
            self.stt_engine = None
        if hasattr(self, 'tts_engine') and self.tts_engine:
            # Check if TTS engine has a close method
            close_method = getattr(self.tts_engine, "close", None)
            if callable(close_method):
                 logger.debug("Closing TTS engine...")
                 close_method()
            self.tts_engine = None

        self.log_signal.emit("Orchestrator shutdown complete.")
        logger.info("Orchestrator shutdown complete.")

# Example Usage remains commented out
