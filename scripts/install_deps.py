#!/usr/bin/env python
"""Installation script for dependencies and models."""

import subprocess
import sys
import urllib.request
import urllib.error
from pathlib import Path

# Add project root to sys.path to allow imports from src
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Updated import for the download utility
from src.utils.download_models import download_model_weights

def install_requirements():
    """Installs packages from requirements.txt, using a mirror if needed."""
    requirements_path = PROJECT_ROOT / 'requirements.txt'
    if not requirements_path.is_file():
        print(f"Error: requirements.txt not found at {requirements_path}")
        sys.exit(1)

    pip_command = [sys.executable, '-m', 'pip', 'install', '-r', str(requirements_path)]

    # Check if Google is accessible to decide on using a mirror
    try:
        print("Checking internet connectivity to Google...")
        urllib.request.urlopen('https://www.google.com', timeout=5)
        print("Google accessible. Installing requirements normally...")
        subprocess.check_call(pip_command)
    except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
        print(f"Google not accessible ({e}). Using Tsinghua PyPI mirror...")
        mirror_pip_command = pip_command + ['-i', 'https://pypi.tuna.tsinghua.edu.cn/simple']
        try:
            subprocess.check_call(mirror_pip_command)
        except subprocess.CalledProcessError as install_err:
            print(f"Error installing requirements with mirror: {install_err}")
            sys.exit(1)
        except Exception as general_err:
             print(f"An unexpected error occurred during installation: {general_err}")
             sys.exit(1)
    except subprocess.CalledProcessError as install_err:
        print(f"Error installing requirements: {install_err}")
        sys.exit(1)
    except Exception as general_err:
         print(f"An unexpected error occurred during installation: {general_err}")
         sys.exit(1)

    print("Requirements installed successfully.")

def check_python_version():
    """Checks if the current Python version is 3.12."""
    print(f"Checking Python version ({sys.version.split()[0]})...")
    if sys.version_info.major != 3 or sys.version_info.minor != 12:
        print(f"Warning: Recommended Python version is 3.12. You are using {sys.version_info.major}.{sys.version_info.minor}.")
        # Continue installation, but warn the user.
        # sys.exit(1) # Optionally exit if strict matching is required
    else:
        print("Python version 3.12 found.")

def install_all():
    """Runs the full installation process."""
    check_python_version()
    install_requirements()
    # Download the model weights
    print("\nDownloading required models...")
    download_model_weights() # Updated function call
    print("\nInstallation and model download complete!")

if __name__ == "__main__":
    print("Starting installation process...")
    install_all() 