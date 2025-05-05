#!/usr/bin/env python
"""Main entry point for the S2S Jarvis Assistant."""

import signal
import sys
import time
import os # Import os for environment variable access example
import logging # Import logging library
from pathlib import Path
import argparse # For command-line arguments
import threading # For running orchestrator in background thread for GUI

# Imports should be relative when running as a module within the package
from .utils.config_loader import load_config, get_config_value
from .utils.logging_setup import setup_logging, get_logger
from .utils.download_models import download_model_weights
from .utils.system_info import get_system_info, DEFAULT_CACHE_DIR
from .orchestrator import Orchestrator
from .core.task_processor import TaskProcessor
# --- GUI Imports (conditional) ---
# Import only if GUI mode is requested to avoid unnecessary dependencies
# from PyQt6.QtWidgets import QApplication
# from SystemAutomation.src.ui.main_window import MainWindow # Keep commented or remove if sure

# Initialize logger for this module first
# We need to call setup_logging early, potentially before loading full config
# TODO: Refine logging setup based on config if needed (e.g., log level)
log_level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_str, logging.INFO)
# TODO: Get log file path from config or use default
setup_logging(log_level=log_level)
logger = get_logger(__name__)

# Global variable to signal shutdown (less used with threading.Event in orchestrator)
# running = True

def run_orchestrator_thread(orchestrator):
    """Target function to run orchestrator loop in a separate thread."""
    try:
        logger.info("Starting orchestrator run loop in background thread...")
        orchestrator.run()
        logger.info("Orchestrator run loop finished in background thread.")
    except Exception as e:
        logger.critical(f"Orchestrator thread encountered a fatal error: {e}", exc_info=True)
        # Optionally signal main thread or GUI about the error

def main():
    parser = argparse.ArgumentParser(description="S2S Jarvis Assistant")
    parser.add_argument("--gui", action="store_true", help="Run with graphical user interface")
    args = parser.parse_args()

    logger.info("Starting S2S Jarvis Assistant...")

    # --- Load Configuration --- #
    try:
        config = load_config()
        logger.info("Configuration loaded successfully.")
        logger.debug(f"TTS Engine from config: {get_config_value('tts.engine', 'default')}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}", exc_info=True)
        print(f"Error: Could not load configuration from config.yaml. Please ensure it exists and is valid.", file=sys.stderr)
        sys.exit(1)

    # --- Gather/Load System Information --- #
    try:
        logger.info("Gathering/loading system information...")
        cache_file_path = DEFAULT_CACHE_DIR / "system_info.json"
        system_info = get_system_info(cache_path=cache_file_path, refresh_apps_if_older_days=1)
        logger.info("System information loaded successfully.")
        # Optional: Log specific info like OS or app count
        logger.debug(f"OS Info: {system_info.get('os_info', {}).get('system')}")
        logger.debug(f"Cached Apps: {len(system_info.get('installed_apps', {}).get('apps', []))}")
    except Exception as e:
        logger.error(f"Failed to get system information: {e}", exc_info=True)
        system_info = {} # Continue with empty info on error?

    # --- Download Necessary Models --- #
    # Check if the primary model file exists before attempting download check
    yolo_model_path_str = get_config_value("screen_analysis.yolo_model_path")
    skip_download = False # Default to attempting download/check
    if yolo_model_path_str:
        # Construct absolute path relative to WORKSPACE root
        yolo_model_full_path = Path(yolo_model_path_str)
        logger.debug(f"Checking for model at calculated path: {yolo_model_full_path}") # Add debug log for path
        if yolo_model_full_path.exists() and yolo_model_full_path.is_file():
            logger.info(f"Model file found at {yolo_model_full_path}. Skipping download check.")
            skip_download = True
        else:
             logger.info(f"Model file not found at {yolo_model_full_path}. Proceeding with download check.")
    else:
        logger.warning("Could not determine model path from config [screen_analysis.yolo_model_path]. Cannot check existence; attempting download check.")

    # skip_download = True # Skip download check as model should already be cached
    if not skip_download:
        try:
            logger.info("Checking/downloading required models...")
            model_id = get_config_value("models.modelscope.id", None)
            file_pattern = get_config_value("models.modelscope.file_pattern", None)
            download_args = {}
            if model_id: download_args['model_id'] = model_id
            if file_pattern: download_args['file_pattern'] = file_pattern
            download_model_weights(**download_args)
            logger.info("Model check/download complete.")
        except Exception as e:
            logger.error(f"Failed during model download: {e}", exc_info=True)
    else:
         logger.info("Skipping model download based on configuration.")

    # --- Initialize Task Processor --- #
    # (Moved initialization here to ensure it happens before Orchestrator)
    task_processor = None 
    try:
        logger.info("Initializing Task Processor...")
        task_processor = TaskProcessor(config, system_info)
    except ValueError as e: 
         logger.critical(f"Configuration error during Task Processor initialization: {e}")
         print(f"Error: Configuration missing required values: {e}. Check config.yaml and logs.", file=sys.stderr)
         sys.exit(1)
    except Exception as e:
         logger.critical(f"Task Processor initialization encountered an unexpected error: {e}", exc_info=True)
         print(f"Error: Task Processor encountered a fatal error during initialization. Check logs.", file=sys.stderr)
         sys.exit(1)

    # --- Initialize Orchestrator --- #
    orchestrator = None
    try:
        logger.info("Initializing Orchestrator...")
        # Pass the created task_processor instance to Orchestrator
        orchestrator = Orchestrator(config, task_processor=task_processor)
    except ValueError as e:
         logger.critical(f"Configuration error during Orchestrator initialization: {e}")
         print(f"Error: Configuration missing required values: {e}. Check config.yaml and logs.", file=sys.stderr)
         sys.exit(1)
    except RuntimeError as e: # Catch specific init errors from Orchestrator
         logger.critical(f"Orchestrator initialization failed: {e}")
         print(f"Error: Failed to initialize assistant components: {e}. Check logs.", file=sys.stderr)
         sys.exit(1)
    except Exception as e:
        logger.critical(f"Orchestrator initialization encountered an unexpected error: {e}", exc_info=True)
        print(f"Error: The assistant encountered a fatal error during initialization. Check logs.", file=sys.stderr)
        sys.exit(1)

    # --- Run Mode: GUI or CLI --- #
    if args.gui:
        logger.info("Running in GUI mode.")
        try:
            # Import GUI components only when needed
            from PyQt6.QtWidgets import QApplication
            # Import the NEW UI entry point
            from ui.main import run_ui # Use absolute import

            app = QApplication(sys.argv)
            orchestrator.is_gui_mode = True # Set GUI mode flag

            # --- Initialize and run the NEW UI ---
            # Assuming run_ui returns the main window or handles showing it
            window = run_ui(orchestrator) # Pass orchestrator

            # If run_ui doesn't return a window or show it, adjust the call:
            # run_ui(orchestrator)
            # And potentially remove window.show() if run_ui handles it.
            # For now, assume it returns a window to be shown.
            if window: # Check if run_ui returned a window object
                 window.show()
            else:
                 logger.warning("run_ui did not return a window object. Assuming it runs the app loop itself.")
                 # If run_ui starts the app.exec_() itself, the code below might not be reached
                 # or might need restructuring depending on how run_ui is implemented.

            # Start orchestrator loop in a separate thread
            orchestrator_thread = threading.Thread(target=run_orchestrator_thread, args=(orchestrator,), daemon=True)
            orchestrator_thread.start()

            # Start Qt event loop (might be redundant if run_ui starts it)
            # Only call app.exec() if run_ui hasn't already started the event loop.
            # Assuming run_ui prepares the window but doesn't block with app.exec()
            exit_code = app.exec()
            logger.info(f"GUI closed with exit code: {exit_code}")
            if orchestrator:
                orchestrator.stop_event.set() # Signal orchestrator thread to stop
            sys.exit(exit_code)

        except ImportError as e:
             logger.error(f"Failed to import PyQt6. Please install it: pip install PyQt6. Error: {e}")
             print("Error: PyQt6 is required for GUI mode but not installed. Run 'pip install PyQt6'.", file=sys.stderr)
             sys.exit(1)
        except Exception as e:
             logger.critical(f"Failed to launch GUI: {e}", exc_info=True)
             print(f"Error: Could not start the GUI. Check logs for details.", file=sys.stderr)
             sys.exit(1)

    else:
        logger.info("Running in Command-Line Interface (CLI) mode.")
        try:
            orchestrator.is_gui_mode = False # Ensure CLI mode flag is set
            logger.info("Starting the orchestrator main loop (CLI mode)...")
            orchestrator.run() # Run blocking loop in main thread
            logger.info("Orchestrator run loop finished (CLI mode).")
        except KeyboardInterrupt:
            logger.info("Assistant stopping due to user interrupt (KeyboardInterrupt).")
        except Exception as e:
            logger.critical(f"Orchestrator encountered a fatal error during run: {e}", exc_info=True)
            print(f"Error: The assistant encountered a fatal error. Check logs for details.", file=sys.stderr)
        finally:
            if orchestrator:
                logger.info("Performing final shutdown (CLI mode)...")
                orchestrator.shutdown()
            logger.info("Assistant shutdown complete (CLI mode).")
            print("Assistant has shut down.")
            sys.exit(0)

if __name__ == "__main__":
    main() 