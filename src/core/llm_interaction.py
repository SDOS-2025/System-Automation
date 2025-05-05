#!/usr/bin/env python
"""Handles interaction with the Language Model (OpenAI) using Tool Calling."""

import base64
import json
from typing import List, Dict, Any, Optional, Tuple
import os # Import os for environment variable access example
import logging # Import logging library
from pathlib import Path
import argparse # For command-line arguments
import threading # For running orchestrator in background thread for GUI

from openai import OpenAI

# Core models/enums
from .action_models import Action, ActionResult
from .llm_models import TaskPlanResponse # Planning still uses JSON mode for simplicity

# Utilities
from ..utils.config_loader import get_config_value
from ..utils.logging_setup import get_logger, setup_logging
# Remove imports causing circular dependency
# from ..utils.download_models import download_model_weights
# from ..utils.system_info import get_system_info, DEFAULT_CACHE_DIR
# from ..core.task_processor import TaskProcessor # <--- REMOVED THIS

# Initialize logger for this module first
# We need to call setup_logging early, potentially before loading full config
# TODO: Refine logging setup based on config if needed (e.g., log level)
log_level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_str, logging.INFO)
# TODO: Get log file path from config or use default
setup_logging(log_level=log_level) # <-- CALL HERE
logger = get_logger(__name__) # Main logger for this module
llm_history_logger = get_logger("llm_history") # Dedicated logger for LLM history

# --- Tool Definitions for OpenAI --- #

def get_tools_schema() -> List[Dict[str, Any]]:
    """Generates the list of tool schemas for the OpenAI API call."""
    tools = [
        {
            "type": "function",
            "function": {
                "name": Action.LEFT_CLICK.value,
                "description": "Perform a left mouse click, targeting either an element ID or specific coordinates.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "box_id": {
                            "type": "integer",
                            "description": "The element ID to click. Use -1 if providing explicit coordinates."
                        },
                        "coordinates": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "The explicit [x, y] coordinates to click. Use ONLY if box_id is -1."
                        },
                        "reasoning": {
                            "type": "string",
                             "description": "Your thought process for performing this click action."
                        }
                    },
                    "required": ["box_id", "reasoning"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": Action.RIGHT_CLICK.value,
                "description": "Perform a right mouse click, targeting either an element ID or specific coordinates.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "box_id": {
                            "type": "integer",
                            "description": "The element ID to click. Use -1 if providing explicit coordinates."
                        },
                        "coordinates": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "The explicit [x, y] coordinates to click. Use ONLY if box_id is -1."
                        },
                        "reasoning": {
                            "type": "string",
                             "description": "Your thought process for performing this click action."
                        }
                    },
                    "required": ["box_id", "reasoning"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": Action.DOUBLE_CLICK.value,
                "description": "Perform a double left click, targeting either an element ID or specific coordinates.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "box_id": {
                            "type": "integer",
                            "description": "The element ID to double-click. Use -1 if providing explicit coordinates."
                        },
                        "coordinates": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "The explicit [x, y] coordinates to double-click. Use ONLY if box_id is -1."
                        },
                        "reasoning": {
                            "type": "string",
                             "description": "Your thought process for performing this double-click action."
                        }
                    },
                    "required": ["box_id", "reasoning"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": Action.TYPE.value,
                "description": "Type the specified text using the keyboard. Ensure the correct input field was clicked previously.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "value": {
                            "type": "string",
                            "description": "The text to type."
                        },
                        "reasoning": {
                            "type": "string",
                             "description": "Your thought process for typing this text."
                        }
                    },
                    "required": ["value", "reasoning"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": Action.KEY.value,
                "description": "Press a special key or key combination (e.g., 'enter', 'ctrl+c').",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keys": {
                            "type": "string",
                            "description": "The key or key combination to press (e.g., 'enter', 'ctrl+a')."
                        },
                        "reasoning": {
                            "type": "string",
                             "description": "Your thought process for pressing these keys."
                        }
                    },
                    "required": ["keys", "reasoning"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": Action.SCROLL.value,
                "description": "Scroll the mouse wheel up or down.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "direction": {
                            "type": "string",
                            "enum": ["up", "down"],
                            "description": "The direction to scroll."
                        },
                        "reasoning": {
                            "type": "string",
                             "description": "Your thought process for scrolling."
                        }
                    },
                    "required": ["direction", "reasoning"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": Action.MOUSE_MOVE.value,
                "description": "Move the mouse cursor to the specified element or coordinates without clicking.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "box_id": {
                            "type": "integer",
                            "description": "The element ID to move to. Use -1 if providing explicit coordinates."
                        },
                        "coordinates": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "The explicit [x, y] coordinates to move to. Use ONLY if box_id is -1."
                        },
                        "reasoning": {
                            "type": "string",
                             "description": "Your thought process for moving the mouse."
                        }
                    },
                    "required": ["box_id", "reasoning"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": Action.HOVER.value,
                "description": "Move the mouse cursor to the specified element or coordinates and briefly pause (hover). Essentially a mouse_move.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "box_id": {
                            "type": "integer",
                            "description": "The element ID to hover over. Use -1 if providing explicit coordinates."
                        },
                        "coordinates": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "The explicit [x, y] coordinates to hover over. Use ONLY if box_id is -1."
                        },
                        "reasoning": {
                            "type": "string",
                             "description": "Your thought process for hovering."
                        }
                    },
                    "required": ["box_id", "reasoning"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": Action.WAIT.value,
                "description": "Wait for a short period (e.g., 1-2 seconds) to allow the UI to update or load.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "duration_secs": {
                            "type": "number",
                            "description": "Optional duration in seconds to wait (default is ~1s)."
                        },
                         "reasoning": {
                            "type": "string",
                             "description": "Your thought process for waiting."
                        }
                    },
                    "required": ["reasoning"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": Action.REANALYZE.value,
                "description": "Request a fresh analysis of the screen state without performing any other action.",
                "parameters": {
                    "type": "object",
                    "properties": {
                         "reasoning": {
                            "type": "string",
                             "description": "Explain why a re-analysis of the screen is needed at this point."
                        }
                    },
                    "required": ["reasoning"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": Action.TASK_COMPLETE.value,
                "description": "Signal that the current task step is finished.",
                "parameters": {
                    "type": "object",
                    "properties": {
                         "reasoning": {
                            "type": "string",
                             "description": "Briefly state why the current task step is considered complete."
                        }
                    },
                    "required": ["reasoning"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": Action.DONE.value,
                "description": "Signal that the entire sequence of tasks is complete.",
                "parameters": {
                    "type": "object",
                    "properties": {
                         "reasoning": {
                            "type": "string",
                             "description": "Briefly state why the task sequence is considered complete."
                        }
                    },
                    "required": ["reasoning"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": Action.DRAG_TO.value,
                "description": "Drag the mouse from its current position to the specified element or coordinates.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "box_id": {
                            "type": "integer",
                            "description": "The element ID to drag the mouse *to*. Use -1 if providing explicit coordinates."
                        },
                        "coordinates": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "The explicit [x, y] coordinates to drag the mouse *to*. Use ONLY if box_id is -1."
                        },
                        "reasoning": {
                            "type": "string",
                             "description": "Your thought process for performing this drag action."
                        }
                    },
                    "required": ["box_id", "reasoning"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": Action.CHANGE_TASK.value,
                "description": "Signal that the current task cannot be completed or is stuck, and should be skipped.",
                "parameters": {
                    "type": "object",
                    "properties": {
                         "reasoning": {
                            "type": "string",
                             "description": "Explain why the current task needs to be skipped (e.g., element not found, action failed repeatedly, task irrelevant)."
                        }
                    },
                    "required": ["reasoning"]
                }
            }
        },
    ]
    return tools

class LLMInteraction:
    """Manages calls to the OpenAI API for planning and action generation."""

    def __init__(self, config: Dict[str, Any]):
        self.api_key = get_config_value("openai.api_key")
        if not self.api_key:
            raise ValueError("OpenAI API key not found in configuration.")

        self.model = get_config_value("openai.model", "gpt-4.1-mini")
        self.base_url = get_config_value("openai.base_url", "https://api.openai.com/v1")
        
        # Initialize OpenAI client with base_url if it's set
        client_kwargs = {
            "api_key": self.api_key,
            "base_url": self.base_url
        }
        
        # Add default headers for OpenRouter if using their API
        if "openrouter.ai" in self.base_url:
            client_kwargs["default_headers"] = {
                "HTTP-Referer": "https://github.com/SDOS-2025/System-Automation",  # Required for OpenRouter
                "X-Title": "System-Automation"  # Optional, helps OpenRouter identify your app
            }
            
        self.client = OpenAI(**client_kwargs)
        
        self.tools = get_tools_schema() # Store tool schema
        logger.info(f"OpenAI client initialized with model: {self.model}, using API endpoint: {self.base_url}")

    def _create_system_prompt(self, system_info: dict) -> str:
        """Creates the system prompt instructing the agent to use tools."""
        # Format system info for the prompt
        os_info = system_info.get("os_info", {})
        super_key_info = system_info.get("super_key", {})
        apps_info = system_info.get("installed_apps", {})
        
        sys_info_text = (
            f"System Environment:\n"
            f"- OS: {os_info.get('system', 'N/A')} {os_info.get('release', '')}\n"
            f"- Architecture: {os_info.get('architecture', 'N/A')}\n"
            f"- Super/Win Key: {super_key_info.get('key_name', 'N/A')} (Assumed Working: {super_key_info.get('works', 'N/A')})\n"
            # Optionally include truncated app list if needed later
        )

        # Updated prompt to allow multiple tool calls
        return f"""
You are an expert computer assistant agent.
Your goal is to complete the CURRENT TASK requested by the user by executing actions using the available tools.

{sys_info_text}

YOU WILL BE GIVEN:
1. The user's original request (for overall context).
2. The single `current_task` description you should focus on right now.
3. The current state of the screen summarized as:
   - The `Available Element IDs` range (e.g., "0-30" or "None").
4. A history of previous actions/tool calls taken and their results (`message_history`).
5. An image of the current screen with element IDs drawn near their centers.

Based on the `current_task`, screen image, available IDs, and history, decide the **sequence of tool calls** needed to progress the `current_task`.

**CRITICAL INSTRUCTIONS:**
- **Base decisions PRIMARILY on the provided screenshot.** Use `message_history` only for context about past actions, not to assume the current state still holds. The user might have interacted with the computer.
- **Focus ONLY on the `current_task`.** Base your action sequence *only* on fulfilling the exact `current_task` description. Do not add steps from previous or future tasks unless absolutely necessary for the current one.
- **Explain your choices.** Provide clear reasoning in the `reasoning` parameter for *each* tool call.
- **You can make MULTIPLE tool calls in a single turn IF you are highly confident they can be executed consecutively without needing to see the screen state in between.** 
  - **Good Examples:** Clicking an input field then immediately typing; clicking, typing, then pressing Enter in a search field; pressing a sequence of hotkeys.
  - **Bad Examples (Use separate turns):** Clicking a button that opens a new window/dialog; scrolling then clicking; clicking a menu item that triggers a load.
- **If uncertain, make only ONE tool call.**
- **AVOID REPETITION:** Check the recent `message_history`. Do not repeat actions that have already been successfully completed in the last few steps. For example, if you just successfully typed text, do not type it again in the next step unless the task explicitly requires it.
- **TASK COMPLETION:** `{Action.TASK_COMPLETE.value}` marks the current task step finished. Use as the final call in a sequence if applicable.
- **OVERALL COMPLETION:** `{Action.DONE.value}` marks the overall user goal met. Use as the final call in a sequence if applicable.
- **SKIPPING TASKS:** If the `current_task` seems impossible (e.g., element not found after re-analysis), incorrect given the screen, or if you are stuck in a loop after trying different approaches (especially repetitive failures), call the `{Action.CHANGE_TASK.value}` tool. This will skip the current task.
- **HANDLE LOGINS:** If you encounter a login screen or password prompt, do not attempt to enter credentials. Call `{Action.CHANGE_TASK.value}` or `{Action.DONE.value}` and state that manual login is required.
- **USE ONLY TOOL CALLS:** You MUST communicate actions *exclusively* through the provided tool call interface. Do NOT describe actions or embed tool call structures within your text response.

TOOL EXECUTION NOTES:
- Analyze Screen & History: Consider visuals AND `message_history`.
- **Opening Apps:** To open an application, the standard method is: 1. Press the `{system_info.get('super_key', {}).get('key_name', 'Super/Win')}` key. 2. `type` the application name. 3. `wait` briefly for search results. 4. Press the `enter` key using the `key` tool.
- Waiting & Re-analyzing: Use `{Action.WAIT.value}` usually as a *single* tool call, especially after actions that load new content or open apps. If needed, follow `wait` with `{Action.REANALYZE.value}` in the *next* turn if you need to confirm the UI state before proceeding.
- Element Interaction (Mouse): Use `box_id` for mouse actions (`left_click`, etc.) only when necessary and keyboard shortcuts are unavailable. Base the `box_id` on the current screenshot.
- Coordinates (Mouse): Use explicit coordinates *only* if a suitable `box_id` is -1.
- **Focus Before Typing:** Before using the `{Action.TYPE.value}` tool, make sure the correct input field has focus. This might require a preceding `{Action.LEFT_CLICK.value}` or keyboard navigation (`key` tool with 'tab' or arrows).
- **Keys:** Use `{Action.KEY.value}` for single key presses (like 'enter') or combinations ('ctrl+c').
- Task Completion: `{Action.TASK_COMPLETE.value}` marks the current task step finished. Use as the final call in a sequence if applicable.
- Overall Completion: `{Action.DONE.value}` marks the overall user goal met. Use as the final call in a sequence if applicable.
- Change Task: `{Action.CHANGE_TASK.value}` skips the current problematic task.
- **Keyboard First (CRITICAL PREFERENCE):** **YOU MUST STRONGLY prefer** using keyboard actions (`key` tool for shortcuts like 'ctrl+k', 'tab', 'enter', arrow keys, or the Super+Type+Enter method for opening apps) over mouse clicks (`left_click`). **Even if a clickable element is visible on the screen**, if a reliable keyboard shortcut or the standard app opening procedure exists for the desired action, **USE THE KEYBOARD METHOD**. Mouse clicks based on `box_id` are less reliable due to potential UI changes and should be a fallback option. Examples:
  - **Instead of:** `left_click` on a search icon (box_id: 15).
  - **Prefer:** `key` with `keys: 'ctrl+k'` (if that's the app's search shortcut).
  - **Instead of:** `left_click` on an OK button (box_id: 45).
  - **Prefer:** `key` with `keys: 'enter'` (if Enter confirms the dialog).
  - **Instead of:** `left_click` on the next input field (box_id: 60).
  - **Prefer:** `key` with `keys: 'tab'`.
  - **Instead of:** `left_click` on a Play button (box_id: 70).
  - **Prefer:** `key` with `keys: 'space'` (if Space toggles play/pause).
  - **Instead of:** `left_click` on a New Tab button (box_id: 80).
  - **Prefer:** `key` with `keys: 'ctrl+t'` (if Ctrl+T opens a new tab).
- **Leverage Known Shortcuts:** Beyond these examples, if you know keyboard shortcut for an action within the current application (e.g., saving, opening menus, navigating), prefer using the `key` tool with that shortcut over mouse interaction.

**EXAMPLE (Multiple Calls):**
1. User wants: "Open Spotify, search Artist Name, click first result"
2. Current Task: "Type 'Artist Name'"
3. (Screen shows search input field 25).
4. Call Sequence: [`left_click` tool (box_id: 25), `type` tool (value: 'Artist Name'), `task_complete` tool (reasoning: Finished typing 'Artist Name')]
5. >> System executes click, then type, then recognizes task complete <<

**EXAMPLE (Single Call):**
1. User wants: "Scroll down to find the 'Submit' button"
2. Current Task: "Scroll down"
3. Call Sequence: [`scroll` tool (direction: 'down')]
4. >> System executes scroll, then re-analyzes screen in the next step <<

REMEMBER: Actions are ONLY communicated via Tool Calls.
"""

    def _create_planning_system_prompt(self, system_info: dict) -> str:
        """Creates the system prompt for the planning phase (still uses JSON mode)."""
        # Format system info (same as in _create_system_prompt)
        os_info = system_info.get("os_info", {})
        super_key_info = system_info.get("super_key", {})
        apps_info = system_info.get("installed_apps", {})
        app_count = len(apps_info.get("apps", []))
        
        sys_info_text = (
            f"System Environment:\n"
            f"- OS: {os_info.get('system', 'N/A')} {os_info.get('release', '')}\n"
            f"- Architecture: {os_info.get('architecture', 'N/A')}\n"
            f"- Super/Win Key: {super_key_info.get('key_name', 'N/A')} (Assumed Working: {super_key_info.get('works', 'N/A')})\n"
            f"- Detected GUI Applications: {app_count}"
        )
        
        return f"""
You are an expert planning agent.
Your goal is to break down a user's high-level request into a **complete sequence of concise, actionable tasks** required to fulfill the *entire* request using a computer GUI.

{sys_info_text}

YOU WILL BE GIVEN:
1. The user's overall requirement.
2. The current state of the screen summarized as:
   - The `Available Element IDs` range (e.g., "0-30" or "None").
3. An image of the current screen with element IDs drawn near their centers (use this visual to understand the layout and element functions *at the start*).

**OUTPUT FORMAT:**
Please provide your response ONLY in the following JSON format:
```json
{{
  "reasoning": "<Your thought process for creating the complete task list. Think step-by-step from the beginning to the end of the user's request. Anticipate how the screen might change.>",
  "task_list": [
    "<First concrete action/step, e.g., 'Click the file menu'>",
    "<Second action/step, e.g., 'Click the Save As option'>",
    "<Third action/step, e.g., 'Type the filename into the input field'>",
    ...
    "<Final action/step required to complete the request>"
  ]
}}
```

**IMPORTANT PLANNING NOTES:**
- **Completeness is Key:** The `task_list` MUST contain ALL the necessary steps to get from the current state to the final goal of the user's request.
- **Think Ahead:** Anticipate the intermediate steps required. For example, if the user asks to search for something, the plan needs steps like 'Click search icon', 'Type search query', 'Wait for results', 'Click result'. Don't just plan the very first click.
- **Concise Actions:** Keep each task description brief and focused on a single logical action (click, type, wait, scroll, etc.).
- **Refer Functionally:** Refer to elements by their function or appearance (e.g., "Click the search icon", "Type in the main text field"); the execution agent will handle finding the correct element ID later using the screenshot at that step.
- **Logical Flow:** Ensure the tasks logically progress towards fulfilling the user requirement.
- **Stick to JSON:** Adhere strictly to the JSON format.

**PLANNING EXAMPLE:**
User Request: "Open the text editor, type 'Hello World', and save it as hello.txt on the desktop."
Initial Screen: Shows a standard desktop with a text editor icon (id 15).

Output:
```json
{{
  "reasoning": "The user wants to create and save a text file. First, I need to open the editor by clicking its icon. Then, I need to type the specified text. Finally, I need to initiate the save process (likely via a menu), type the filename, and confirm the save, potentially navigating to the desktop if needed (assuming default save location isn't desktop).",
  "task_list": [
    "Click the text editor icon (id 15)",
    "Wait for the editor window to open",
    "Type 'Hello World' into the editor window",
    "Click the 'File' menu",
    "Click the 'Save As...' option",
    "Wait for the save dialog to appear",
    "Type 'hello.txt' into the filename input field",
    "Navigate to the Desktop location (if necessary)",
    "Click the 'Save' button"
  ]
}}
```
"""

    def get_task_plan(self, user_requirement: str, screen_analysis: Dict[str, Any], base64_image: str, system_info: dict) -> TaskPlanResponse:
        """Calls the LLM to generate a task plan based on the user requirement and screen."""
        system_prompt = self._create_planning_system_prompt(system_info)

        # --- Prepare screen analysis data FOR LLM PROMPT (ID range only) ---
        available_element_ids = sorted([elem.get("element_id", -1) for elem in screen_analysis.get("elements", []) if elem.get("element_id", -1) != -1])
        element_count = len(available_element_ids)
        if element_count > 0:
            id_range_str = f"{available_element_ids[0]}-{available_element_ids[-1]}"
        else:
            id_range_str = "None"
        screen_analysis_str = f"Available Element IDs: {id_range_str}"

        # Log the data being sent (Count and Range)
        logger.info(f"Screen Analysis (Planning): {element_count} elements detected (IDs: {id_range_str}).")

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"User Requirement: {user_requirement}\n\nCurrent Screen Analysis:\n{screen_analysis_str}\nPlease generate the task list."},
                    {
                "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}",
                            "detail": "high"
                        }
                    }
                ]
            }
        ]

        # --- Log Request to History File --- #
        try:
            llm_history_logger.info(f"--- Planning Request --->\n{json.dumps(messages, indent=2)}")
        except Exception as log_e:
             logger.warning(f"Failed to log planning request to history file: {log_e}")

        response_content = "" # Initialize for error logging
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1000,
                temperature=0.2,
                response_format={"type": "json_object"} # Keep JSON mode for planning
            )
            response_content = response.choices[0].message.content
            logger.debug(f"LLM Planning Raw Response Content: {response_content}") # Keep debug log for main file

            # --- Log Response to History File --- #
            try:
                 llm_history_logger.info(f"--- Planning Response <---\n{response_content}") # Log raw content
            except Exception as log_e:
                 logger.warning(f"Failed to log planning response to history file: {log_e}")

            parsed_json = json.loads(response_content)
            plan_response = TaskPlanResponse(**parsed_json)
            return plan_response

        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode LLM JSON response for planning: {response_content}. Error: {e}")
            return TaskPlanResponse(reasoning=f"Error: LLM response was not valid JSON. Content: {response_content}", task_list=[])
        except Exception as e:
            logger.error(f"Unexpected error calling OpenAI API for planning: {e}", exc_info=True)
            return TaskPlanResponse(reasoning=f"Error: API call failed - {e}", task_list=[])

    def get_next_action(self,
                        message_history: List[Dict[str, Any]],
                        current_task: str,
                        screen_analysis: Dict[str, Any],
                        base64_image: str,
                        system_info: dict) -> List[Tuple[Action, Optional[dict], Optional[str]]]: # Return type changed to List
        """Calls the LLM to determine the next sequence of actions for the CURRENT task using Tool Calling."""
        system_prompt = self._create_system_prompt(system_info)

        # --- Prepare screen analysis data FOR LLM PROMPT (ID range only) ---
        available_element_ids = sorted([elem.get("element_id", -1) for elem in screen_analysis.get("elements", []) if elem.get("element_id", -1) != -1])
        element_count = len(available_element_ids)
        if element_count > 0:
            id_range_str = f"{available_element_ids[0]}-{available_element_ids[-1]}"
        else:
            id_range_str = "None"
        screen_analysis_str = f"Available Element IDs: {id_range_str}"

        # Log the data being sent (Count and Range)
        logger.info(f"Screen Analysis (Action): {element_count} elements detected (IDs: {id_range_str}).")

        # Add CURRENT TASK info to prompt text
        current_state_text = (
            f"Current Task: {current_task}\n" +
            "\n\nCurrent Screen Analysis:\n" +
            f"{screen_analysis_str}\n" +
            "\nBased on the history and current screen, what is the tool call sequence to make to progress the Current Task?"
            " (Call task_complete as the last action if it is finished, or done if the overall goal is met)"
        )

        # Ensure message history doesn't grow indefinitely (optional, good practice)
        MAX_HISTORY_MESSAGES = 15 # Example limit
        if len(message_history) > MAX_HISTORY_MESSAGES:
             logger.warning(f"Message history exceeds {MAX_HISTORY_MESSAGES}. Truncating.")
             # Preserve system prompt (index 0) and initial plan (likely index 1/assistant)
             preserved_messages = []
             num_to_preserve_at_start = 0
             if len(message_history) > 0 and message_history[0].get('role') == 'system':
                  preserved_messages.append(message_history[0])
                  num_to_preserve_at_start += 1
             if len(message_history) > 1 and message_history[1].get('role') == 'assistant':
                  # Assuming the first assistant message is the plan
                  preserved_messages.append(message_history[1]) 
                  num_to_preserve_at_start += 1
             
             # Calculate how many messages to take from the end
             num_from_end = MAX_HISTORY_MESSAGES - num_to_preserve_at_start
             if num_from_end < 0: # Should not happen if MAX_HISTORY > 2, but safety check
                  num_from_end = 0 
                  
             # Combine preserved start messages and tail messages
             messages_from_end = message_history[-num_from_end:] if num_from_end > 0 else []
             
             # Avoid duplicating messages if the preserved ones overlap with the tail
             final_truncated_history = []
             preserved_ids = {id(msg) for msg in preserved_messages}
             final_truncated_history.extend(preserved_messages)
             for msg in messages_from_end:
                  if id(msg) not in preserved_ids:
                       final_truncated_history.append(msg)
                       
             # Ensure we don't exceed max length due to edge cases/short histories
             if len(final_truncated_history) > MAX_HISTORY_MESSAGES:
                 final_truncated_history = final_truncated_history[-MAX_HISTORY_MESSAGES:]

             message_history = final_truncated_history # Update the main history list


        messages = list(message_history) # Create a mutable copy
        messages.append(
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": current_state_text},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}",
                            "detail": "high" # Use high detail for action phase
                        }
                    }
                ]
            }
        )
        
        # Add system prompt if not already in history (or update it)
        system_message_found = False
        for i, msg in enumerate(messages):
             if msg['role'] == 'system':
                  messages[i]['content'] = system_prompt # Ensure latest prompt is used
                  system_message_found = True
                  break
        if not system_message_found:
             messages.insert(0, {"role": "system", "content": system_prompt})


        # --- Log Request to History File --- #
        try:
            # Exclude image data from file log for brevity
            loggable_messages = []
            for msg in messages:
                 if isinstance(msg['content'], list):
                      text_content = [item['text'] for item in msg['content'] if item['type'] == 'text']
                      loggable_messages.append({**msg, 'content': ' '.join(text_content) + " (+ image)"})
                 else:
                      loggable_messages.append(msg)
            llm_history_logger.info(f"--- Action Request --->\n{json.dumps(loggable_messages, indent=2)}")
        except Exception as log_e:
             logger.warning(f"Failed to log action request to history file: {log_e}")


        action_sequence: List[Tuple[Action, Optional[dict], Optional[str]]] = [] # Initialize return list
        response_content = None # For logging/error reporting

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto", # Let the model decide whether to use tools
                max_tokens=1000, # Adjust as needed
                temperature=0.1 # Lower temperature for more deterministic actions
            )

            response_message = response.choices[0].message
            response_content = response_message.content # Text part, might be None if only tool calls
            tool_calls = response_message.tool_calls # List of tool calls

            # --- Log Response to History File --- #
            try:
                 log_data = {
                      "response_text": response_content,
                      "tool_calls": [
                            {"id": call.id, "function": {"name": call.function.name, "arguments": call.function.arguments}}
                            for call in tool_calls
                      ] if tool_calls else None
                 }
                 llm_history_logger.info(f"--- Action Response <---\n{json.dumps(log_data, indent=2)}")
            except Exception as log_e:
                 logger.warning(f"Failed to log action response to history file: {log_e}")


            # --- Process Extracted Tool Calls (if any) --- #
            if tool_calls:
                 # Process the list of tool calls
                 for tool_call in tool_calls:
                      tool_name = tool_call.function.name
                      try:
                           action_enum = Action(tool_name) # Convert string name to Action enum
                      except ValueError:
                           logger.warning(f"LLM called unknown tool: {tool_name}. Skipping this call.")
                           continue # Skip this specific tool call

                      try:
                           args_dict = json.loads(tool_call.function.arguments)
                      except json.JSONDecodeError:
                           logger.warning(f"Failed to parse arguments for tool {tool_name}: {tool_call.function.arguments}. Proceeding without arguments.")
                           args_dict = {}

                      reasoning = args_dict.pop("reasoning", None) # Extract reasoning if present in args
                      
                      # Add the parsed action to the sequence
                      action_sequence.append((action_enum, args_dict, reasoning))
                      
                      # If REANALYZE is called, stop processing further calls in this sequence
                      if action_enum == Action.REANALYZE:
                           logger.info("REANALYZE tool called. Stopping processing of subsequent tool calls in this turn.")
                           break 
             
            else:
                # No tool calls made. Maybe LLM just responded with text?
                logger.info(f"LLM did not make any tool calls. Response text: {response_content}")
                # We could potentially treat this as a "wait and reanalyze" situation or signal an error/no action.
                # For now, return an empty sequence, TaskProcessor will handle re-looping.
                pass # Return empty list

            return action_sequence

        except Exception as e:
            logger.error(f"Error calling OpenAI API for action generation: {e}", exc_info=True)
            logger.error(f"LLM response content at time of error (if available): {response_content}")
            # Return empty list on error, task processor will likely retry or stop
            return []
