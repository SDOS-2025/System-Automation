#!/usr/bin/env python
"""Utility functions for drawing on images."""

import os
from typing import List
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2

# Use relative imports
from ..core.screen_analysis import UIElement

def draw_elements(image: Image.Image, elements: List[UIElement]) -> Image.Image:
    """
    Draws bounding boxes and element IDs onto a copy of the input image.

    Args:
        image: The PIL Image to draw on.
        elements: A list of UIElement objects with coordinates and IDs.

    Returns:
        A new PIL Image with annotations drawn.
    """
    if not elements:
        return image # Return original image if no elements

    draw = ImageDraw.Draw(image)

    # Try to load Consolas Bold, fall back if not found
    font_size = 16
    font = None
    # Update this list with the actual filenames found by `ls -l ~/.local/share/fonts/ | grep -i consola`
    # Prioritize Bold and Regular variants.
    
    # Get user's home directory
    home_dir = os.path.expanduser("~")
    font_dir = os.path.join(home_dir, ".local", "share", "fonts")

    font_names_to_try = [
        os.path.join(font_dir, "CONSOLAB.TTF"),      # Bold (Absolute Path)
        os.path.join(font_dir, "Consolas.ttf"),      # Regular (Absolute Path)
        os.path.join(font_dir, "CONSOLA.TTF"),       # Regular Alternate (Absolute Path)
        os.path.join(font_dir, "consolai.ttf"),      # Italic (Absolute Path)
        os.path.join(font_dir, "consolaz.ttf"),      # Bold Italic (Absolute Path)
        "DejaVuSans-Bold.ttf" # Fallback option (Keep this non-absolute)
    ]
    
    for font_path in font_names_to_try:
        try:
            font = ImageFont.truetype(font_path, font_size)
            print(f"Using font: {font_path}") # Print full path now
            break # Found a font, exit loop
        except IOError:
            print(f"Font '{font_path}' not found, trying next...")
            continue

    # If no specific font was loaded, use default
    if font is None:
        try:
             print(f"Warning: Consolas Bold font variations not found. Using default PIL font.")
             font = ImageFont.load_default(size=font_size)
        except AttributeError:
            print("Warning: Cannot request size for default font. Using smallest default.")
            font = ImageFont.load_default()
        except IOError as e:
             print(f"Warning: Error loading default font: {e}")
             # Final fallback if even default fails (very unlikely)
             font = ImageFont.load_default() 

    text_color = "#0000FF" # Blue
    background_color = "#FFFF00" # Yellow
    outline_color = "red" # Keep outline red for now
    outline_width = 2

    for element in elements:
        coords = element.coordinates
        element_id = element.element_id

        # Ensure coordinates are valid
        if len(coords) == 4:
            x1, y1, x2, y2 = map(int, coords) # Convert to int for drawing

            # Draw bounding box
            draw.rectangle([x1, y1, x2, y2], outline=outline_color, width=outline_width)

            # Prepare text label (just the number)
            label = f"{element_id}"

            # Calculate text position (top-left corner, slightly inside the box)
            text_x = x1 + 3
            text_y = y1 + 1

            # Draw a background rectangle for the text
            try:
                # Use textbbox for better background sizing
                text_bbox = draw.textbbox((text_x, text_y), label, font=font)
                # Add padding to background
                text_bg_coords = (text_bbox[0]-2, text_bbox[1]-1, text_bbox[2]+2, text_bbox[3]+1)
                draw.rectangle(text_bg_coords, fill=background_color)
            except Exception as e:
                 print(f"Warning: Could not draw text background for ID {element_id}: {e}") 
                 pass

            # Draw text label
            draw.text((text_x, text_y), label, fill=text_color, font=font)

    return image 