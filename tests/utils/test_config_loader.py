#!/usr/bin/env python
"""Unit tests for the config_loader utility."""

import unittest
import sys
import os
from pathlib import Path
import yaml # Import yaml to check for YAMLError

# Now import the module to test
# Ensure this import works when run from SystemAutomation dir
from src.utils import config_loader

TEST_DIR = Path(__file__).resolve().parent

class TestConfigLoader(unittest.TestCase):

    def setUp(self):
        """Prepare paths to test config files."""
        self.valid_config_path = TEST_DIR / "valid_config.yaml"
        self.invalid_config_path = TEST_DIR / "invalid_config.yaml"
        self.empty_config_path = TEST_DIR / "empty_config.yaml"
        self.non_existent_path = TEST_DIR / "non_existent_config.yaml"
        # Ensure non-existent file really doesn't exist
        if self.non_existent_path.exists():
            os.remove(self.non_existent_path)

    def tearDown(self):
        """Clear the config cache after each test."""
        config_loader._config_cache = None

    def test_load_valid_config(self):
        """Test loading a correctly formatted YAML file."""
        config = config_loader.load_config(self.valid_config_path)
        self.assertIsNotNone(config)
        self.assertIsInstance(config, dict)
        self.assertEqual(config.get("project_name"), "Jarvis Assistant")
        self.assertEqual(config.get("version"), 0.1)
        self.assertIn("llm", config)
        self.assertEqual(config["llm"].get("model"), "gpt-4.1-mini")

    def test_load_non_existent_config(self):
        """Test loading a path that does not exist."""
        # Should ideally log a warning but return an empty dict
        # Redirect stderr/stdout if we want to check warnings, but for now check return
        config = config_loader.load_config(self.non_existent_path)
        self.assertIsNotNone(config)
        self.assertEqual(config, {})

    def test_load_invalid_config(self):
        """Test loading a file with invalid YAML syntax."""
        # Should raise ValueError (wrapping yaml.YAMLError)
        with self.assertRaises(ValueError) as cm:
            config_loader.load_config(self.invalid_config_path)
        self.assertIn("Invalid YAML configuration", str(cm.exception))
        # Check that the cause is YAMLError if possible (depends on Python version)
        if hasattr(cm.exception, '__cause__'):
            self.assertIsInstance(cm.exception.__cause__, yaml.YAMLError)

    def test_load_empty_config(self):
        """Test loading an empty YAML file."""
        config = config_loader.load_config(self.empty_config_path)
        self.assertIsNotNone(config)
        self.assertEqual(config, {})

    def test_config_caching(self):
        """Test that the configuration is cached after the first load."""
        config1 = config_loader.load_config(self.valid_config_path)
        # Modify the cache directly to see if second call returns modified version
        config_loader._config_cache["test_cache_key"] = "cached_value"
        config2 = config_loader.load_config(self.valid_config_path) # Should return cached version

        self.assertIs(config1, config2) # Should be the same object
        self.assertEqual(config2.get("test_cache_key"), "cached_value")

    def test_get_config_value_valid(self):
        """Test getting existing top-level and nested values."""
        # Load config first
        config_loader.load_config(self.valid_config_path)

        self.assertEqual(config_loader.get_config_value("project_name"), "Jarvis Assistant")
        self.assertEqual(config_loader.get_config_value("version"), 0.1)
        self.assertEqual(config_loader.get_config_value("llm.provider"), "openai")
        self.assertEqual(config_loader.get_config_value("llm.api_key"), "sk-dummy-key-from-yaml")
        self.assertEqual(config_loader.get_config_value("tts.system.rate"), 150)
        self.assertEqual(config_loader.get_config_value("picovoice.keyword_paths"), ["/path/to/keywords/jarvis.ppn"])

    def test_get_config_value_missing(self):
        """Test getting missing keys with and without defaults."""
        config_loader.load_config(self.valid_config_path)

        self.assertIsNone(config_loader.get_config_value("non_existent_key"))
        self.assertEqual(config_loader.get_config_value("non_existent_key", "default_val"), "default_val")
        # Missing nested key
        self.assertIsNone(config_loader.get_config_value("llm.missing_sub_key"))
        self.assertEqual(config_loader.get_config_value("llm.missing_sub_key", 123), 123)
        # Missing parent key
        self.assertIsNone(config_loader.get_config_value("missing_parent.sub_key"))
        self.assertEqual(config_loader.get_config_value("missing_parent.sub_key", True), True)
        # Accessing subkey of non-dict
        self.assertIsNone(config_loader.get_config_value("version.subkey"))
        self.assertEqual(config_loader.get_config_value("version.subkey", "fallback"), "fallback")
        # Check missing key defined in YAML but commented out
        self.assertIsNone(config_loader.get_config_value("picovoice.access_key"))
        self.assertEqual(config_loader.get_config_value("picovoice.access_key", "default_acc_key"), "default_acc_key")

    def test_get_config_value_before_load(self):
        """Test that get_config_value triggers loading if cache is empty."""
        # Ensure cache is empty
        config_loader._config_cache = None
        # Replace default CONFIG_FILE path temporarily for this test
        original_config_file = config_loader.CONFIG_FILE
        config_loader.CONFIG_FILE = self.valid_config_path
        try:
            value = config_loader.get_config_value("project_name")
            self.assertEqual(value, "Jarvis Assistant")
            # Check cache is now populated
            self.assertIsNotNone(config_loader._config_cache)
            self.assertEqual(config_loader._config_cache.get("project_name"), "Jarvis Assistant")
        finally:
            # Restore original config file path
            config_loader.CONFIG_FILE = original_config_file

if __name__ == '__main__':
    unittest.main()
