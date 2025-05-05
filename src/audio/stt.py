#!/usr/bin/env python
"""Handles Speech-to-Text transcription using various engines."""

import time
import wave
import io
import tempfile
import os
from typing import Optional, Tuple

import pyaudio
from openai import OpenAI # Use the official openai library
import whisper
import numpy as np

# Use relative imports
from ..utils.logging_setup import get_logger
# from ...utils.config_loader import get_config_value

logger = get_logger(__name__)

class SpeechToTextError(Exception):
    """Custom exception for STT errors."""
    pass

class OpenAiSttEngine:
    """Uses OpenAI Whisper API for Speech-to-Text."""

    def __init__(self,
                 api_key: str,
                 model: str = "whisper-1",
                 language: Optional[str] = None, # e.g., "en"
                 input_device_index: Optional[int] = None):
        """
        Initializes the OpenAI STT Engine.

        Args:
            api_key: Your OpenAI API key.
            model: The Whisper model to use (default: whisper-1).
            language: Optional language code (ISO 639-1) for transcription.
            input_device_index: Index of the audio input device.
        """
        if not api_key:
            raise ValueError("OpenAI API key is required.")
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.language = language
        self.input_device_index = input_device_index
        self.pa = pyaudio.PyAudio()

    def _record_audio(self, duration: float = 5.0, silence_threshold: float = 0.5, sample_rate: int = 16000, chunk_size: int = 1024) -> Optional[io.BytesIO]:
        """
        Records audio from the microphone until silence or max duration is reached.

        Args:
            duration: Maximum recording duration in seconds.
            silence_threshold: Duration of silence in seconds to stop recording.
            sample_rate: Audio sample rate.
            chunk_size: Audio buffer size.

        Returns:
            BytesIO object containing the recorded WAV audio, or None if recording fails.
        """
        audio_format = pyaudio.paInt16
        channels = 1

        try:
            stream = self.pa.open(format=audio_format,
                                  channels=channels,
                                  rate=sample_rate,
                                  input=True,
                                  frames_per_buffer=chunk_size,
                                  input_device_index=self.input_device_index)
        except Exception as e:
            logger.error(f"Failed to open audio stream for recording: {e}", exc_info=True)
            return None

        logger.info("Recording audio...")
        frames = []
        start_time = time.time()
        silence_start_time = None
        is_silent = True

        while True:
            try:
                data = stream.read(chunk_size, exception_on_overflow=False)
                frames.append(data)
            except IOError as e:
                logger.warning(f"Audio recording read error: {e}")
                # Consider attempting recovery or just stopping
                break

            # Basic silence detection (energy-based would be better)
            # This simple version checks if audio level is consistently low
            # For simplicity, we'll just use elapsed time and max duration for now.
            # TODO: Implement better silence detection

            current_time = time.time()
            elapsed_time = current_time - start_time

            # Check for max duration
            if elapsed_time >= duration:
                logger.info(f"Reached maximum recording duration ({duration}s).")
                break

            # Basic silence check (needs improvement)
            # if is_silent_chunk(data): # Requires implementing is_silent_chunk
            #     if is_silent and silence_start_time is None:
            #         silence_start_time = current_time
            #     elif not is_silent:
            #         is_silent = True
            #         silence_start_time = current_time
            #     elif current_time - silence_start_time >= silence_threshold:
            #         logger.info(f"Detected silence for {silence_threshold}s. Stopping recording.")
            #         break
            # else:
            #     is_silent = False
            #     silence_start_time = None

        logger.info("Finished recording.")

        # Stop and close the stream
        try:
            stream.stop_stream()
            stream.close()
        except Exception as e:
             logger.error(f"Error closing recording stream: {e}", exc_info=True)
             # Continue saving audio even if stream closing fails

        # Save recorded data to a BytesIO object as WAV
        if not frames:
            logger.warning("No audio frames recorded.")
            return None

        audio_buffer = io.BytesIO()
        wf = wave.open(audio_buffer, 'wb')
        wf.setnchannels(channels)
        wf.setsampwidth(self.pa.get_sample_size(audio_format))
        wf.setframerate(sample_rate)
        wf.writeframes(b''.join(frames))
        wf.close()

        audio_buffer.seek(0) # Rewind buffer to the beginning
        return audio_buffer

    def transcribe_audio_buffer(self, audio_buffer: io.BytesIO) -> Optional[str]:
        """Sends audio data from a buffer to Whisper API for transcription."""
        if not audio_buffer:
            logger.error("No audio buffer provided for transcription.")
            return None

        logger.info(f"Transcribing audio using OpenAI Whisper model: {self.model}...")
        try:
            # Need to pass the buffer with a filename for the API
            audio_buffer.name = "recording.wav" # Mock filename

            transcript = self.client.audio.transcriptions.create(
                model=self.model,
                file=audio_buffer,
                language=self.language # Pass language if specified
                # response_format="text" # Get plain text directly
            )
            logger.info("Transcription successful.")
            # The response object has a .text attribute
            return transcript.text.strip()

        except Exception as e:
            logger.error(f"OpenAI Whisper API request failed: {e}", exc_info=True)
            raise SpeechToTextError(f"Whisper API error: {e}") from e

    def listen_and_transcribe(self, record_duration: float = 5.0) -> Optional[str]:
        """Records audio and then transcribes it."""
        audio_buffer = self._record_audio(duration=record_duration)
        if audio_buffer:
            # # Optional: Save recorded audio for debugging
            # with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            #      tmp_file.write(audio_buffer.getvalue())
            #      logger.info(f"Saved recording for debug: {tmp_file.name}")
            #      audio_buffer.seek(0)

            return self.transcribe_audio_buffer(audio_buffer)
        else:
            logger.error("Audio recording failed, cannot transcribe.")
            return None

    def close(self):
         """Closes the PyAudio instance."""
         if self.pa:
             try:
                 self.pa.terminate()
                 logger.info("PyAudio instance terminated for STT engine.")
             except Exception as e:
                 logger.error(f"Error terminating PyAudio for STT: {e}", exc_info=True)
             finally:
                 self.pa = None

    def __del__(self):
        # Ensure PyAudio is terminated when the object is garbage collected
        self.close()

# Example Usage:
# if __name__ == '__main__':
#     # Load API key from environment or config
#     OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
#     if not OPENAI_API_KEY:
#         print("Error: OPENAI_API_KEY environment variable not set.")
#         exit(1)
#
#     try:
#         stt_engine = OpenAiSttEngine(api_key=OPENAI_API_KEY)
#         print("Speak clearly after the prompt (max 5 seconds)...")
#         time.sleep(1) # Give user a moment
#         transcription = stt_engine.listen_and_transcribe(record_duration=5.0)
#
#         if transcription:
#             print(f"\nTranscription: {transcription}")
#         else:
#             print("\nCould not transcribe audio.")
#
#     except ValueError as e:
#         print(f"Configuration Error: {e}")
#     except SpeechToTextError as e:
#         print(f"STT Error: {e}")
#     except Exception as e:
#         print(f"An unexpected error occurred: {e}")
#     finally:
#         # Clean up PyAudio instance if engine was created
#         if 'stt_engine' in locals():
#             stt_engine.close() 