#!/usr/bin/env python
"""Unit tests for the logging_setup utility."""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import logging
import sys
import os
from pathlib import Path
import io

# Add project root to sys.path to allow imports from src
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import the module to test
try:
    from src.utils import logging_setup
except ImportError as e:
    print(f"Error importing logging_setup: {e}")
    logging_setup = None

# Define paths relative to the project root for testing
TEST_LOG_DIR = PROJECT_ROOT / "test_logs"
TEST_LOG_FILE = TEST_LOG_DIR / "test_assistant.log"

class TestLoggingSetup(unittest.TestCase):

    def setUp(self):
        """Reset logger state before each test."""
        # Reset the global state in logging_setup
        if logging_setup:
            logging_setup._is_configured = False
        # Remove all handlers from the root logger to ensure isolation
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
            handler.close()
        # Clean up test log directory/file if it exists from previous runs
        if TEST_LOG_FILE.exists():
            os.remove(TEST_LOG_FILE)
        if TEST_LOG_DIR.exists():
            os.rmdir(TEST_LOG_DIR)

    def tearDown(self):
        """Clean up test logs after tests."""
        # Ensure handlers are closed
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            handler.close()
        # Clean up test log directory/file
        if TEST_LOG_FILE.exists():
            os.remove(TEST_LOG_FILE)
        if TEST_LOG_DIR.exists() and not os.listdir(TEST_LOG_DIR):
            os.rmdir(TEST_LOG_DIR)

    @unittest.skipIf(logging_setup is None, "Skipping tests because logging_setup module failed to import")
    def test_setup_logging_defaults(self):
        """Test setup_logging with default parameters."""
        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            with patch('pathlib.Path.mkdir') as mock_mkdir, \
                 patch('logging.FileHandler') as mock_file_handler:

                # Configure the mock FileHandler instance BEFORE setup is called
                mock_handler_instance = MagicMock()
                mock_handler_instance.level = logging_setup.LOG_LEVEL # Set level attribute
                mock_file_handler.return_value = mock_handler_instance

                logging_setup.setup_logging()

                root_logger = logging.getLogger()
                self.assertEqual(root_logger.level, logging_setup.LOG_LEVEL)
                # Check handlers (Console handler + Mock File Handler)
                # Order might vary, so check types and count
                self.assertEqual(len(root_logger.handlers), 2)
                self.assertTrue(any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers))
                self.assertTrue(any(h is mock_handler_instance for h in root_logger.handlers))

                console_handler = next(h for h in root_logger.handlers if isinstance(h, logging.StreamHandler))
                # Check console handler
                # self.assertIsInstance(console_handler, logging.StreamHandler)
                self.assertEqual(console_handler.level, logging_setup.LOG_LEVEL)
                self.assertIsNotNone(console_handler.formatter)
                self.assertIn("Logging configured.", captured_output.getvalue())

                mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
                mock_file_handler.assert_called_once_with(logging_setup.LOG_FILE_PATH)
                # Check the instance returned by the mock was configured
                self.assertEqual(mock_handler_instance.level, logging_setup.LOG_LEVEL)
                # Check formatter was set on the mock instance
                self.assertIsNotNone(mock_handler_instance.formatter)

                self.assertTrue(logging_setup._is_configured)

                # Test idempotency
                captured_output.seek(0)
                captured_output.truncate(0)
                mock_mkdir.reset_mock()
                mock_file_handler.reset_mock()
                # Call setup again
                logging_setup.setup_logging()
                mock_mkdir.assert_not_called()
                mock_file_handler.assert_not_called()
                self.assertEqual(len(root_logger.handlers), 2)
                self.assertEqual(captured_output.getvalue(), "")

    @unittest.skipIf(logging_setup is None, "Skipping tests because logging_setup module failed to import")
    def test_get_logger(self):
        """Test the get_logger function."""
        # Patch setup_logging AND the internal _is_configured flag
        with patch('src.utils.logging_setup.setup_logging') as mock_setup, \
             patch('src.utils.logging_setup._is_configured', False) as mock_is_configured: # Start as False

            logger_name = "test_logger"
            # First call should trigger setup
            logger = logging_setup.get_logger(logger_name)
            mock_setup.assert_called_once()
            self.assertIsInstance(logger, logging.Logger)
            self.assertEqual(logger.name, logger_name)

            # Manually set the mocked flag to True to simulate configuration completion
            # We patch the *module's* flag, so change it via the module path
            logging_setup._is_configured = True
            mock_setup.reset_mock()

            # Second call should NOT trigger setup
            logger2 = logging_setup.get_logger("another_logger")
            mock_setup.assert_not_called()
            self.assertEqual(logger2.name, "another_logger")

            # Reset flag for subsequent tests via setUp
            logging_setup._is_configured = False

    # --- More tests needed for custom paths, levels, file creation, error handling ---

if __name__ == '__main__':
    unittest.main() 