# System Automation Assistant

## Overview

This project provides a framework for a desktop assistant that can understand natural language commands (text or speech) and execute them by controlling your desktop environment (mouse, keyboard, screen analysis). It uses AI (LLMs and computer vision) to interpret commands and interact with GUI elements.

The system can:
*   Analyze the screen to identify UI elements using computer vision (YOLO).
*   Accept commands via a GUI chat interface or potentially voice commands (requires further configuration).
*   Use Large Language Models (LLMs) to understand the command and the screen content.
*   Plan a sequence of actions (clicks, typing, key presses) to achieve the user's goal.
*   Execute these actions using desktop automation tools (`pyautogui`).

## Features

*   **GUI Interface:** Chat-like interface for command input and viewing system responses/logs.
*   **Screen Analysis:** Employs YOLO models to detect UI elements, assigning IDs based on their position (sorted top-to-bottom, left-to-right using element centers for robustness).
*   **Natural Language Understanding:** Uses LLMs to interpret commands in the context of the current screen.
*   **Desktop Control:** Executes actions like clicks, typing, scrolling, key presses.
*   **Task Planning & Execution:** Breaks down complex commands into executable steps (via LLM).
*   **Configurable:** Key settings (API keys, models, theme) managed via `config.yaml` or UI settings dialog.
*   **Modular Structure:** Code organized into distinct components (`core`, `ui`, `utils`, `audio` - *audio components may require setup*).
*   **System Tray Integration:** Provides a tray icon for basic controls (Show/Exit).

## Quick Start

**1. Prerequisites:**

*   **Python:** Version 3.10 or higher recommended.
*   **Conda (Recommended):** For managing the Python environment.
*   **System Dependencies:**
    *   **GUI Libraries:** PyQt6 is used (`pip install PyQt6`).
    *   **(Optional) Audio:** If enabling voice features (Wake Word, STT, TTS):
        *   **PortAudio:** Required by `pyaudio`. Install using your system's package manager:
            *   Debian/Ubuntu: `sudo apt-get update && sudo apt-get install portaudio19-dev python3-pyaudio`
            *   macOS (Homebrew): `brew install portaudio && pip install pyaudio`
            *   Windows: Check `pyaudio` documentation.
        *   **TTS Engines (for `pyttsx3`):** Ensure system TTS engines are installed (e.g., `espeak` on Linux).
        *   **Picovoice Account & Setup (for Wake Word):** See [Picovoice Console](https://console.picovoice.ai/). Requires `AccessKey` and keyword (`.ppn`) files configured in `config.yaml`.
*   **OpenAI API Key (or compatible):**
    *   Required for the LLM interaction (task planning, action generation).
    *   Configure in the UI Settings or `config.yaml`.
*   **YOLO Model Weights:**
    *   Object detection model weights are needed for screen analysis.
    *   The script `scripts/install_deps.py` attempts to download these. Verify the path in `config.yaml` (`vision.yolo_model_path`).

**2. Installation:**

```bash
# Clone the repository
# git clone <your-repo-url>
# cd SystemAutomation

# Create conda environment (recommended)
conda create -n sysauto python=3.12 -y # Or your preferred Python 3.10+ version
conda activate sysauto

# Install core dependencies
pip install -r requirements.txt

# Run the dependency download script (for models)
# Note: This may require manual adjustments depending on model sources
python scripts/install_deps.py

# If install_deps.py has issues, manually ensure model weights
# (e.g., YOLO model) are downloaded and paths are correct in config.yaml
```

**3. Configuration:**

*   Create `config.yaml` in the project root (or copy/modify the example if provided).
*   **Essential:**
    *   `llm.provider` (e.g., `openai` or other compatible provider).
    *   `llm.<provider>.api_key`: Your API key.
    *   `llm.<provider>.base_url` (if not using default OpenAI).
    *   `llm.model`: The specific LLM model to use (e.g., `gpt-4o`).
    *   `vision.yolo_model_path`: Correct path to the downloaded YOLO model weights.
*   **(Optional) Audio Configuration (if enabling):**
    *   `wake_word.enabled`: `true` or `false`.
    *   `wake_word.access_key`: Your Picovoice AccessKey.
    *   `wake_word.keyword_paths`: List containing the *full path* to your `.ppn` file(s).
    *   Review `stt` and `tts` sections for engine choice (OpenAI, System) and related keys/settings.
    *   `audio.input_device_index` / `audio.output_device_index`: May need adjustment based on your system. Use `python -m sounddevice` to list devices.

**4. Running the Assistant:**

```bash
# Activate conda environment
conda activate sysauto

# Run the main application with GUI
python -m src.assistant --gui
```

## Usage

1.  **Launch:** Run `python -m src.assistant --gui`.
2.  **Configure (First time):** Use the "Settings" button to enter your LLM API key, base URL (if needed), and model name.
3.  **Enter Command:** Type your command into the input box at the bottom (e.g., "Open the file explorer", "Find the VS Code icon and click it").
4.  **Send:** Press Enter or click "Send". The window will minimize while processing.
5.  **Observe:** The assistant will analyze the screen, plan steps, and execute them. Status messages appear in the chat window.
6.  **Restore Window:** Click the tray icon or taskbar icon to bring the window back.
7.  **Stop:** Click the "Stop" button in the UI to interrupt the current operation. Use the tray icon's "Exit" option to close the application.

## Project Structure

*   `src/`: Main source code.
    *   `assistant.py`: Main entry point, argument parsing.
    *   `orchestrator.py`: Coordinates components (can handle audio flow if enabled).
    *   `core/`: Handles LLM interaction, screen analysis, action planning & execution.
        *   `screen_analysis.py`: Vision processing, element detection and sorting.
        *   `llm_interaction.py`: Communication with LLM APIs.
        *   `task_processor.py`: Manages the overall task lifecycle.
        *   `action_executor.py`: Executes low-level desktop actions.
    *   `ui/`: PyQt6 GUI components (main window, settings, tray icon).
    *   `audio/`: (Optional) Wake word, STT, TTS components.
    *   `utils/`: Configuration loading, logging, drawing, system info, etc.
*   `scripts/`: Installation and utility scripts.
*   `weights/`: Default location for downloaded model weights.
*   `config.yaml`: User configuration file.
*   `requirements.txt`: Core Python dependencies.
*   `README.md`: This file.

## License

This project is licensed under the MIT License, which allows you to freely use, modify, and distribute the code, provided that you include the copyright notice and disclaimers of warranty.
