import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from typing import List, Dict, Any, Tuple
import base64
from io import BytesIO
from PIL import Image

# Adjust imports based on project structure (running pytest from SystemAutomation)
from src.core.task_processor import TaskProcessor
from src.core.llm_interaction import LLMInteraction, TaskPlanResponse, Action
from src.core.screen_analysis import ScreenAnalyzer, UIElement
from src.core.action_executor import ActionExecutor
from src.core.action_models import ActionResult, Action

# Sample data
SAMPLE_CONFIG = {
    "openai": {"api_key": "test_key", "model": "test_model"},
    "screen_analysis": {"yolo_model_path": "dummy/yolo.pt"}
}
SAMPLE_USER_REQUIREMENT = "Do something cool."
SAMPLE_TASK_LIST = ["Task 1: Click Button", "Task 2: Type Text"]

# ADDED: Sample system info
SAMPLE_SYSTEM_INFO = {"os": "Linux", "version": "TestOS 1.0"}

# Create a dummy PNG image in memory for mocking screen capture
def create_dummy_image_bytes(width=100, height=50):
    img = Image.new('RGB', (width, height), color = 'red')
    buf = BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

DUMMY_IMAGE_BYTES = create_dummy_image_bytes()
DUMMY_IMAGE_BASE64 = base64.b64encode(DUMMY_IMAGE_BYTES).decode('utf-8')

SAMPLE_SCREEN_ANALYSIS_RESULT = {
    "elements": [
        {"element_id": 1, "label": "Button", "coordinates": [10, 10, 50, 30]},
        {"element_id": 2, "label": "Input Field", "coordinates": [10, 40, 90, 60]}
    ],
    "width": 100,
    "height": 50,
}

# --- Fixtures ---

@pytest.fixture
def mock_dependencies():
    with patch('src.core.task_processor.LLMInteraction', autospec=True) as MockLLM:
        with patch('src.core.task_processor.ScreenAnalyzer', autospec=True) as MockScreen:
            with patch('src.core.task_processor.ActionExecutor', autospec=True) as MockAction:
                with patch('src.core.task_processor.Image.open') as mock_image_open:
                    with patch('src.core.task_processor.base64.b64encode') as mock_b64encode:

                        # Configure ScreenAnalyzer mock
                        mock_screen_instance = MockScreen.return_value
                        mock_screen_instance.capture_screen.return_value = "dummy_path.png"
                        mock_elements = [UIElement(**data) for data in SAMPLE_SCREEN_ANALYSIS_RESULT['elements']]
                        mock_screen_instance.analyze_image_from_path.return_value = mock_elements

                        # Configure Image.open mock
                        mock_img = MagicMock()
                        mock_img.size = (SAMPLE_SCREEN_ANALYSIS_RESULT['width'], SAMPLE_SCREEN_ANALYSIS_RESULT['height'])
                        def mock_save(buffer, format):
                            buffer.write(DUMMY_IMAGE_BYTES)
                        mock_img.save = mock_save
                        mock_image_open.return_value.__enter__.return_value = mock_img

                        # Configure base64 encode mock
                        mock_b64encode.return_value.decode.return_value = DUMMY_IMAGE_BASE64

                        # Configure LLM mock
                        mock_llm_instance = MockLLM.return_value
                        mock_plan = TaskPlanResponse(reasoning="Plan reason", task_list=SAMPLE_TASK_LIST)
                        mock_llm_instance.get_task_plan.return_value = mock_plan

                        # Configure ActionExecutor mock
                        mock_action_instance = MockAction.return_value
                        # Create an empty ActionResult to signify success (error=None)
                        mock_action_instance.execute.return_value = ActionResult()

                        # Yield the mocks
                        yield MockLLM, MockScreen, MockAction

@pytest.fixture
def processor(mock_dependencies):
    MockLLM, MockScreen, MockAction = mock_dependencies
    # We pass the config, TaskProcessor will instantiate mocks internally
    # ADDED system_info argument
    return TaskProcessor(config=SAMPLE_CONFIG, system_info=SAMPLE_SYSTEM_INFO)

# --- Test Cases ---

def test_task_processor_init(processor, mock_dependencies):
    """Test TaskProcessor initialization."""
    MockLLM, MockScreen, MockAction = mock_dependencies
    # Check if the correct classes were called during TaskProcessor init
    MockLLM.assert_called_once_with(SAMPLE_CONFIG)
    MockScreen.assert_called_once_with(yolo_model_path=SAMPLE_CONFIG['screen_analysis']['yolo_model_path'])
    MockAction.assert_called_once_with()
    assert processor.message_history == []
    assert processor.task_list == []

def test_get_current_screen_analysis(processor, mock_dependencies):
    """Test the internal screen analysis gathering."""
    MockLLM, MockScreen, MockAction = mock_dependencies
    mock_screen_instance = MockScreen.return_value

    analysis_result, base64_image = processor._get_current_screen_analysis()

    mock_screen_instance.capture_screen.assert_called_once()
    mock_screen_instance.analyze_image_from_path.assert_called_once_with("dummy_path.png")
    assert base64_image == DUMMY_IMAGE_BASE64
    # Check if elements were correctly converted back to dicts
    assert analysis_result["elements"] == [elem.model_dump() for elem in mock_screen_instance.analyze_image_from_path.return_value]
    assert analysis_result["width"] == SAMPLE_SCREEN_ANALYSIS_RESULT["width"]
    assert analysis_result["height"] == SAMPLE_SCREEN_ANALYSIS_RESULT["height"]

def test_run_plan(processor, mock_dependencies):
    """Test the run_plan method."""
    MockLLM, MockScreen, MockAction = mock_dependencies
    mock_llm_instance = processor.llm_interaction # Get mock instance from processor

    # Patch _get_current_screen_analysis to simplify test
    with patch.object(processor, '_get_current_screen_analysis') as mock_get_analysis:
        mock_get_analysis.return_value = (SAMPLE_SCREEN_ANALYSIS_RESULT, DUMMY_IMAGE_BASE64)

        tasks = processor.run_plan(SAMPLE_USER_REQUIREMENT)

        mock_get_analysis.assert_called_once()
        mock_llm_instance.get_task_plan.assert_called_once_with(
            SAMPLE_USER_REQUIREMENT,
            SAMPLE_SCREEN_ANALYSIS_RESULT,
            DUMMY_IMAGE_BASE64,
            SAMPLE_SYSTEM_INFO
        )
        assert tasks == SAMPLE_TASK_LIST
        assert processor.task_list == SAMPLE_TASK_LIST
        assert len(processor.message_history) == 2 # User req + Assistant plan
        assert processor.message_history[0]["role"] == "user"
        assert processor.message_history[1]["role"] == "assistant"

# TODO: Add test for run_plan error handling

def test_execute_tasks_single_step(processor, mock_dependencies):
    """Test execute_tasks for a single successful step using Tool Calling."""
    MockLLM, MockScreen, MockAction = mock_dependencies
    mock_llm_instance = processor.llm_interaction
    mock_action_instance = processor.action_executor

    # --- Setup processor state ---
    processor.task_list = SAMPLE_TASK_LIST # ["Task 1: Click Button", ...]
    initial_history = [
        {"role": "user", "content": SAMPLE_USER_REQUIREMENT},
        {"role": "assistant", "content": TaskPlanResponse(reasoning="plan", task_list=SAMPLE_TASK_LIST).model_dump_json()}
    ]
    processor.message_history = initial_history.copy()

    # --- Mock LLM get_next_action response (Tool Calling) ---
    # First call: LLM requests a single action (left_click)
    action_args = {"box_id": 1, "reasoning": "Click the button"}
    first_llm_response = [
        (Action.LEFT_CLICK, action_args, "Click the button")
    ]
    # Second call: LLM returns an empty list (or DONE/TASK_COMPLETE if testing that)
    # For this test, let's assume it returns empty, stopping the loop after one action
    second_llm_response = []
    # Third call: LLM also returns empty after re-analysis
    third_llm_response = []

    mock_llm_instance.get_next_action.side_effect = [first_llm_response, second_llm_response, third_llm_response]

    # --- Mock ActionExecutor response ---
    # Assume successful execution for this test
    mock_action_instance.execute.return_value = ActionResult(output="Clicked button 1", success=True)

    # --- Patch screen analysis --- 
    with patch.object(processor, '_get_current_screen_analysis') as mock_get_analysis:
        mock_get_analysis.return_value = (SAMPLE_SCREEN_ANALYSIS_RESULT, DUMMY_IMAGE_BASE64)

        # --- Execute --- 
        with patch('time.sleep', return_value=None): # Patch time.sleep
             processor.execute_tasks()

    # --- Assertions --- 
    # Screen analysis called four times (loop 1, 2, 3, 4 before StopIteration)
    assert mock_get_analysis.call_count == 4
    # LLM called four times (exhausting the side_effect on the 4th call)
    assert mock_llm_instance.get_next_action.call_count == 4

    # Check get_next_action calls (only first 3 succeeded)
    assert len(mock_llm_instance.get_next_action.call_args_list) == 4
    # first_call_args = mock_llm_instance.get_next_action.call_args_list[0][1] # This gets kwargs
    first_call_positional_args = mock_llm_instance.get_next_action.call_args_list[0][0] # Get positional args
    first_call_keyword_args = mock_llm_instance.get_next_action.call_args_list[0][1] # Get keyword args

    # Assert positional arguments
    # assert first_call_positional_args[0] == initial_history # message_history # This fails due to list mutation
    # Check if the history passed *started* with the initial history
    passed_history = first_call_positional_args[0]
    assert len(passed_history) >= len(initial_history)
    assert passed_history[:len(initial_history)] == initial_history

    assert first_call_positional_args[1] == SAMPLE_TASK_LIST[0] # current_task
    assert first_call_positional_args[2] == SAMPLE_SCREEN_ANALYSIS_RESULT # screen_analysis
    assert first_call_positional_args[3] == DUMMY_IMAGE_BASE64 # base64_image
    assert first_call_positional_args[4] == SAMPLE_SYSTEM_INFO # system_info

    # Assert keyword arguments (should be empty if all passed positionally)
    assert not first_call_keyword_args 

    # Check action execution call
    # Find element 1 coordinates and calculate center
    elem1_coords = SAMPLE_SCREEN_ANALYSIS_RESULT['elements'][0]['coordinates'] # [10, 10, 50, 30]
    expected_x = (elem1_coords[0] + elem1_coords[2]) // 2 # (10 + 50) // 2 = 30
    expected_y = (elem1_coords[1] + elem1_coords[3]) // 2 # (10 + 30) // 2 = 20
    mock_action_instance.execute.assert_called_once_with(
        Action.LEFT_CLICK.value, 
        coords=(expected_x, expected_y) # TaskProcessor calculates coords
    )

    # Check history update
    # initial(2) + assistant tools(1) + system result(1) + system no action(1) + system no action(1) + system error(1) = 7
    assert len(processor.message_history) == 7
    assert processor.message_history[0]["role"] == "user"
    assert processor.message_history[1]["role"] == "assistant" # Plan
    assert processor.message_history[2]["role"] == "assistant" # Tool call summary 1
    assert Action.LEFT_CLICK.value in processor.message_history[2]["content"]
    assert processor.message_history[3]["role"] == "system"    # Execution result 1
    assert "Action 'left_click' executed" in processor.message_history[3]["content"]
    assert processor.message_history[4]["role"] == "system"    # LLM provided no action (loop 2)
    assert "LLM provided no actionable tool calls" in processor.message_history[4]["content"]
    assert processor.message_history[5]["role"] == "system"    # LLM provided no action (loop 3)
    assert "LLM provided no actionable tool calls" in processor.message_history[5]["content"]
    assert processor.message_history[6]["role"] == "system"    # Error during execution
    assert "Error during execution step 4" in processor.message_history[6]["content"]

    # Task list should still contain both tasks as DONE/TASK_COMPLETE wasn't called
    assert processor.task_list == SAMPLE_TASK_LIST

# TODO: Add test for execute_tasks multiple steps
# TODO: Add test for execute_tasks with coordinate usage (box_id = -1)
# TODO: Add test for execute_tasks with TYPE action
# TODO: Add test for execute_tasks with LLM returning Action.NONE
# TODO: Add test for execute_tasks reaching max steps
# TODO: Add test for execute_tasks execution error
# TODO: Add test for execute_tasks analysis error 