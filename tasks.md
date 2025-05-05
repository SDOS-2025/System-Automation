# S2S Jarvis Assistant Implementation Tasks

Based on `plan.md`.

## Phase 1: Initial Setup and File Migration

- [x] **1. Create Basic Directory Structure:** (`src`, `scripts`, `weights`, `docs`, `tests`)
- [x] **2. Copy Top-Level Files:** (`.gitignore`, `LICENSE`, `README.md`, `requirements.txt`)
- [x] **3. Create Placeholder/Configuration Files:** (`config.yaml`, `Structure.md`, `weights/.gitkeep`)
- [x] **4. Create `src` Subdirectories & `__init__.py` files:** (`audio`, `core`, `utils`)

## Phase 2: Refactoring Existing `autoMate` Code

- [x] **1. Refactor `autoMate/auto_control` -> `src/core`:**
    - [x] Move `computer.py` -> `action_executor.py`
    - [x] Move `screen_capture.py` -> `screen_analysis.py`
    - [x] Merge `vision_agent.py` into `screen_analysis.py`
    - [x] Move `anthropic_executor.py` -> `llm_interaction.py` (initial move)
    - [x] Merge agent logic (`task_plan_agent`, `task_run_agent`) into `llm_interaction.py` (prompts, models, call logic)
    - [x] Merge `app.py` / `loop.py` logic into `task_processor.py`
    - [x] Merge `tools/base.py`, `tools/collection.py` into appropriate `src/core` files (`action_models.py`, `action_executor.py`)
    - [x] Update imports in all moved/refactored files.
- [x] **2. Refactor `autoMate/util` -> `src/utils`:**
    - [x] Move relevant utilities (`download_weights.py`, `screen_selector.py`, `tool.py`).
    - [x] Adapt `download_weights.py` -> `download_models.py`.
    - [x] Create `config_loader.py`, `logging_setup.py` (placeholders).
    - [x] Update imports/comments (`screen_selector.py`).
- [x] **3. Refactor Entry Point (`autoMate/main.py` -> `src/assistant.py`):**
    - [x] Create `assistant.py`.
    - [x] Move/adapt logic from `main.py`.
- [x] **4. Refactor Installation Script (`autoMate/install.py` -> `scripts/install_deps.py`):**
    - [x] Move `install.py`.
    - [x] Update script.
- [x] **5. Handle `autoMate/ui`:**
    - [x] Decide fate (remove/archive). - Removed.

## Phase 3: Implementing S2S Components

- [x] **1. Implement `src/audio/wake_word.py`** (Created initial structure)
- [x] **2. Implement `src/audio/stt.py`** (Created initial structure - OpenAI API)
- [x] **3. Implement `src/audio/tts.py`** (Created initial structure - OpenAI API, System TTS)
- [x] **4. Implement `src/orchestrator.py`** (Created initial structure)

## Phase 4: Integration and Finalization

- [x] **1. Implement `src/utils/config_loader.py`** (Implemented placeholder in Phase 2)
- [x] **2. Implement `src/utils/logging_setup.py`** (Implemented placeholder in Phase 2)
- [x] **3. Update `src/assistant.py`** (Initialization, run orchestrator)
- [x] **4. Update `requirements.txt`** (Added S2S libs, removed unused)
- [x] **5. Update `README.md`** (New description, setup, usage)

## Phase 5: Testing and Running

- [x] **1. Configuration Tests:**
    - [x] Test loading `config.yaml` (valid, missing, invalid format).
    - [x] Test retrieval of different config values (`get_config_value`).
- [x] **2. Utility Tests:**
    - [x] Test `download_models.py` (mock download if possible, check path logic).
    - [x] Test `logging_setup.py` (check log file creation, console output).
    - [ ] (Optional) Test `screen_selector.py` manually or via mock UI events.
- [ ] **3. Core Component Tests (Unit/Integration):**
    - [x] Test `action_models.py` (basic model instantiation, validation if any).
    - [x] Test `action_executor.py` methods (mock `pyautogui` calls, test coordinate clamping, different actions).
    - [x] Test `screen_analysis.py` (provide sample images, check element detection/filtering, test screen capture).
    - [x] Test `llm_interaction.py` (mock LLM calls, test prompt formatting, response parsing).
    - [x] Test `task_processor.py` (mock components, test planning flow, execution flow, state updates).
- [ ] **4. Audio Component Tests (Unit/Integration):**
    - [ ] Test `wake_word.py` (requires manual testing with microphone/config or mocking `pvporcupine`/`pyaudio`).
    - [ ] Test `stt.py` (test recording, test API call with sample audio, test error handling).
    - [ ] Test `tts.py` (test API/engine call, test playback, test different engines if configured).
- [ ] **5. Orchestrator and End-to-End Tests:**
    - [ ] Test `orchestrator.py` initialization with different configs.
    - [ ] Test the main loop flow manually (Wake Word -> STT -> Placeholder Core -> TTS).
    - [ ] Test full E2E flow with simple commands (e.g., "hello", "what time is it?").
    - [ ] Test E2E flow with a basic desktop automation command (e.g., "open calculator").
    - [ ] Test error handling scenarios (e.g., wake word error, STT error, TTS error, core error).
    - [ ] Test `Ctrl+C` shutdown.

## Phase 6: Cleanup and Refinement

- [ ] **1. Code Review**
- [ ] **2. Error Handling**
- [ ] **3. Performance Optimization**
- [ ] **4. Finalize Configuration** 
- [ ] **5. Documentation** 
