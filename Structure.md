# Proposed Repository Structure for S2S Jarvis Assistant

This document outlines the proposed directory and file structure for the Speech-to-Speech (S2S) Jarvis-like desktop assistant, refactored from the `autoMate` codebase. The goal is modularity and clear separation of concerns.

```
.
├── .gitignore
├── LICENSE
├── README.md                 # Updated project description, setup, usage for S2S assistant
├── requirements.txt          # Updated Python dependencies (including STT, TTS, wake word libs)
├── config.yaml               # Configuration file (API keys, model choices, wake word, audio devices, etc.)
├── Structure.md              # This file
│
├── src/                      # Main source code directory
│   ├── __init__.py
│   ├── assistant.py          # Main application entry point, initializes components, manages main loop
│   ├── orchestrator.py       # Coordinates the flow: wake word -> STT -> core -> TTS
│   │
│   ├── audio/                # Modules related to audio input/output
│   │   ├── __init__.py
│   │   ├── wake_word.py      # Handles wake word detection (e.g., using Porcupine)
│   │   ├── stt.py            # Speech-to-Text: Captures audio, transcribes using selected engine (Whisper, etc.)
│   │   └── tts.py            # Text-to-Speech: Converts text responses to speech (pyttsx3, ElevenLabs, OpenAI TTS, etc.)
│   │
│   ├── core/                 # Core automation logic (Refactored from autoMate/auto_control)
│   │   ├── __init__.py
│   │   ├── llm_interaction.py  # Manages communication with the chosen LLM (OpenAI, Anthropic, etc.)
│   │   ├── screen_analysis.py  # Handles screen capture, OCR, object detection (from autoMate)
│   │   ├── action_executor.py  # Executes desktop actions (mouse, keyboard - from autoMate)
│   │   └── task_processor.py   # Processes transcribed commands, plans steps (if needed), uses other core modules
│   │
│   └── utils/                # Utility functions and classes
│       ├── __init__.py
│       ├── config_loader.py  # Loads and validates settings from config.yaml
│       ├── logging_setup.py  # Configures logging
│       └── download_models.py # Handles downloading necessary models (LLM, vision, STT, wake word) - adapted from autoMate/util/download_weights.py
│
├── scripts/                  # Helper scripts
│   └── install_deps.py       # Installation script (replaces/adapts autoMate/install.py)
│
├── weights/                  # Directory for storing downloaded model weights (same as autoMate)
│   └── .gitkeep              # Placeholder
│
├── docs/                     # Documentation files (optional)
│   └── ...
│
└── tests/                    # Unit and integration tests (optional but recommended)
    └── ...
```

## Key Changes from `autoMate`:

1.  **Source Code Location:** All primary Python code moved into a `src/` directory.
2.  **Entry Point:** Changed from `main.py` to `src/assistant.py`.
3.  **Configuration:** Centralized configuration in `config.yaml`.
4.  **New `audio/` Module:** Added specifically for STT, TTS, and wake word functionality.
5.  **New `orchestrator.py`:** Manages the interaction flow between audio components and the core logic.
6.  **Core Logic Refactoring:** `autoMate/auto_control/` becomes `src/core/` with potentially refined internal structure (`task_processor.py` added for clarity).
7.  **Utility Refactoring:** `autoMate/util/` functions moved/adapted into `src/utils/`.
8.  **UI Removal:** The `autoMate/ui/` (Gradio web UI) is assumed to be removed or replaced, as the primary interface is now speech. A separate configuration UI could be added later if needed.
9.  **Dependency Update:** `requirements.txt` will need significant updates to include libraries for STT (e.g., `openai-whisper`, `SpeechRecognition`), TTS (e.g., `pyttsx3`, `elevenlabs`, `openai`), and wake word detection (e.g., `pvporcupine`).
10. **Installation Script:** `autoMate/install.py` adapted into `scripts/install_deps.py`. 