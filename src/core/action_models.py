#!/usr/bin/env python
"""Models related to action execution results."""

import enum
from dataclasses import dataclass, fields, replace
from typing import Optional, List

# --- Define Action Enum --- #
class Action(enum.Enum):
    """Enumeration of possible actions the agent can take."""
    # NONE = "None" # Replaced by explicit DONE action
    LEFT_CLICK = "left_click"
    RIGHT_CLICK = "right_click"
    DOUBLE_CLICK = "double_click"
    TYPE = "type"
    KEY = "key" # For pressing special keys or combinations
    SCROLL = "scroll"
    MOUSE_MOVE = "mouse_move"
    HOVER = "hover"
    DRAG_TO = "drag_to" # Added missing drag action
    WAIT = "wait" # Explicitly wait for a short duration
    REANALYZE = "reanalyze" # Explicitly request a new screen analysis
    TASK_COMPLETE = "task_complete" # Signal that the current task step is finished
    DONE = "done" # Signal that the entire user request is fulfilled
    CHANGE_TASK = "change_task" # NEW: Signal that the current task cannot be completed and should be skipped
    # Add other actions as needed

    @classmethod
    def get_action_descriptions(cls) -> str:
        """Returns a string describing available actions for the LLM prompt."""
        # Customize descriptions as needed
        descriptions = {
            # cls.NONE: "Use ONLY when the entire user request is fully completed or if you are absolutely stuck.",
            cls.LEFT_CLICK: "Perform a left mouse click at the specified element or coordinates.",
            cls.RIGHT_CLICK: "Perform a right mouse click at the specified element or coordinates.",
            cls.DOUBLE_CLICK: "Perform a double left mouse click at the specified element or coordinates.",
            cls.TYPE: "Type the specified text using the keyboard.",
            cls.KEY: "Press a special key or key combination (e.g., 'enter', 'ctrl+c').",
            cls.SCROLL: "Scroll the mouse wheel ('up' or 'down').",
            cls.MOUSE_MOVE: "Move the mouse cursor to the specified element or coordinates without clicking.",
            cls.HOVER: "Move the mouse cursor to the specified element or coordinates and briefly pause (hover).",
            cls.DRAG_TO: "Drag the mouse from its current position to the specified element or coordinates.", # Added description
            cls.WAIT: "Wait for a short period (e.g., 1-2 seconds) to allow the UI to update or load before the next action.",
            cls.REANALYZE: "Take a new screenshot and analyze the screen again. Use this after 'wait' if unsure the UI is ready, or if a previous action failed.",
            cls.TASK_COMPLETE: "Call this tool ONLY when the single, current task step provided to you is finished, and you are ready for the next task.",
            cls.DONE: "Call this tool ONLY when the ENTIRE multi-step user request is fully completed (which might be before or after the task list is empty).",
            cls.CHANGE_TASK: "Call this tool ONLY if the current task seems impossible, incorrect, or stuck in a loop. Provide reasoning why it should be skipped." # NEW description
        }
        return ", ".join([f"{action.value}: {descriptions.get(action, 'No description.')}" for action in cls])

    @classmethod
    def get_action_names(cls) -> List[str]:
        """Returns a list of valid action names."""
        return [action.value for action in cls]

# --- ActionResult and ActionError --- #
@dataclass(kw_only=True, frozen=True)
class ActionResult:
    """Represents the result of an action execution."""

    output: Optional[str] = None
    error: Optional[str] = None
    success: bool = True # Added success flag
    # base64_image: Optional[str] = None # Keep if image feedback is needed
    # system: Optional[str] = None      # Keep if system messages are generated

    def __post_init__(self):
        # Automatically set success to False if there's an error
        if self.error:
            # Bypass frozen=True using object.__setattr__
            object.__setattr__(self, 'success', False)

    def __bool__(self):
        """Return True if the action was successful."""
        return self.success

    def __add__(self, other: "ActionResult") -> "ActionResult":
        """
        Combine two action results. Errors take precedence.
        Outputs are concatenated if both exist.
        The overall success is False if either result failed.
        Other fields (image, system) are taken from `other` if they exist, otherwise from `self`.
        """
        if not isinstance(other, ActionResult):
            return NotImplemented

        combined_error = self.error or other.error # Prioritize errors
        combined_success = self.success and other.success
        combined_output = None

        if self.output and other.output:
            combined_output = self.output + "\n" + other.output
        else:
            combined_output = self.output or other.output

        # Construct the new result, success will be auto-updated if error exists
        new_result = ActionResult(
            output=combined_output,
            error=combined_error,
            # base64_image=other.base64_image or self.base64_image,
            # system=other.system or self.system,
        )
        # Ensure the combined success state is reflected if no error was present initially
        if not new_result.error:
             object.__setattr__(new_result, 'success', combined_success)

        return new_result

    def replace(self, **kwargs) -> "ActionResult":
        """Returns a new ActionResult with the given fields replaced."""
        # Ensure success is handled correctly if error is added/removed
        new_instance = replace(self, **kwargs)
        # Re-trigger post_init logic (or replicate it)
        if new_instance.error and new_instance.success:
            object.__setattr__(new_instance, 'success', False)
        elif not new_instance.error and not new_instance.success and 'success' not in kwargs:
             # If error removed and success wasn't explicitly set to False, assume success
             # This logic might need refinement based on desired behavior
             object.__setattr__(new_instance, 'success', True)
        return new_instance

class ActionError(Exception):
    """Raised when an action encounters an error during execution."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message) 