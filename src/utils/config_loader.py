#!/usr/bin/env python
"""Utility for loading and accessing configuration settings."""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional

# Assumes config.yaml is in the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_FILE = PROJECT_ROOT / "config.yaml"

_config_cache: Optional[Dict[str, Any]] = None

def load_config(config_path: Path = CONFIG_FILE) -> Dict[str, Any]:
    """Loads the configuration from the YAML file."""
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    if not config_path.is_file():
        # TODO: Handle missing config file more gracefully (e.g., create default)
        print(f"Warning: Configuration file not found at {config_path}")
        _config_cache = {}
        return _config_cache

    try:
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
            if config_data is None:
                _config_cache = {}
            else:
                _config_cache = config_data
            return _config_cache
    except yaml.YAMLError as e:
        print(f"Error parsing configuration file {config_path}: {e}")
        # Maybe raise an error or return default empty config
        raise ValueError(f"Invalid YAML configuration: {e}") from e
    except Exception as e:
        print(f"Error reading configuration file {config_path}: {e}")
        raise

def get_config_value(key: str, default: Any = None) -> Any:
    """Gets a specific value from the loaded configuration."""
    config = load_config(CONFIG_FILE)
    # Allow nested key access, e.g., "llm.api_key"
    keys = key.split('.')
    value = config
    try:
        for k in keys:
            if isinstance(value, dict):
                value = value[k]
            else:
                 # If trying to access subkey of non-dict, return default
                 return default
        return value
    except KeyError:
        return default

# Example usage:
# if __name__ == '__main__':
#     cfg = load_config()
#     print("Full config:", cfg)
#     api_key = get_config_value("llm.openai_api_key", "not_found")
#     print("API Key:", api_key)
#     model = get_config_value("llm.model")
#     print("Model:", model) 