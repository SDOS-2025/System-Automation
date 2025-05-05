# Implementation Plan for S2S Jarvis Assistant

This plan outlines the steps to refactor the `autoMate` project into the `SystemAutomation` project, following the structure defined in `Structure.md`, to create a Speech-to-Speech (S2S) Jarvis-like desktop assistant.

## Phase 1: Initial Setup and File Migration

1.  **Create Basic Directory Structure:**
    *   Run `mkdir -p src scripts weights docs tests` inside the `SystemAutomation` directory.
    *   Create `src/__init__.py`.
2.  **Copy/Move Top-Level Files:**
    *   Copy `autoMate/.gitignore` to `SystemAutomation/.gitignore`.
    *   Copy `autoMate/LICENSE` to `SystemAutomation/LICENSE`.
    *   Copy `autoMate/README.md` to `SystemAutomation/README.md` (will be updated later).
    *   Copy `autoMate/requirements.txt` to `SystemAutomation/requirements.txt` (will be updated later).
3.  **Create Placeholder/Configuration Files:**
    *   Create an empty `SystemAutomation/config.yaml`.
    *   Copy `Structure.md` (from the workspace root) to `SystemAutomation/Structure.md`.
    *   Create `weights/.gitkeep`.
4.  **Create `src` Subdirectories:**
    *   Run `mkdir src/audio src/core src/utils`.
    *   Create `__init__.py` files in each: `src/audio/__init__.py`, `src/core/__init__.py`, `src/utils/__init__.py`.

## Phase 2: Refactoring Existing `autoMate` Code

1.  **Refactor `autoMate/auto_control` -> `src/core`:**
    *   Move relevant Python files from `autoMate/auto_control/` to `SystemAutomation/src/core/`.
    *   **Goal:** Separate logic into:
        *   `llm_interaction.py`: Code interacting with LLMs.
        *   `screen_analysis.py`: Code for screen capture, OCR, object detection.
        *   `action_executor.py`: Code for `pyautogui`, `pynput`, etc.
        *   `task_processor.py`: Higher-level logic coordinating core components based on input commands (might need creation/heavy adaptation).
    *   Update all relative imports within these files to reflect the new structure (e.g., `from . import screen_analysis`).
2.  **Refactor `autoMate/util` -> `src/utils`:**
    *   Move relevant utility files/functions from `autoMate/util/` to `SystemAutomation/src/utils/`.
    *   Adapt `autoMate/util/download_weights.py` into `src/utils/download_models.py`. Update it to potentially handle STT/TTS/wake word models if needed.
    *   Create placeholder files: `src/utils/config_loader.py`, `src/utils/logging_setup.py`.
    *   Update imports in moved files and where these utilities are used (e.g., `from src.utils.config_loader import ...`).
3.  **Refactor Entry Point (`autoMate/main.py` -> `src/assistant.py`):**
    *   Create `src/assistant.py`.
    *   Move the core logic from `autoMate/main.py` (importing/calling `download_weights`, calling the main application function) into `src/assistant.py`.
    *   Adapt the `if __name__ == "__main__":` block.
    *   The `main()` function in `assistant.py` will eventually initialize and run the orchestrator.
4.  **Refactor Installation Script (`autoMate/install.py` -> `scripts/install_deps.py`):**
    *   Move `autoMate/install.py` to `SystemAutomation/scripts/install_deps.py`.
    *   Update the script to handle the new structure and dependencies (Phase 4).
5.  **Handle `autoMate/ui`:**
    *   Decide whether to completely remove the Gradio UI code (`autoMate/ui/`) or archive it elsewhere. Since the primary interface is S2S, it's likely unnecessary for the core assistant.

## Phase 3: Implementing S2S Components

1.  **Implement `src/audio/wake_word.py`:**
    *   Choose a wake word engine (e.g., `pvporcupine`).
    *   Implement logic to listen for the wake word and trigger the next step.
    *   Integrate with `config.yaml` for model paths, sensitivity, etc.
2.  **Implement `src/audio/stt.py`:**
    *   Choose an STT engine (e.g., `openai-whisper`, `SpeechRecognition`).
    *   Implement logic to record audio after wake word detection.
    *   Implement logic to transcribe the audio.
    *   Integrate with `config.yaml` for model selection, API keys, device selection.
3.  **Implement `src/audio/tts.py`:**
    *   Choose a TTS engine (e.g., `pyttsx3`, `elevenlabs`, `openai`).
    *   Implement logic to synthesize speech from text.
    *   Integrate with `config.yaml` for voice selection, API keys, etc.
4.  **Implement `src/orchestrator.py`:**
    *   Create the main control flow:
        *   Listen for wake word (`wake_word.py`).
        *   On wake word, activate STT (`stt.py`).
        *   Pass transcribed text to the core logic (`core/task_processor.py`).
        *   Receive text response from the core.
        *   Send text response to TTS (`tts.py`).
        *   Play back the synthesized audio.
    *   Handle state management (e.g., listening, processing, speaking).
    *   Integrate components, passing data between them.

## Phase 4: Integration and Finalization

1.  **Implement `src/utils/config_loader.py`:**
    *   Use a library like `PyYAML`.
    *   Load settings from `config.yaml`.
    *   Provide a way for other modules to access configuration values.
    *   Include basic validation.
2.  **Implement `src/utils/logging_setup.py`:**
    *   Configure Python's `logging` module.
    *   Set up logging levels, formatters, and handlers (e.g., console, file).
3.  **Update `src/assistant.py`:**
    *   Initialize configuration (`config_loader`).
    *   Initialize logging (`logging_setup`).
    *   Initialize all main components (`audio`, `core`).
    *   Initialize and run the `Orchestrator`.
4.  **Update `requirements.txt`:**
    *   Add necessary libraries for STT, TTS, wake word, YAML parsing.
    *   Remove unused dependencies (e.g., `gradio` if UI is removed).
    *   Pin versions for reproducibility.
5.  **Update `README.md`:**
    *   Change the project description to reflect the S2S Jarvis assistant.
    *   Update installation instructions (`conda`, `pip install -r requirements.txt`, running `scripts/install_deps.py` if needed).
    *   Update usage instructions (how to configure `config.yaml`, how to run `src/assistant.py`).
    *   Update dependencies section.
    *   Mention hardware requirements (microphone, speakers, GPU if needed for local STT/vision).
6.  **Testing:**
    *   Manually test the end-to-end flow.
    *   (Optional) Write unit/integration tests for key components (`audio`, `core`, `orchestrator`).
7.  **Documentation:**
    *   (Optional) Add more detailed documentation in the `docs/` directory (e.g., configuration options, architecture details).

## Phase 5: Cleanup and Refinement

1.  **Code Review:** Review the refactored code for clarity, efficiency, and adherence to the structure.
2.  **Error Handling:** Improve error handling throughout the application.
3.  **Performance Optimization:** Profile and optimize critical sections if needed (e.g., STT processing, screen analysis).
4.  **Finalize Configuration:** Ensure all necessary options are configurable via `config.yaml`. 