#!/usr/bin/env python
"""Unit tests for ScreenAnalyzer."""

import unittest
from unittest.mock import patch, MagicMock, call
import sys
import os
import tempfile
from pathlib import Path

import numpy as np
import pytest # Use pytest features like fixtures and raises

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Mock libraries used by the module BEFORE importing the module
mock_cv2 = MagicMock()
mock_sv = MagicMock()
mock_ultralytics = MagicMock()
mock_PIL_ImageGrab = MagicMock()
mock_PIL_Image = MagicMock()

sys.modules['cv2'] = mock_cv2
sys.modules['supervision'] = mock_sv
sys.modules['ultralytics'] = mock_ultralytics
sys.modules['PIL.ImageGrab'] = mock_PIL_ImageGrab
sys.modules['PIL.Image'] = mock_PIL_Image # Mock Image within PIL if needed

# Now import the module under test
from src.core.screen_analysis import ScreenAnalyzer, UIElement # Remove ActionError

# --- Test Data ---
DUMMY_MODEL_PATH = "dummy/path/model.pt"
DUMMY_IMAGE_PATH = "dummy/image.png"

# Helper to create mock YOLO results
def create_mock_yolo_result(boxes_xyxy=None):
    mock_result = MagicMock()
    mock_detections = MagicMock()
    if boxes_xyxy is not None:
        mock_detections.xyxy = np.array(boxes_xyxy, dtype=float)
    else:
        mock_detections.xyxy = np.array([], dtype=float)

    # Mock the chain: YOLO() -> result[0] -> sv.Detections -> detections.xyxy
    mock_sv.Detections.from_ultralytics.return_value = mock_detections
    mock_ultralytics.YOLO.return_value.return_value = [mock_result] # YOLO call returns list
    # For simplicity, assume from_ultralytics directly gives detections
    # If it expects the raw result object, adjust mocking accordingly

    return mock_result, mock_detections

# --- Pytest Fixture ---
@pytest.fixture
def analyzer():
    """Fixture to create a ScreenAnalyzer instance with mocked YOLO."""
    # Reset mocks for YOLO specifically for each test via fixture
    mock_ultralytics.YOLO.reset_mock()
    mock_sv.Detections.from_ultralytics.reset_mock()
    mock_ultralytics.YOLO.return_value.reset_mock()
    mock_ultralytics.YOLO.return_value.return_value = [MagicMock()] # Default empty result
    # Reset other relevant mocks used across tests
    mock_cv2.reset_mock()
    mock_PIL_ImageGrab.reset_mock()

    # Create analyzer instance
    instance = ScreenAnalyzer(DUMMY_MODEL_PATH)
    # Check model was initialized
    mock_ultralytics.YOLO.assert_called_once_with(DUMMY_MODEL_PATH)
    return instance

# --- Test Functions ---

def test_analyzer_init(analyzer):
    """Test ScreenAnalyzer initialization."""
    assert analyzer.yolo_model is not None
    # Check YOLO was called by fixture setup
    mock_ultralytics.YOLO.assert_called_with(DUMMY_MODEL_PATH)

# --- Tests for _filter_contained_boxes ---

def test_filter_no_boxes(analyzer):
    assert analyzer._filter_contained_boxes(np.array([])).shape == (0,)

def test_filter_single_box(analyzer):
    boxes = np.array([[10, 10, 100, 100]])
    assert np.array_equal(analyzer._filter_contained_boxes(boxes), boxes)

def test_filter_identical_boxes(analyzer):
    boxes = np.array([[10, 10, 100, 100], [10, 10, 100, 100]])
    # Keeps one of the identical boxes (implementation detail might vary which one)
    filtered = analyzer._filter_contained_boxes(boxes)
    assert len(filtered) == 1
    assert np.array_equal(filtered[0], [10, 10, 100, 100])

def test_filter_simple_containment(analyzer):
    """Test one box fully inside another."""
    boxes = np.array([
        [10, 10, 100, 100], # Outer
        [30, 30, 70, 70]   # Inner (should be removed)
    ])
    expected = np.array([[10, 10, 100, 100]])
    filtered = analyzer._filter_contained_boxes(boxes)
    assert len(filtered) == 1
    assert np.array_equal(filtered, expected)

def test_filter_multiple_containment(analyzer):
    """Test multiple levels of containment."""
    boxes = np.array([
        [10, 10, 100, 100], # Outer
        [20, 20, 80, 80],   # Middle (contained by outer)
        [30, 30, 70, 70],   # Inner (contained by middle and outer)
        [110, 110, 150, 150] # Separate
    ])
    # Should keep only the outer box and the separate box
    filtered = analyzer._filter_contained_boxes(boxes)
    assert len(filtered) == 2
    # Use set comparison for order independence
    expected_set = {tuple(row) for row in [[10, 10, 100, 100], [110, 110, 150, 150]]}
    filtered_set = {tuple(row) for row in filtered}
    assert filtered_set == expected_set

def test_filter_overlapping_no_containment(analyzer):
    """Test overlapping boxes where neither is fully contained."""
    boxes = np.array([
        [10, 10, 50, 50],
        [30, 30, 70, 70]
    ])
    filtered = analyzer._filter_contained_boxes(boxes)
    assert len(filtered) == 2 # Both should be kept
    assert np.array_equal(np.sort(filtered, axis=0), np.sort(boxes, axis=0))

def test_filter_touching_boxes(analyzer):
    """Test boxes touching at edges/corners."""
    boxes = np.array([
        [10, 10, 50, 50],
        [50, 10, 90, 50]  # Touching side
    ])
    filtered = analyzer._filter_contained_boxes(boxes)
    assert len(filtered) == 2

def test_filter_zero_area_boxes(analyzer):
    """Test filtering out boxes with zero or negative area."""
    boxes = np.array([
        [10, 10, 100, 100],
        [50, 50, 50, 60],  # Zero width
        [60, 60, 70, 60],  # Zero height
        [80, 80, 70, 90]   # Negative width
    ])
    expected = np.array([[10, 10, 100, 100]])
    filtered = analyzer._filter_contained_boxes(boxes)
    assert len(filtered) == 1
    assert np.array_equal(filtered, expected)

# --- Tests for analyze_image ---

def test_analyze_image_no_detections(analyzer):
    """Test analysis when YOLO finds nothing."""
    create_mock_yolo_result([]) # Setup mock YOLO to return no boxes
    dummy_image = np.zeros((200, 200, 3), dtype=np.uint8)
    elements = analyzer.analyze_image(dummy_image)
    assert elements == []

def test_analyze_image_with_detections(analyzer):
    """Test analyze_image assigns elements correctly from _detect_objects result."""
    # Simulate the final, filtered boxes returned by _detect_objects
    final_boxes = np.array([
        [10, 10, 50, 50],
        [100, 100, 150, 150]
    ])
    dummy_image = np.zeros((200, 200, 3), dtype=np.uint8)

    # Mock _detect_objects to return the final expected boxes
    with patch.object(analyzer, '_detect_objects', return_value=final_boxes) as mock_detect:

        elements = analyzer.analyze_image(dummy_image)

        # --- Assertions ---
        mock_detect.assert_called_once_with(dummy_image)
        # _filter_contained_boxes is inside _detect_objects, so not called directly by analyze_image

        # Check final elements based on the direct output of (mocked) _detect_objects
        assert len(elements) == 2
        assert isinstance(elements[0], UIElement)
        coords_set = {tuple(e.coordinates) for e in elements}
        expected_coords_set = {tuple(b) for b in final_boxes}
        assert coords_set == expected_coords_set
        # Check IDs are assigned sequentially
        ids = sorted([e.element_id for e in elements])
        assert ids == [0, 1]

# --- Tests for analyze_image_from_path ---

def test_analyze_image_from_path_success(analyzer):
    """Test reading and analyzing from a path."""
    final_boxes = [[20, 30, 40, 50]]
    dummy_image_array = np.zeros((100, 100, 3), dtype=np.uint8)
    mock_cv2.imread.return_value = dummy_image_array

    # Mock the internal _analyze_image to check it's called
    expected_elements = [UIElement(element_id=0, coordinates=final_boxes[0])]
    with patch.object(analyzer, '_analyze_image', return_value=expected_elements) as mock_analyze:
        elements = analyzer.analyze_image_from_path(DUMMY_IMAGE_PATH)

        mock_cv2.imread.assert_called_once_with(DUMMY_IMAGE_PATH)
        mock_analyze.assert_called_once() # Check _analyze_image was called
        # Check the argument passed to _analyze_image
        np.testing.assert_array_equal(mock_analyze.call_args[0][0], dummy_image_array)
        assert elements == expected_elements

def test_analyze_image_from_path_not_found(analyzer):
    """Test analysis when image file not found."""
    mock_cv2.imread.return_value = None # Simulate file not found/read error
    with pytest.raises(FileNotFoundError):
        analyzer.analyze_image_from_path("non_existent.png")
    mock_cv2.imread.assert_called_once_with("non_existent.png")

# --- Tests for capture_screen (more complex due to file I/O) ---

@patch('os.close') # Mock os.close for tempfile
@patch('tempfile.mkstemp', return_value=(123, "/tmp/test_screenshot.png"))
def test_capture_screen_temp_file(mock_mkstemp, mock_os_close, analyzer):
    """Test screen capture saves to a temporary file."""
    mock_screenshot = MagicMock()
    mock_PIL_ImageGrab.grab.return_value = mock_screenshot

    file_path = analyzer.capture_screen()

    mock_PIL_ImageGrab.grab.assert_called_once()
    mock_mkstemp.assert_called_once_with(suffix=".png")
    mock_os_close.assert_called_once_with(123)
    assert file_path == "/tmp/test_screenshot.png"
    mock_screenshot.save.assert_called_once_with(file_path)

@patch('pathlib.Path.mkdir') # Mock mkdir for target directory
def test_capture_screen_specific_path(mock_mkdir, analyzer):
    """Test screen capture saves to a specific file path."""
    mock_screenshot = MagicMock()
    mock_PIL_ImageGrab.grab.return_value = mock_screenshot
    target_path = "/path/to/save/screenshot.png"

    # Need to ensure the parent dir exists for save typically, mocking mkdir covers this
    file_path = analyzer.capture_screen(file_path=target_path)

    mock_PIL_ImageGrab.grab.assert_called_once()
    assert file_path == target_path
    mock_screenshot.save.assert_called_once_with(target_path)
    # mock_mkdir maybe called by save, depending on implementation

# Add tests for capture_screen error handling (ImageGrab fails, tempfile fails, save fails)

# Add tests for _detect_objects if needed (mocking yolo_model call, sv.Detections etc.) 