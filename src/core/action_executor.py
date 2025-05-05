#!/usr/bin/env python
"""Executes desktop automation actions using pyautogui."""

import time
import platform
from typing import Optional, Tuple, List

import pyautogui
import pyperclip
import logging

# Core models/enums
from .action_models import ActionResult, ActionError
from .llm_interaction import Action # Import Action enum

# TODO: Make delays configurable
TYPING_DELAY_SECS = 0.05 # Delay between key presses for typing
ACTION_DELAY_SECS = 0.5 # Short delay after actions like clicks
WAIT_DELAY_SECS = 1.0 # Default delay for explicit wait action

# Key name mapping (from autoMate/auto_control/tools/computer.py)
# Add more mappings as needed (e.g., for function keys, modifiers)
PYAUTOGUI_KEY_MAP = {
    "Page_Down": "pagedown",
    "Page_Up": "pageup",
    "Super_L": "win",       # Windows/Super key (Left)
    "Super_R": "win",       # Windows/Super key (Right)
    "Escape": "esc",
    "Enter": "enter",
    "Tab": "tab",
    "Delete": "delete",
    "Backspace": "backspace",
    "Home": "home",
    "End": "end",
    "Up": "up",
    "Down": "down",
    "Left": "left",
    "Right": "right",
    # Add Ctrl, Alt, Shift if needed for hotkeys, though pyautogui handles them separately
}

logger = logging.getLogger(__name__)

class ActionExecutor:
    """Handles the execution of specific desktop actions."""

    def __init__(self):
        # Get screen dimensions on initialization
        try:
            self.width, self.height = pyautogui.size()
        except Exception as e:
            # TODO: Log this error properly
            print(f"Warning: Failed to get screen size. Coordinates might be inaccurate. Error: {e}")
            self.width, self.height = None, None

    def _validate_coordinates(self, x: int, y: int) -> Tuple[int, int]:
        """Validates and clamps coordinates to screen boundaries."""
        if self.width is None or self.height is None:
            # If screen size unknown, perform basic type check
            if not isinstance(x, int) or not isinstance(y, int):
                raise ActionError(f"Invalid coordinate types: ({x}, {y})")
            return x, y # Cannot clamp

        # Clamp coordinates to be within screen bounds
        x = max(0, min(x, self.width - 1))
        y = max(0, min(y, self.height - 1))
        return int(x), int(y)

    def _perform_action_with_delay(self, action_func, *args, **kwargs):
        """Executes a pyautogui action and adds a small delay after."""
        action_func(*args, **kwargs)
        time.sleep(ACTION_DELAY_SECS)

    def _execute_mouse_move(self, x: int, y: int) -> ActionResult:
        try:
            clamped_x, clamped_y = self._validate_coordinates(x, y)
            pyautogui.moveTo(clamped_x, clamped_y, duration=0.25) # Add slight duration
            return ActionResult(output=f"Moved mouse to ({clamped_x}, {clamped_y})")
        except Exception as e:
            raise ActionError(f"Failed to move mouse to ({x}, {y}): {e}")

    def _execute_left_click(self, x: Optional[int] = None, y: Optional[int] = None) -> ActionResult:
        target_coords_str = f"at ({x}, {y})" if x is not None and y is not None else "at current position"
        logger.info(f"Attempting left click {target_coords_str}") # Log before attempt
        try:
            if x is not None and y is not None:
                clamped_x, clamped_y = self._validate_coordinates(x, y)
                pyautogui.click(x=clamped_x, y=clamped_y) # Click handles its own delay
            else:
                pyautogui.click()
            # Add a small verification pause and check mouse position (basic sanity check)
            time.sleep(0.1)
            current_x, current_y = pyautogui.position()
            if x is not None and y is not None and (current_x != clamped_x or current_y != clamped_y):
                 logger.warning(f"Mouse position ({current_x}, {current_y}) doesn't match target ({clamped_x}, {clamped_y}) after click.")
                 # Still return success for now, as click might have happened but window focus changed etc.
            return ActionResult(output=f"Performed left click")
        except Exception as e:
            logger.error(f"Exception during left click {target_coords_str}: {e}", exc_info=True) # Log exception info
            raise ActionError(f"Failed left click: {e}")

    def _execute_right_click(self, x: Optional[int] = None, y: Optional[int] = None) -> ActionResult:
        try:
            if x is not None and y is not None:
                clamped_x, clamped_y = self._validate_coordinates(x, y)
                self._perform_action_with_delay(pyautogui.rightClick, x=clamped_x, y=clamped_y)
            else:
                self._perform_action_with_delay(pyautogui.rightClick)
            # TODO: Consider removing fixed wait from original code, let LLM decide if wait needed
            # time.sleep(5) # Original code had a 5s wait for context menu
            return ActionResult(output="Performed right click")
        except Exception as e:
            raise ActionError(f"Failed right click: {e}")

    def _execute_double_click(self, x: Optional[int] = None, y: Optional[int] = None) -> ActionResult:
        try:
            if x is not None and y is not None:
                clamped_x, clamped_y = self._validate_coordinates(x, y)
                self._perform_action_with_delay(pyautogui.doubleClick, x=clamped_x, y=clamped_y)
            else:
                self._perform_action_with_delay(pyautogui.doubleClick)
            return ActionResult(output="Performed double click")
        except Exception as e:
            raise ActionError(f"Failed double click: {e}")

    def _execute_type(self, text: str) -> ActionResult:
        if not isinstance(text, str):
            raise ActionError(f"Invalid text for typing: {text}")
        try:
            # Using clipboard paste for speed and reliability with complex text
            original_clipboard = pyperclip.paste()
            pyperclip.copy(text)
            time.sleep(0.1) # Short delay for clipboard operation

            if platform.system() == 'Darwin': # macOS
                pyautogui.hotkey('command', 'v')
            else: # Windows/Linux
                pyautogui.hotkey('ctrl', 'v')

            time.sleep(0.1)
            # Restore original clipboard content
            pyperclip.copy(original_clipboard)

            # Alternative: pyautogui.write with interval for more human-like typing
            # pyautogui.write(text, interval=TYPING_DELAY_SECS / 10) # interval needs to be smaller
            time.sleep(ACTION_DELAY_SECS)
            # Mask potentially sensitive data in output
            output_text = text if len(text) < 50 else text[:47] + "..."
            return ActionResult(output=f"Typed text: '{output_text}'")
        except Exception as e:
            # Restore clipboard on error too
            pyperclip.copy(original_clipboard)
            raise ActionError(f"Failed to type text: {e}")

    def _execute_key(self, key_sequence: str) -> ActionResult:
        if not isinstance(key_sequence, str):
            raise ActionError(f"Invalid key sequence: {key_sequence}")
        try:
            # Handle multiple keys separated by '+' (for hotkeys) or single keys
            keys_to_press = [k.strip() for k in key_sequence.split('+')]
            mapped_keys = []
            for key in keys_to_press:
                # Map common names to pyautogui names
                mapped_key = PYAUTOGUI_KEY_MAP.get(key, key.lower())
                # Validate against pyautogui's keys if possible (optional)
                # if mapped_key not in pyautogui.KEYBOARD_KEYS:
                #     raise ActionError(f"Unrecognized key: {key} (mapped to {mapped_key})")
                mapped_keys.append(mapped_key)

            if len(mapped_keys) > 1:
                # Press keys down in order, then up in reverse for hotkeys
                pyautogui.hotkey(*mapped_keys)
            elif len(mapped_keys) == 1:
                # Press single key
                pyautogui.press(mapped_keys[0])
            else:
                raise ActionError("No valid keys provided.")

            time.sleep(ACTION_DELAY_SECS)
            return ActionResult(output=f"Pressed key(s): {key_sequence}")
        except Exception as e:
            raise ActionError(f"Failed to press key(s) '{key_sequence}': {e}")

    def _execute_scroll(self, direction: str) -> ActionResult:
        try:
            # Determine scroll amount (adjust as needed)
            scroll_amount = 150 # Number of pixels to scroll
            if direction == "up":
                pyautogui.scroll(scroll_amount)
            elif direction == "down":
                pyautogui.scroll(-scroll_amount)
            else:
                raise ActionError(f"Invalid scroll direction: {direction}")
            time.sleep(ACTION_DELAY_SECS)
            return ActionResult(output=f"Scrolled {direction}")
        except Exception as e:
            raise ActionError(f"Failed to scroll {direction}: {e}")

    def _execute_wait(self, duration_secs: Optional[float] = None) -> ActionResult:
        try:
            wait_time = float(duration_secs if duration_secs is not None else WAIT_DELAY_SECS)
            wait_time = max(0.1, min(wait_time, 30)) # Clamp wait time
            time.sleep(wait_time)
            return ActionResult(output=f"Waited for {wait_time:.1f} seconds")
        except Exception as e:
            raise ActionError(f"Failed to wait: {e}")


    def execute(self, action_name: str, **kwargs) -> ActionResult:
        """Executes the specified action with given arguments."""
        # Map action name (string from LLM) to implementation method
        # We assume action_name matches the Action enum values from llm_interaction.py
        print(f"Executor received action: {action_name} with args: {kwargs}") # Debug

        try:
            if action_name == "left_click":
                coords = kwargs.get('coords')
                x, y = (coords[0], coords[1]) if coords and len(coords) == 2 else (None, None)
                return self._execute_left_click(x, y)
            elif action_name == "right_click":
                coords = kwargs.get('coords')
                x, y = (coords[0], coords[1]) if coords and len(coords) == 2 else (None, None)
                return self._execute_right_click(x, y)
            elif action_name == "double_click":
                coords = kwargs.get('coords')
                x, y = (coords[0], coords[1]) if coords and len(coords) == 2 else (None, None)
                return self._execute_double_click(x, y)
            elif action_name == "mouse_move":
                coords = kwargs.get('coords')
                if not isinstance(coords, (list, tuple)) or len(coords) != 2:
                    raise ActionError(f"Coordinate list/tuple of length 2 required for mouse_move, got: {coords}")
                return self._execute_mouse_move(coords[0], coords[1])
            elif action_name == "type":
                text = kwargs.get('text')
                if text is None:
                    raise ActionError("'text' argument required for type action")
                return self._execute_type(text)
            elif action_name == "key":
                keys = kwargs.get('keys') # TaskProcessor now passes 'keys'
                if keys is None:
                    raise ActionError("'keys' argument required for key action")
                return self._execute_key(keys)
            elif action_name == "scroll": # Consolidated scroll action
                direction = kwargs.get('direction')
                if direction not in ["up", "down"]:
                    raise ActionError(f"Invalid scroll direction: {direction}. Must be 'up' or 'down'.")
                return self._execute_scroll(direction)
            elif action_name == "wait": # Assuming wait action exists
                return self._execute_wait(kwargs.get('duration_secs'))
            elif action_name == "hover": # Hover is often just a mouse move
                coords = kwargs.get('coords')
                if not isinstance(coords, (list, tuple)) or len(coords) != 2:
                     raise ActionError(f"Coordinate list/tuple of length 2 required for hover, got: {coords}")
                # Could add a small sleep after move for hover effect if desired
                result = self._execute_mouse_move(coords[0], coords[1])
                # time.sleep(0.1) # Optional small pause for hover
                return result
            elif action_name == "drag_to": 
                target_coords = kwargs.get('target_coords')
                if not isinstance(target_coords, (list, tuple)) or len(target_coords) != 2:
                    raise ActionError(f"Target coordinate list/tuple of length 2 required for drag_to, got: {target_coords}")
                pyautogui.dragTo(target_coords[0], target_coords[1], duration=0.5)
                time.sleep(ACTION_DELAY_SECS) 
                return ActionResult(output=f"Dragged mouse to ({target_coords[0]}, {target_coords[1]})")
            elif action_name == "None" or action_name is None:
                 return ActionResult(output="No action performed (None).")
            # Add other actions like middle_click, drag etc. if needed
            else:
                raise ActionError(f"Unsupported action: {action_name}")

        except ActionError as e:
            # TODO: Log error
            print(f"Action Error: {e}")
            return ActionResult(error=e.message)
        except Exception as e:
            # TODO: Log unexpected error
            print(f"Unexpected Execution Error: {e}")
            # Provide more context in the error message returned
            return ActionResult(error=f"Unexpected error during action '{action_name}': {e}")