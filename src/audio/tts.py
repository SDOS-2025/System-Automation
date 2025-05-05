#!/usr/bin/env python
"""Handles Text-to-Speech synthesis using various engines."""

import tempfile
import os
from typing import Optional

# Option 1: OpenAI TTS
from openai import OpenAI
import pygame # For playing audio from OpenAI stream

# Option 2: System TTS
import pyttsx3

# Use relative imports
from ..utils.logging_setup import get_logger
# from SystemAutomation.src.utils.config_loader import get_config_value

logger = get_logger(__name__)

class TextToSpeechError(Exception):
    """Custom exception for TTS errors."""
    pass

# --- OpenAI TTS Engine --- #

class OpenAiTtsEngine:
    """Uses OpenAI TTS API for speech synthesis."""

    def __init__(self, api_key: str,
                 model: str = "tts-1",
                 voice: str = "alloy",
                 output_format: str = "mp3"):
        """
        Initializes the OpenAI TTS Engine.

        Args:
            api_key: Your OpenAI API key.
            model: The TTS model (e.g., "tts-1", "tts-1-hd").
            voice: The voice to use (e.g., "alloy", "echo", "fable", "onyx", "nova", "shimmer").
            output_format: Audio output format (e.g., "mp3", "opus", "aac", "flac").
        """
        if not api_key:
            raise ValueError("OpenAI API key is required.")
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.voice = voice
        self.output_format = output_format

        # Initialize pygame mixer for playback
        try:
            pygame.mixer.init()
            logger.info("Pygame mixer initialized for OpenAI TTS playback.")
        except Exception as e:
            logger.error(f"Failed to initialize pygame mixer: {e}. Playback may fail.")
            raise TextToSpeechError("Audio playback initialization failed") from e

    def synthesize_and_play(self, text: str):
        """Synthesizes speech using OpenAI API and plays it back immediately."""
        if not text:
            logger.warning("No text provided for speech synthesis.")
            return

        logger.info(f"Synthesizing speech for: '{text[:50]}...'")
        try:
            # Use streaming response
            with self.client.audio.speech.with_streaming_response.create(
                model=self.model,
                voice=self.voice,
                input=text,
                response_format=self.output_format
            ) as response:
                # Stream audio to a temporary file
                # Pygame needs a file or file-like object, direct streaming can be tricky
                with tempfile.NamedTemporaryFile(suffix=f".{self.output_format}", delete=False) as tmp_audio_file:
                    for chunk in response.iter_bytes(chunk_size=4096):
                        tmp_audio_file.write(chunk)
                    tmp_file_path = tmp_audio_file.name

            logger.debug(f"Synthesized audio saved to temporary file: {tmp_file_path}")

            # Play the audio file using pygame
            if pygame.mixer.get_init():
                logger.info("Playing synthesized audio...")
                try:
                    pygame.mixer.music.load(tmp_file_path)
                    pygame.mixer.music.play()
                    # Wait for playback to finish
                    while pygame.mixer.music.get_busy():
                        pygame.time.Clock().tick(10)
                    logger.info("Audio playback finished.")
                except Exception as e:
                     logger.error(f"Error during pygame playback: {e}", exc_info=True)
                     raise TextToSpeechError("Audio playback failed") from e
                finally:
                    # Clean up the temporary file
                    if os.path.exists(tmp_file_path):
                         try:
                              os.remove(tmp_file_path)
                              logger.debug(f"Removed temporary audio file: {tmp_file_path}")
                         except OSError as e:
                              logger.warning(f"Could not remove temporary audio file {tmp_file_path}: {e}")
            else:
                 logger.error("Pygame mixer not initialized. Cannot play audio.")
                 raise TextToSpeechError("Playback engine not ready.")

        except Exception as e:
            logger.error(f"OpenAI TTS API request failed: {e}", exc_info=True)
            # Ensure temp file is cleaned up if created before error
            if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
                 try:
                      os.remove(tmp_file_path)
                 except OSError as remove_err:
                     logger.warning(f"Could not remove temporary audio file {tmp_file_path} after error: {remove_err}")
            raise TextToSpeechError(f"OpenAI TTS error: {e}") from e

    def close(self):
        """Closes the pygame mixer."""
        if pygame.mixer.get_init():
            try:
                pygame.mixer.quit()
                logger.info("Pygame mixer quit for OpenAI TTS.")
            except Exception as e:
                 logger.error(f"Error quitting pygame mixer: {e}", exc_info=True)

    def __del__(self):
         self.close()

# --- System TTS Engine (pyttsx3) --- #

class SystemTtsEngine:
    """Uses pyttsx3 library to access native OS TTS engines."""

    def __init__(self, rate: Optional[int] = None, volume: Optional[float] = None, voice_id: Optional[str] = None):
        """
        Initializes the pyttsx3 engine.

        Args:
            rate: Speech rate (words per minute). Default depends on OS engine.
            volume: Volume (0.0 to 1.0). Default is 1.0.
            voice_id: ID of the specific voice to use (get available IDs via list_available_voices).
        """
        try:
            self.engine = pyttsx3.init()
            logger.info("pyttsx3 engine initialized.")

            # Set default font to a common one on Linux to avoid Consolas errors
            import platform
            if platform.system() == 'Linux':
                try:
                    # Try to workaround Consolas font issues with a common Linux font
                    logger.info("Setting default TTS font for Linux")
                    self.engine.setProperty('voice', 'default')
                except Exception as e:
                    logger.warning(f"Could not set default voice: {e}")

            if rate:
                current_rate = self.engine.getProperty('rate')
                logger.debug(f"Setting TTS rate from {current_rate} to {rate}")
                self.engine.setProperty('rate', rate)

            if volume:
                current_volume = self.engine.getProperty('volume')
                logger.debug(f"Setting TTS volume from {current_volume} to {volume}")
                self.engine.setProperty('volume', max(0.0, min(volume, 1.0)))

            if voice_id:
                logger.debug(f"Attempting to set TTS voice ID to {voice_id}")
                try:
                     self.engine.setProperty('voice', voice_id)
                except Exception as e:
                     logger.warning(f"Could not set voice ID '{voice_id}': {e}. Using default voice.")
                     available = self.list_available_voices()
                     logger.info(f"Available voices: {available}")

            # Connect callback for when speaking finishes (optional)
            # self.engine.connect('finished-utterance', self.on_speech_end)

        except Exception as e:
            logger.error(f"Failed to initialize pyttsx3 engine: {e}", exc_info=True)
            self.engine = None
            raise TextToSpeechError("pyttsx3 initialization failed") from e

    # def on_speech_end(self, name, completed):
    #     logger.debug(f"Finished speaking utterance: {name}, Completed: {completed}")

    def list_available_voices(self):
        """Lists available voices and their IDs."""
        if not self.engine:
            logger.error("pyttsx3 engine not initialized.")
            return []
        voices = self.engine.getProperty('voices')
        return [(voice.name, voice.id) for voice in voices]

    def synthesize_and_play(self, text: str):
        """Synthesizes speech using pyttsx3 and blocks until finished."""
        if not self.engine:
            logger.error("pyttsx3 engine not initialized, cannot synthesize speech.")
            raise TextToSpeechError("System TTS engine not ready.")

        if not text:
            logger.warning("No text provided for speech synthesis.")
            return

        logger.info(f"Synthesizing speech (system TTS) for: '{text[:50]}...'")
        try:
            self.engine.say(text)
            self.engine.runAndWait() # Blocks until speech is finished
            logger.info("System TTS playback finished.")
        except Exception as e:
            logger.error(f"pyttsx3 synthesis/playback failed: {e}", exc_info=True)
            raise TextToSpeechError("System TTS failed") from e

    def close(self):
        """Cleanly shuts down the pyttsx3 engine if needed."""
        # runAndWait usually handles cleanup, explicit stop might cause issues
        # if self.engine:
        #     try:
        #         self.engine.stop() # Stop any ongoing speech
        #         logger.info("pyttsx3 engine stopped.")
        #     except Exception as e:
        #         logger.error(f"Error stopping pyttsx3 engine: {e}", exc_info=True)
        pass # Generally not needed

    def __del__(self):
         self.close()


# Example Usage:
# if __name__ == '__main__':
#     text_to_say = "Hello world! This is a test of the text to speech system."
#     print("--- Testing System TTS (pyttsx3) ---")
#     try:
#         system_tts = SystemTtsEngine(rate=150) # Optional: Adjust rate
#         # print("Available voices:", system_tts.list_available_voices())
#         system_tts.synthesize_and_play(text_to_say)
#         print("System TTS test complete.")
#     except TextToSpeechError as e:
#          print(f"System TTS Error: {e}")
#     except Exception as e:
#         print(f"Could not initialize pyttsx3. Ensure TTS engines are installed on your system. Error: {e}")
#
#     print("\n--- Testing OpenAI TTS ---")
#     OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
#     if not OPENAI_API_KEY:
#         print("Skipping OpenAI TTS test: OPENAI_API_KEY environment variable not set.")
#     else:
#         openai_tts = None
#         try:
#             openai_tts = OpenAiTtsEngine(api_key=OPENAI_API_KEY, voice="nova")
#             openai_tts.synthesize_and_play(text_to_say)
#             print("OpenAI TTS test complete.")
#         except TextToSpeechError as e:
#             print(f"OpenAI TTS Error: {e}")
#         except Exception as e:
#             print(f"An unexpected error occurred during OpenAI TTS test: {e}")
#         finally:
#             if openai_tts:
#                 openai_tts.close() 