#!/usr/bin/env python
"""Unit tests for the download_models utility."""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
from pathlib import Path

# Add project root to sys.path to allow imports from src
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent # Adjust path as necessary
sys.path.insert(0, str(PROJECT_ROOT))

# Now import the module to test
try:
    from src.utils import download_models
except ImportError as e:
    # Handle case where module might not be found during test discovery
    # This might happen depending on how tests are run
    print(f"Error importing download_models: {e}")
    download_models = None # Set to None to avoid errors later if import fails

# Define expected paths relative to the test file or a known structure
TEST_UTILS_DIR = Path(__file__).resolve().parent
TEST_TESTS_DIR = TEST_UTILS_DIR.parent
TEST_SYSTEM_AUTOMATION_DIR = TEST_TESTS_DIR.parent
EXPECTED_PROJECT_ROOT = TEST_SYSTEM_AUTOMATION_DIR.parent # Should match PROJECT_ROOT above
EXPECTED_WEIGHTS_DIR = EXPECTED_PROJECT_ROOT / "weights"
EXPECTED_CACHE_SUBDIR = "modelscope_cache"

class TestDownloadModels(unittest.TestCase):

    def setUp(self):
        """Set up test environment if needed."""
        # Reset any module-level states if necessary (e.g., clear cached paths)
        pass

    def tearDown(self):
        """Clean up after tests if needed."""
        # e.g., remove dummy files/directories created
        pass

    @unittest.skipIf(download_models is None, "Skipping tests because download_models module failed to import")
    def test_constants_paths(self):
        """Verify the calculated constant paths."""
        self.assertEqual(download_models.PROJECT_ROOT, EXPECTED_PROJECT_ROOT)
        self.assertEqual(download_models.WEIGHTS_DIR, EXPECTED_WEIGHTS_DIR)
        self.assertEqual(download_models.MODEL_CACHE_SUBDIR, EXPECTED_CACHE_SUBDIR)

    @unittest.skipIf(download_models is None, "Skipping tests because download_models module failed to import")
    @patch('pathlib.Path.mkdir') # Mock mkdir to avoid creating dirs
    @patch('modelscope.hub.snapshot_download.snapshot_download')
    def test_download_model_weights_calls_snapshot(self, mock_snapshot_download, mock_mkdir):
        """Test that download_model_weights calls snapshot_download correctly."""
        test_model_id = "test/model-id"
        test_file_pattern = "model.pt"
        expected_cache_path = EXPECTED_WEIGHTS_DIR / EXPECTED_CACHE_SUBDIR

        download_models.download_model_weights(
            model_id=test_model_id,
            file_pattern=test_file_pattern
        )

        # Check that mkdir was called to create the weights dir
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

        # Check that snapshot_download was called once with the correct args
        mock_snapshot_download.assert_called_once_with(
            model_id=test_model_id,
            cache_dir=str(expected_cache_path),
            allow_patterns=[test_file_pattern]
        )

    @unittest.skipIf(download_models is None, "Skipping tests because download_models module failed to import")
    @patch('pathlib.Path.mkdir') # Mock mkdir
    @patch('modelscope.hub.snapshot_download.snapshot_download', side_effect=Exception("Download failed"))
    @patch('builtins.print') # Mock print to check error message
    def test_download_model_weights_handles_exception(self, mock_print, mock_snapshot_download, mock_mkdir):
        """Test that download_model_weights handles exceptions during download."""
        test_model_id = "test/error-model"
        test_file_pattern = "error.pt"

        download_models.download_model_weights(
            model_id=test_model_id,
            file_pattern=test_file_pattern
        )

        # Check that print was called with an error message
        mock_print.assert_any_call(f"Error downloading model weights: Download failed")
        # Check that the download function was called
        mock_snapshot_download.assert_called_once()

    # --- More tests will go here ---

if __name__ == '__main__':
    unittest.main() 