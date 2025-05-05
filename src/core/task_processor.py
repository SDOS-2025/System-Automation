#!/usr/bin/env python
"""Processes tasks by interacting with LLM, screen analysis, and action execution."""

import time
import json
import base64
from io import BytesIO
from typing import List, Dict, Any, Optional, Tuple
import os
import datetime

from PIL import Image # Import Image

# Core components (adjust imports based on final structure)
from .screen_analysis import ScreenAnalyzer, UIElement # Assuming get_screenshot logic is in ScreenAnalyzer
from .llm_interaction import LLMInteraction, Action, TaskPlanResponse
from .action_executor import ActionExecutor
from .action_models import ActionResult

# Utilities (adjust imports)
from ..utils.logging_setup import get_logger # Setup logging later
from ..utils.drawing import draw_elements # If drawing needed

logger = get_logger(__name__)

# Define path for debug screenshots relative to project root or this file
DEBUG_IMAGE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "debug_screenshots")

class TaskProcessor:
    """Orchestrates the planning and execution of automation tasks."""

    def __init__(self, config: Dict[str, Any], system_info: dict):
        """Initializes the TaskProcessor with necessary components and system info."""
        self.config = config
        self.system_info = system_info # Store system info
        self.llm_interaction = LLMInteraction(config)
        # Get model path from nested config structure
        # Ensure nested keys exist before accessing
        screen_analysis_config = config.get("screen_analysis", {})
        yolo_model_path = screen_analysis_config.get("yolo_model_path")
        if not yolo_model_path:
             # Fallback or raise error if path is crucial
             logger.warning("YOLO model path not found in config [screen_analysis.yolo_model_path]. Using default/placeholder.")
             # yolo_model_path = "path/to/default/model.pt" # Or raise ValueError
             raise ValueError("Missing required configuration: screen_analysis.yolo_model_path")

        self.screen_analyzer = ScreenAnalyzer(yolo_model_path=yolo_model_path)
        self.action_executor = ActionExecutor()
        self.message_history: List[Dict[str, Any]] = []
        self.task_list: List[str] = []
        self.should_stop = False

        # Ensure debug directory exists
        os.makedirs(DEBUG_IMAGE_DIR, exist_ok=True)
        logger.info(f"Debug screenshot directory ensured at: {os.path.abspath(DEBUG_IMAGE_DIR)}")

    def _get_current_screen_analysis(self, screen_region: Optional[Tuple[int, int, int, int]] = None) -> Tuple[Dict[str, Any], str]:
        """Captures screen, performs analysis, returns results + base64 image, and saves debug image."""
        screenshot_path = None
        try:
            # Capture screen to a temporary file path
            screenshot_path = self.screen_analyzer.capture_screen()
            logger.debug(f"Screenshot saved to temporary path: {screenshot_path}")

            # Analyze the image from the path - gets elements sorted (y,x), containing bbox coords
            elements: List[UIElement] = self.screen_analyzer.analyze_image_from_path(screenshot_path)
            logger.debug(f"Screen analysis found {len(elements)} elements (sorted by y,x).")

            # Prepare analysis results dictionary (containing full bbox coordinates for internal use)
            analysis_result = {
                "elements": [elem.model_dump() for elem in elements],
                "width": 0, # Will be updated below
                "height": 0,
            }

            # Open image, get dimensions, DRAW ANNOTATIONS, encode ANNOTATED image, save debug image
            with Image.open(screenshot_path) as img:
                width, height = img.size
                # Update width/height in the dict
                analysis_result["width"] = width
                analysis_result["height"] = height

                # --- Draw elements onto a copy FIRST --- 
                annotated_image = img.copy()
                try:
                    annotated_image = draw_elements(annotated_image, elements)
                    logger.debug("Drew elements onto image copy.")
                     # Save the annotated image for debugging
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    debug_filename = f"analysis_{timestamp}.png"
                    debug_filepath = os.path.join(DEBUG_IMAGE_DIR, debug_filename)
                    annotated_image.save(debug_filepath)
                    logger.info(f"Saved annotated debug screenshot to: {debug_filepath}")
                except Exception as draw_err:
                    logger.error(f"Failed to draw elements or save debug image: {draw_err}", exc_info=True)
                    # If drawing fails, send the original image instead
                    annotated_image = img # Fallback to original

                # --- Encode the ANNOTATED image for the LLM --- 
                buffered = BytesIO()
                annotated_image.save(buffered, format="PNG")
                base64_image = base64.b64encode(buffered.getvalue()).decode("utf-8")
                logger.debug("ANNOTATED screenshot encoded to base64 for LLM.")

            # Return the full analysis result (with bboxes) and the ANNOTATED image's base64
            return analysis_result, base64_image

        except Exception as e:
            logger.error(f"Error getting screen analysis: {e}", exc_info=True)
            raise
        finally:
            if screenshot_path and os.path.exists(screenshot_path):
                try:
                    os.remove(screenshot_path)
                    logger.debug(f"Removed temporary screenshot: {screenshot_path}")
                except OSError as e:
                    logger.warning(f"Could not remove temporary screenshot {screenshot_path}: {e}")

    def run_plan(self, user_requirement: str):
        """Generates a plan based on user requirement and current screen."""
        logger.info(f"Received requirement: {user_requirement}")
        self.message_history = [] # Reset history for new requirement
        self.task_list = []
        self.should_stop = False

        try:
            analysis_result, base64_image = self._get_current_screen_analysis()
            # Add user request to history *before* planning call
            self.message_history.append({"role": "user", "content": user_requirement})

            plan_response: TaskPlanResponse = self.llm_interaction.get_task_plan(
                user_requirement,
                analysis_result,
                base64_image,
                self.system_info # Pass system info
            )

            self.task_list = plan_response.task_list
            # Add assistant response (plan) to history
            # Store the structured plan, not just the JSON string, if useful later
            self.message_history.append({
                "role": "assistant",
                "content": plan_response.model_dump_json() # Or store the Pydantic object itself?
                # "plan_object": plan_response # Example if storing object
            })

            # Log the generated plan
            print(self.task_list)
            logger.info("Generated Plan:")
            for i, task in enumerate(self.task_list):
                logger.info(f"  {i}. {task}")

            return self.task_list

        except Exception as e:
            logger.error(f"Error during planning phase: {e}", exc_info=True)
            self.message_history.append({"role": "system", "content": f"Error during planning: {e}"}) # Add error to history
            return [] # Return empty list on error

    def execute_tasks(self):
        """Executes the planned tasks step-by-step, removing completed tasks."""
        if not self.task_list:
            logger.warning("No tasks to execute.")
            return

        logger.info("--- Starting Task Execution ---")
        max_steps = 30 # Increased max steps slightly
        step_count = 0

        # Loop while tasks remain and stop signal not received
        while self.task_list and step_count < max_steps and not self.should_stop:
            step_count += 1
            current_task = self.task_list[0] # Get the current task
            logger.info(f"--- Step {step_count}: Current Task: '{current_task}' --- ({len(self.task_list)} tasks remaining)")

            try:
                current_analysis_result, base64_image = self._get_current_screen_analysis()

                # Call LLM for the *sequence* of actions for the CURRENT task
                action_sequence = self.llm_interaction.get_next_action(
                    self.message_history,
                    current_task, # Pass only the current task string
                    current_analysis_result,
                    base64_image,
                    self.system_info # Pass system info
                )

                # --- Inner Loop: Process Action Sequence --- #
                if not action_sequence:
                     logger.warning("LLM returned no actions for this step. Re-analyzing in next loop iteration.")
                     # Add a system message indicating no action was taken this step
                     self.message_history.append({"role": "system", "content": "LLM provided no actionable tool calls. Preparing for next analysis step."}) 
                     continue # Proceed to the next outer loop iteration (which will re-analyze)

                queue_processed_successfully = True # Flag for this sequence
                stop_outer_loop = False # Flag to stop processor entirely
                advance_to_next_task = False # Flag to move to the next task
                force_reanalyze = False # Flag to force reanalysis immediately
                force_change_task = False # NEW: Flag to skip current task

                # --- Add single assistant message summarizing the planned tool calls --- #
                tool_call_summary = []
                for action_enum_summary, args_dict_summary, reasoning_summary in action_sequence:
                    # Optionally format args for brevity/clarity in history
                    formatted_args = json.dumps(args_dict_summary or {})
                    tool_call_summary.append(
                        f"Tool: {action_enum_summary.value}, Args: {formatted_args}, Reasoning: {reasoning_summary or 'N/A'}"
                    )
                assistant_turn_content = "\n".join(tool_call_summary)
                self.message_history.append({"role": "assistant", "content": assistant_turn_content})
                # ---------------------------------------------------------------------- #

                for action_enum, args_dict, reasoning in action_sequence:
                    
                    # Log the reasoning for this specific action from the sequence
                    if reasoning:
                         logger.info(f"LLM Reasoning (Action: '{action_enum.value}'): {reasoning}")
                    # else: # Optional: Log if reasoning is missing
                    #    logger.info(f"LLM provided no specific reasoning for action '{action_enum.value}'.")
                    
                    # Log LLM Action Decision from the queue
                    log_action_details = [f"Action: {action_enum.value}"]
                    args_dict = args_dict or {} # Ensure args_dict is a dict
                    if "box_id" in args_dict:
                         log_action_details.append(f"Box ID: {args_dict.get('box_id')}")
                    if args_dict.get("coordinates"):
                         log_action_details.append(f"Coords: {args_dict['coordinates']}")
                    if "value" in args_dict:
                         log_action_details.append(f"Value: '{args_dict.get('value')}'")
                    if "keys" in args_dict:
                         log_action_details.append(f"Keys: '{args_dict.get('keys')}'")
                    if "direction" in args_dict:
                         log_action_details.append(f"Direction: {args_dict.get('direction')}")
                    if "duration_secs" in args_dict:
                         log_action_details.append(f"Duration: {args_dict.get('duration_secs')}s")
                    logger.info(f"LLM Decision (Queue): { ', '.join(log_action_details) }")
                    
                    # --- Process Special Control Actions --- #

                    # Check for overall completion FIRST
                    if action_enum == Action.DONE:
                        logger.info(f"LLM signaled OVERALL completion (Action.DONE). Stopping execution after this sequence.")
                        self.should_stop = True
                        stop_outer_loop = True
                        break # Exit the inner loop (queue processing)

                    # Check for current task completion
                    if action_enum == Action.TASK_COMPLETE:
                        logger.info(f"LLM signaled CURRENT task '{current_task}' complete. Will remove task after this sequence.")
                        advance_to_next_task = True
                        # Don't break here, allow subsequent actions *in this queue* if LLM provided them (though unlikely per prompt)
                        continue # Process next action in queue (if any)

                    # Handle REANALYZE (skip execution, stop queue, re-loop outer for new screenshot)
                    if action_enum == Action.REANALYZE:
                        logger.info(f"LLM requested re-analysis. Stopping queue and forcing re-analysis.")
                        self.message_history.append({"role": "system", "content": f"Action 'reanalyze' requested. Proceeding to next analysis step."}) 
                        force_reanalyze = True
                        break # Exit the inner loop (queue processing)
                        
                    # Handle CHANGE_TASK (skip execution, stop queue, set flag to remove task)
                    if action_enum == Action.CHANGE_TASK:
                        logger.warning(f"LLM requested CHANGE_TASK for task '{current_task}'. Reason: {reasoning or 'None provided'}. Stopping queue and skipping task.")
                        self.message_history.append({"role": "system", "content": f"Action 'change_task' requested by LLM. Skipping task: {current_task}. Reason: {reasoning}"}) 
                        force_change_task = True
                        break # Exit the inner loop (queue processing)

                    # --- Prepare and Execute Normal Actions --- #
                    action_name = action_enum.value
                    exec_args = {}
                    # args_dict already ensured to be a dict
                    box_id = args_dict.get("box_id")
                    explicit_coords = args_dict.get("coordinates")
                    coords_to_use = None

                    # Coordinate Logic (same as before)
                    if action_enum in [Action.LEFT_CLICK, Action.RIGHT_CLICK, Action.DOUBLE_CLICK, Action.HOVER, Action.DRAG_TO]:
                        if box_id is not None and box_id != -1:
                            # Find element coordinates based on box_id
                            element_dict = next((elem for elem in current_analysis_result.get("elements", []) if elem.get("element_id") == box_id), None)
                            # Calculate center from coordinates if element found
                            if element_dict and 'coordinates' in element_dict and len(element_dict['coordinates']) == 4:
                                bbox = element_dict['coordinates']
                                center_x = int((bbox[0] + bbox[2]) / 2)
                                center_y = int((bbox[1] + bbox[3]) / 2)
                                coords_to_use = (center_x, center_y)
                                logger.debug(f"Using calculated center coords {coords_to_use} for element ID {box_id}")
                            else:
                                logger.warning(f"Element ID {box_id} not found or missing valid coordinates in analysis result for action '{action_name}'. Skipping execution of this action.")
                                self.message_history.append({"role": "system", "content": f"Action '{action_name}' skipped: Element ID {box_id} not found or invalid."}) 
                                queue_processed_successfully = False
                                break # Stop processing this queue
                        elif explicit_coords and len(explicit_coords) == 2:
                            coords_to_use = tuple(explicit_coords)
                            logger.debug(f"Using explicit coordinates {coords_to_use} for action '{action_name}'.")
                        else:
                            # Neither box_id nor valid coordinates provided for a mouse action
                            logger.warning(f"Action '{action_name}' requires valid 'box_id' or 'coordinates'. Skipping execution of this action.")
                            self.message_history.append({"role": "system", "content": f"Action '{action_name}' skipped due to missing/invalid 'box_id' or 'coordinates'."}) 
                            queue_processed_successfully = False
                            break # Stop processing this queue
                        
                        # Assign coordinates for relevant actions
                        if action_enum in [Action.LEFT_CLICK, Action.RIGHT_CLICK, Action.DOUBLE_CLICK, Action.HOVER]:
                             exec_args['coords'] = coords_to_use
                        elif action_enum == Action.DRAG_TO:
                             exec_args['target_coords'] = coords_to_use # Assumes drag *from* current mouse pos

                    # Argument preparation for other actions (same as before)
                    elif action_enum == Action.TYPE:
                        text_value = args_dict.get("value")
                        if text_value is not None:
                            exec_args['text'] = text_value
                        else:
                            logger.warning(f"Action '{action_name}' requires 'value' argument. Skipping execution.")
                            self.message_history.append({"role": "system", "content": f"Action '{action_name}' skipped due to missing 'value' argument."}) 
                            queue_processed_successfully = False
                            break # Stop processing this queue
                    elif action_enum == Action.KEY:
                        keys_value = args_dict.get("keys")
                        if keys_value:
                            # Pass the raw string, executor will handle splitting/mapping
                            exec_args['keys'] = keys_value 
                        else:
                             logger.warning(f"Action '{action_name}' requires 'keys' argument (e.g., 'ctrl+c'). Skipping execution.")
                             self.message_history.append({"role": "system", "content": f"Action '{action_name}' skipped due to missing/invalid 'keys' argument."}) 
                             queue_processed_successfully = False
                             break # Stop processing this queue

                    elif action_enum == Action.SCROLL:
                        direction_value = args_dict.get("direction")
                        if direction_value in ["up", "down"]:
                            exec_args['direction'] = direction_value
                        else:
                             logger.warning(f"Action '{action_name}' requires valid 'direction' ('up'/'down'). Skipping execution.")
                             self.message_history.append({"role": "system", "content": f"Action '{action_name}' skipped due to missing/invalid 'direction' argument."}) 
                             queue_processed_successfully = False
                             break # Stop processing this queue
                    elif action_enum == Action.WAIT:
                        duration = args_dict.get("duration_secs")
                        if duration is not None:
                             try:
                                 exec_args['duration_secs'] = float(duration)
                             except (ValueError, TypeError):
                                 logger.warning(f"Invalid duration '{duration}' for WAIT action. Using default.")
                                 # Executor will use default if duration_secs is not passed or is None
                        # If duration is None or invalid, executor uses default
                    
                    # --- Execute the specific action from the queue --- #
                    logger.info(f"Executing action from queue: {action_name} with args: {exec_args}")
                    try:
                         exec_result: ActionResult = self.action_executor.execute(action_name, **exec_args)
                    except Exception as exec_e:
                         logger.error(f"Unexpected error during execution of {action_name}: {exec_e}", exc_info=True)
                         exec_result = ActionResult(success=False, error=str(exec_e))
                         
                    # Log result (same as before)
                    log_parts = []
                    if not exec_result.success:
                         log_parts.append("Success=False")
                    if exec_result.output:
                        log_parts.append(f"Output='{exec_result.output}'")
                    if exec_result.error:
                        log_parts.append(f"Error='{exec_result.error}'")
                    logger.info(f"Execution Result (Queue): { ', '.join(log_parts) if log_parts else 'Completed (no output/error)' }")

                    # Add execution result to history (same as before)
                    result_content = f"Action '{action_name}' executed."
                    if not exec_result.success:
                         result_content = f"Action '{action_name}' FAILED."
                    if exec_result.output:
                        result_content += f" Output: {exec_result.output}"
                    if exec_result.error:
                        result_content += f" Error: {exec_result.error}"
                    self.message_history.append({"role": "system", "content": result_content})

                    # Stop processing the REST of the queue if this action failed
                    if not exec_result.success:
                        logger.error(f"Execution failed for {action_name}: {exec_result.error}. Stopping processing of current action queue.")
                        queue_processed_successfully = False
                        # Optionally set should_stop for the outer loop? Decide based on desired behavior.
                        # self.should_stop = True # Uncomment to stop entirely on any execution failure
                        break # Stop processing this queue
                    
                    # Small delay between actions *within* the same queue? Optional.
                    # time.sleep(0.2) 

                # --- End of Inner Loop (Queue Processing) --- #
                
                # Check flags set during inner loop
                if stop_outer_loop:
                     break # Exit the main while loop
                
                if force_reanalyze:
                     # Already logged, just continue to next outer loop iteration for re-analysis
                     time.sleep(0.5) # Small delay before re-analyzing
                     continue 
                     
                if force_change_task:
                     logger.warning(f"Skipping task due to CHANGE_TASK request: '{current_task}'")
                     if self.task_list:
                          self.task_list.pop(0) # Remove skipped task
                     else:
                           logger.warning("CHANGE_TASK signaled but task list was already empty?")
                     if not self.task_list:
                          logger.info("Task list is now empty after skipping the task.")
                     time.sleep(0.5) # Small delay before starting next task analysis (if any)
                     continue # Go to the next outer loop iteration for the next task or re-analysis

                if advance_to_next_task and queue_processed_successfully:
                     logger.info(f"Task '{current_task}' marked complete. Removing task from list.")
                     if self.task_list:
                          self.task_list.pop(0) # Remove completed task
                     else:
                           logger.warning("TASK_COMPLETE signaled but task list was already empty?")
                     # If task list is now empty, maybe trigger DONE check? Or rely on LLM to call DONE.
                     if not self.task_list:
                          logger.info("Task list is now empty after completing the task.")
                          # Consider if we should automatically stop here or wait for explicit DONE call
                          # self.should_stop = True # Uncomment if empty list means done
                     time.sleep(0.5) # Small delay before starting next task analysis (if any)
                     continue # Go to the next outer loop iteration for the next task or re-analysis

                # If the queue was processed without critical errors/signals, add delay before next cycle
                if queue_processed_successfully:
                     # Delay before next analysis cycle (outer loop)
                     time.sleep(1.0) # Slightly shorter delay as potentially more happened

            except Exception as e:
                logger.error(f"Error during execution step {step_count} for task '{current_task}': {e}", exc_info=True)
                self.message_history.append({"role": "system", "content": f"Error during execution step {step_count}: {e}"}) # Add error to history
                # Decide if we should stop on error or try to continue with next task?
                # For now, let's stop.
                self.should_stop = True
                break # Stop on unexpected error in outer loop

        # --- Loop End Logging --- #
        if not self.task_list and not self.should_stop:
             logger.info("--- Task Execution Finished (Task list empty) ---")
        elif step_count >= max_steps:
            logger.warning("Reached maximum execution steps. Stopping.")
        elif self.should_stop:
             # Reason logged when should_stop was set (DONE or error)
             logger.info("--- Task Execution Finished (Stopped) ---")
        else:
            logger.info("--- Task Execution Finished (Unknown condition) ---")

    def stop(self):
        """Signals the execution loop to stop."""
        self.should_stop = True
        logger.info("Stop signal received for TaskProcessor.")

# Example Usage (Illustrative) - Remains commented out
# if __name__ == '__main__':
#     # Load config from a file or environment
#     config = {"openai": {"api_key": "YOUR_API_KEY", "model": "gpt-4o"}, "screen_analysis": {"yolo_model_path": "path/to/yolo.pt"}}
#     processor = TaskProcessor(config)
#     user_input = "Open notepad and type hello world"
#     tasks = processor.run_plan(user_input)
#     if tasks:
#        processor.execute_tasks()
