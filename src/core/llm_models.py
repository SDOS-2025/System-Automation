#!/usr/bin/env python
"""Pydantic models for representing LLM responses."""

from typing import List
from pydantic import BaseModel, Field

# Import the Action enum from the sibling module
from .action_models import Action

class TaskPlanResponse(BaseModel):
    """Model for the response when asking the LLM to generate a task plan."""
    reasoning: str = Field(..., description="The LLM's reasoning for the generated task list.")
    task_list: List[str] = Field(..., description="The sequence of tasks to achieve the user's goal.")

class NextActionResponse(BaseModel):
    """Model for the response when asking the LLM for the next action."""
    reasoning: str = Field(..., description="The LLM's reasoning for choosing the next action.")
    next_action: Action = Field(..., description="The specific action to execute next.")
    box_id: int = Field(..., description="The element ID to interact with (-1 for coordinates or no element).")
    coordinates: List[int] = Field(default=[], description="Coordinates [x, y] for the action, if applicable.")
    value: str = Field(default="", description="Text value for typing or key presses, if applicable.")
    current_task_id: int = Field(..., description="The index of the task currently being worked on.") 