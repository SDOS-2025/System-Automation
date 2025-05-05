#!/usr/bin/env python
"""Utility to download required model weights."""

import os
from pathlib import Path

# Define weights directory relative to the script's parent's parent (project root)
# Assumes this script stays in SystemAutomation/src/utils/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent # Go up 3 levels
WEIGHTS_DIR = PROJECT_ROOT / "weights"
MODEL_CACHE_SUBDIR = "modelscope_cache" # Subdirectory within weights for modelscope

# TODO: Make model details configurable if necessary
DEFAULT_MODEL_ID = 'AI-ModelScope/OmniParser-v2.0'
DEFAULT_FILE_PATTERN = 'icon_detect/model.pt'

def download_model_weights(model_id: str = DEFAULT_MODEL_ID,
                         file_pattern: str = DEFAULT_FILE_PATTERN,
                         force_download: bool = False):
    """
    Downloads specified model files using modelscope.

    Args:
        model_id: The model ID from ModelScope.
        file_pattern: Glob pattern to filter specific files.
        force_download: If True, redownloads even if files exist.
    """
    try:
        from modelscope.hub.snapshot_download import snapshot_download
        # Using modelscope >= 1.11.0
    except ImportError:
        print("Error: modelscope library not found. Please install it: pip install modelscope")
        return
    except Exception as e:
        print(f"Error importing modelscope: {e}")
        return

    # Define the specific cache directory within weights
    cache_path = WEIGHTS_DIR / MODEL_CACHE_SUBDIR

    print(f"Ensuring weights directory exists: {WEIGHTS_DIR}")
    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Downloading model '{model_id}' (pattern: '{file_pattern}') to cache: {cache_path}")

    try:
        snapshot_download(
            model_id=model_id,
            cache_dir=str(cache_path), # snapshot_download expects string path
            allow_patterns=[file_pattern],
            # revision="master", # Optional: specify a revision
            # ignore_file_pattern=[], # Optional: specify files to ignore
            # force_download=force_download, # Optional: force redownload
        )
        print(f"Model weights downloaded successfully to {cache_path}.")

        # TODO: Verify downloaded file exists and potentially return its path
        # e.g., find the actual model.pt file within the cache structure

    except Exception as e:
        print(f"Error downloading model weights: {e}")
        # Consider raising the exception or returning an error status

if __name__ == "__main__":
    print("Running model download utility...")
    download_model_weights()
    print("Model download utility finished.")