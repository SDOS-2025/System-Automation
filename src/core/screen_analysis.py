#!/usr/bin/env python
"""Analyzes screen content using computer vision."""

import os
import platform
import tempfile
from typing import List, Optional

import cv2
import numpy as np
import supervision as sv
from PIL import Image, ImageGrab
from pydantic import BaseModel
from ultralytics import YOLO

# Models/Errors (if needed, but not currently used here)
# from .action_models import ActionError

class UIElement(BaseModel):
    """Represents a detected UI element with ID and coordinates."""
    element_id: int
    coordinates: List[float] # [x1, y1, x2, y2]

class ScreenAnalyzer:
    """Handles screen capture and vision-based analysis."""
    def __init__(self, yolo_model_path: str):
        """Initializes the analyzer with the YOLO model path."""
        # TODO: Add error handling for model loading
        self.yolo_model = YOLO(yolo_model_path)
        self.elements: List[UIElement] = []

    def capture_screen(self, file_path: Optional[str] = None) -> str:
        """
        Captures the primary screen and saves it to a file.
        Returns the path to the saved file.
        """
        try:
            # Use Pillow's ImageGrab for cross-platform compatibility
            screenshot = ImageGrab.grab()
        except Exception as e:
             # TODO: Add more specific error handling for different OS issues
             raise OSError(f"Failed to capture screenshot using ImageGrab: {e}") from e

        # Determine save path
        if file_path is None:
            # Create a temporary file if no path is provided
            try:
                fd, temp_path = tempfile.mkstemp(suffix=".png")
                os.close(fd)
                file_path = temp_path
            except Exception as e:
                 raise OSError(f"Failed to create temporary screenshot file: {e}") from e

        # Save the screenshot
        try:
            screenshot.save(file_path)
            return file_path
        except Exception as e:
            raise OSError(f"Failed to save screenshot to {file_path}: {e}") from e

    def analyze_image_from_path(self, image_path: str) -> List[UIElement]:
        """Loads an image from path and analyzes it using OpenCV and YOLO."""
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise FileNotFoundError(f"ScreenAnalyzer: Failed to read image at {image_path}")
            return self._analyze_image(image)
        except FileNotFoundError:
            raise
        except Exception as e:
            # TODO: Log error
            print(f"Error analyzing image from path {image_path}: {e}")
            raise ActionError(f"Failed to analyze image: {e}") from e # Use ActionError if applicable

    def analyze_image(self, image: np.ndarray) -> List[UIElement]:
        """Processes an image numpy array (BGR format)."""
        try:
            return self._analyze_image(image)
        except Exception as e:
            # TODO: Log error
            print(f"Error analyzing image array: {e}")
            raise ActionError(f"Failed to analyze image array: {e}") from e # Use ActionError if applicable

    def _reset_state(self):
        """Clear previous analysis results."""
        self.elements = []

    def _analyze_image(self, image: np.ndarray) -> List[UIElement]:
        """
        Internal method to process an image through computer vision pipelines.
        Assigns element IDs based on grid-based sorting (top-to-bottom, left-to-right).

        Args:
            image: Input image in BGR format (OpenCV default)

        Returns:
            List of detected UI elements (with bbox coordinates) sorted by grid position.
        """
        self._reset_state()

        boxes = self._detect_objects(image) # Filtered boxes [x1, y1, x2, y2]

        if boxes is None or len(boxes) == 0:
            return []

        # Calculate grid coordinates for sorting
        # Use center y for vertical grouping, top-left x for horizontal
        center_y = (boxes[:, 1] + boxes[:, 3]) / 2
        grid_x = (boxes[:, 0] // 30).astype(int)
        grid_y = (center_y // 30).astype(int) # Apply grid size to center y

        # Sort based on grid coordinates (primarily grid_y, then grid_x)
        # lexsort sorts by last key first
        sort_indices = np.lexsort((grid_x, grid_y))
        sorted_boxes = boxes[sort_indices]

        # Convert sorted boxes to list and assign sequential IDs
        # Store the original bbox coordinates in the elements
        self.elements = [
            UIElement(element_id=idx, coordinates=box.tolist())
            for idx, box in enumerate(sorted_boxes) # Assign ID based on grid-sorted order
        ]

        return self.elements # Return elements sorted by grid, containing bbox coords

    def _detect_objects(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Runs the object detection pipeline and filters overlapping boxes."""
        try:
            # Ensure image is in the correct format if needed
            # image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = self.yolo_model(image, conf=0.10)[0] # Reduced confidence from 0.15
            detections = sv.Detections.from_ultralytics(results)
            boxes = detections.xyxy # Get bounding boxes [x1, y1, x2, y2]
        except Exception as e:
            # TODO: Add proper logging here
            print(f"Error during YOLO detection: {e}")
            return None

        if boxes is None or len(boxes) == 0:
            return None

        # Filter out boxes contained entirely within others (non-maximum suppression variant)
        try:
            return self._filter_contained_boxes(boxes)
        except Exception as e:
             # TODO: Log error
             print(f"Error filtering boxes: {e}")
             return boxes # Return unfiltered boxes on error?

    def _filter_contained_boxes(self, boxes: np.ndarray) -> np.ndarray:
        """Filters out boxes that are fully contained within larger boxes."""
        if len(boxes) <= 1:
            return boxes

        areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])

        # Handle potential division by zero or negative areas if coordinates are invalid
        valid_indices = np.where(areas > 0)[0]
        if len(valid_indices) < len(areas):
            print(f"Warning: Detected {len(areas) - len(valid_indices)} boxes with zero/negative area. Filtering them out.") # TODO: Use logging
            boxes = boxes[valid_indices]
            areas = areas[valid_indices]
            if len(boxes) <= 1:
                return boxes

        # Sort boxes by area descending - THIS is crucial for the filtering logic
        area_sorted_indices = np.argsort(-areas)
        # Keep original indices for final return
        original_indices = np.arange(len(boxes))
        
        keep_mask = np.ones(len(boxes), dtype=bool)
        for i_idx in area_sorted_indices: # Iterate using indices sorted by area
            if not keep_mask[i_idx]:
                continue
            # Check against all subsequent boxes *in the area-sorted list*
            current_box = boxes[i_idx]
            # Find where i_idx appears in area_sorted_indices to slice correctly
            current_pos_in_sorted = np.where(area_sorted_indices == i_idx)[0][0]
            
            for j_idx in area_sorted_indices[current_pos_in_sorted + 1:]:
                if keep_mask[j_idx]:
                    other_box = boxes[j_idx]
                    # Check if other_box is fully contained within current_box
                    is_contained = (
                        current_box[0] <= other_box[0] and
                        current_box[1] <= other_box[1] and
                        current_box[2] >= other_box[2] and
                        current_box[3] >= other_box[3]
                    )
                    if is_contained:
                        keep_mask[j_idx] = False # Mark the contained box for removal

        # Return the boxes corresponding to the original indices that were kept
        return boxes[keep_mask]