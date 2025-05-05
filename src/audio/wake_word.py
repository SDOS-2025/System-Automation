#!/usr/bin/env python
"""Handles wake word detection using Porcupine."""

import time
import struct
from typing import Optional, List

import pyaudio
import pvporcupine

from ..utils.logging_setup import get_logger
# from ...utils.config_loader import get_config_value # For getting config later

logger = get_logger(__name__)

class WakeWordDetectorError(Exception):
    """Custom exception for wake word detection errors."""
    pass

class WakeWordDetector:
    """Listens for a specific wake word using Porcupine."""

    def __init__(self,
                 access_key: str,
                 library_path: Optional[str] = None,
                 model_path: Optional[str] = None,
                 keyword_paths: Optional[List[str]] = None,
                 sensitivities: Optional[List[float]] = None,
                 input_device_index: Optional[int] = None):
        """
        Initializes the WakeWordDetector.

        Args:
            access_key: Picovoice access key.
            library_path: Path to the Porcupine dynamic library.
            model_path: Path to the Porcupine model file.
            keyword_paths: List of paths to Porcupine keyword files (.ppn).
            sensitivities: List of sensitivities for each keyword (0.0 to 1.0).
            input_device_index: Index of the audio input device.
        """
        if not access_key:
            raise ValueError("Porcupine access key is required.")
        if not keyword_paths:
            # Example default keyword
            # keyword_paths = [pvporcupine.KEYWORD_PATHS["jarvis"]]
            raise ValueError("At least one keyword path is required.")
        if sensitivities is None:
            sensitivities = [0.5] * len(keyword_paths)
        if len(keyword_paths) != len(sensitivities):
            raise ValueError("Number of keyword paths and sensitivities must match.")

        self.access_key = access_key
        self.library_path = library_path
        self.model_path = model_path
        self.keyword_paths = keyword_paths
        self.sensitivities = sensitivities
        self.input_device_index = input_device_index

        self.porcupine: Optional[pvporcupine.Porcupine] = None
        self.audio_stream: Optional[pyaudio.Stream] = None
        self.pa: Optional[pyaudio.PyAudio] = None

        self._initialize_engine()

    def _initialize_engine(self):
        """Initializes the Porcupine engine."""
        try:
            self.porcupine = pvporcupine.create(
                access_key=self.access_key,
                library_path=self.library_path,
                model_path=self.model_path,
                keyword_paths=self.keyword_paths,
                sensitivities=self.sensitivities
            )
            logger.info(f"Porcupine engine initialized for keywords: {self.keyword_paths}")
        except pvporcupine.PorcupineError as e:
            logger.error(f"Failed to initialize Porcupine engine: {e}")
            raise WakeWordDetectorError(f"Porcupine initialization failed: {e}") from e

    def _start_audio_stream(self):
        """Starts the PyAudio input stream."""
        if self.porcupine is None:
            raise WakeWordDetectorError("Porcupine engine not initialized.")

        try:
            self.pa = pyaudio.PyAudio()
            self.audio_stream = self.pa.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length,
                input_device_index=self.input_device_index
            )
            logger.info(f"Audio stream started. Listening on device index: {self.input_device_index or 'default'}")
        except Exception as e:
            logger.error(f"Failed to open audio stream: {e}")
            if self.pa:
                self.pa.terminate()
            self.pa = None
            self.audio_stream = None
            raise WakeWordDetectorError(f"PyAudio stream failed: {e}") from e

    def run(self, detected_callback=None) -> int:
        """
        Continuously listens for the wake word.

        Args:
            detected_callback: An optional function to call when wake word is detected.
                               It receives the keyword index as an argument.

        Returns:
            The index of the detected keyword.
            Blocks until a wake word is detected.
        """
        if self.porcupine is None:
            self._initialize_engine() # Try to re-initialize

        self._start_audio_stream()
        if self.audio_stream is None or self.porcupine is None:
             raise WakeWordDetectorError("Failed to start wake word detection components.")

        logger.info("Listening for wake word...")
        try:
            while True:
                try:
                    pcm = self.audio_stream.read(
                        self.porcupine.frame_length,
                        exception_on_overflow=False # Avoid crashing on buffer overflow
                    )
                    pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)
                except IOError as e:
                    logger.warning(f"Audio read error: {e}. Attempting to recover stream.")
                    # Attempt to stop and restart the stream
                    self._stop_audio_stream()
                    time.sleep(0.1)
                    self._start_audio_stream()
                    continue # Skip this frame

                # Process audio frame with Porcupine
                keyword_index = self.porcupine.process(pcm)

                if keyword_index >= 0:
                    logger.info(f"Detected keyword index: {keyword_index} ('{self.keyword_paths[keyword_index]}')")
                    if detected_callback:
                        try:
                            detected_callback(keyword_index)
                        except Exception as cb_err:
                            logger.error(f"Error in detected_callback: {cb_err}")
                    return keyword_index # Stop listening after detection

        except KeyboardInterrupt:
            logger.info("Wake word detection stopped by user.")
            return -1 # Indicate stop via interrupt
        except Exception as e:
             logger.error(f"An error occurred during wake word detection: {e}", exc_info=True)
             raise WakeWordDetectorError(f"Detection loop error: {e}") from e
        finally:
            self._stop_audio_stream()
            self.delete() # Ensure engine resources are released

    def _stop_audio_stream(self):
        """Stops and closes the PyAudio stream."""
        if self.audio_stream is not None:
            try:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                logger.debug("Audio stream stopped.")
            except Exception as e:
                logger.error(f"Error stopping audio stream: {e}", exc_info=True)
            finally:
                self.audio_stream = None

        if self.pa is not None:
            try:
                self.pa.terminate()
                logger.debug("PyAudio terminated.")
            except Exception as e:
                logger.error(f"Error terminating PyAudio: {e}", exc_info=True)
            finally:
                 self.pa = None

    def delete(self):
        """Releases resources used by Porcupine and PyAudio."""
        self._stop_audio_stream()
        if self.porcupine is not None:
            try:
                self.porcupine.delete()
                logger.info("Porcupine engine resources released.")
            except Exception as e:
                 logger.error(f"Error deleting Porcupine engine: {e}", exc_info=True)
            finally:
                self.porcupine = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.delete()

# Example Usage (requires configuration and libraries installed)
# if __name__ == '__main__':
#     # --- Configuration --- #
#     # Replace with your actual access key from Picovoice Console
#     PICOVOICE_ACCESS_KEY = "YOUR_ACCESS_KEY_HERE"
#     # Find available audio devices (optional)
#     # pa = pyaudio.PyAudio()
#     # for i in range(pa.get_device_count()):
#     #     info = pa.get_device_info_by_index(i)
#     #     if info.get('maxInputChannels') > 0:
#     #         print(f"Input Device {i}: {info.get('name')}")
#     # pa.terminate()
#     INPUT_DEVICE_IDX = None # Default device
#     # Download keyword files (.ppn) for your platform from Picovoice Console
#     # Example using built-in keywords (if available and match platform)
#     # keyword_paths = [pvporcupine.KEYWORD_PATHS["jarvis"]]
#     keyword_paths = ["path/to/your/keyword.ppn"] # Replace with actual path(s)
#     sensitivities = [0.7] # Adjust sensitivity (0.0-1.0)
#
#     if PICOVOICE_ACCESS_KEY == "YOUR_ACCESS_KEY_HERE" or "path/to" in keyword_paths[0]:
#          print("Error: Please replace placeholders for PICOVOICE_ACCESS_KEY and keyword_paths.")
#          exit(1)
#
#     try:
#         detector = WakeWordDetector(
#             access_key=PICOVOICE_ACCESS_KEY,
#             keyword_paths=keyword_paths,
#             sensitivities=sensitivities,
#             input_device_index=INPUT_DEVICE_IDX
#         )
#         print("Listening for wake word... Press Ctrl+C to exit.")
#         keyword_index = detector.run()
#         if keyword_index >= 0:
#             print(f"Wake word '{keyword_paths[keyword_index]}' detected!")
#
#     except WakeWordDetectorError as e:
#         print(f"Error: {e}")
#     except KeyboardInterrupt:
#         print("\nStopping...")
#     finally:
#         # Ensure resources are released if detector was created
#         if 'detector' in locals() and detector:
#              detector.delete() 