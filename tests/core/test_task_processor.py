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
from src.core.action_models import ActionResult

# Sample data
SAMPLE_CONFIG = {"model": "test_model", "yolo_model_path": "dummy/yolo.pt"}
SAMPLE_USER_REQUIREMENT = "Do something cool."
SAMPLE_TASK_LIST = ["Task 1: Click Button", "Task 2: Type Text"]

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
    return TaskProcessor(config=SAMPLE_CONFIG)

# --- Test Cases ---

def test_task_processor_init(processor, mock_dependencies):
    """Test TaskProcessor initialization."""
    MockLLM, MockScreen, MockAction = mock_dependencies
    # Check if the correct classes were called during TaskProcessor init
    MockLLM.assert_called_once_with(SAMPLE_CONFIG)
    MockScreen.assert_called_once_with(yolo_model_path=SAMPLE_CONFIG['yolo_model_path'])
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
            DUMMY_IMAGE_BASE64
        )
        assert tasks == SAMPLE_TASK_LIST
        assert processor.task_list == SAMPLE_TASK_LIST
        assert len(processor.message_history) == 2 # User req + Assistant plan
        assert processor.message_history[0]["role"] == "user"
        assert processor.message_history[1]["role"] == "assistant"

# TODO: Add test for run_plan error handling

def test_execute_tasks_single_step(processor, mock_dependencies):
    """Test execute_tasks for a single successful step."""
    MockLLM, MockScreen, MockAction = mock_dependencies
    mock_llm_instance = processor.llm_interaction # Get mock instance from processor
    mock_action_instance = processor.action_executor # Get mock instance from processor

    # --- Setup processor state ---
    processor.task_list = SAMPLE_TASK_LIST
    processor.message_history = [
        {"role": "user", "content": SAMPLE_USER_REQUIREMENT},
        {"role": "assistant", "content": TaskPlanResponse(reasoning="plan", task_list=SAMPLE_TASK_LIST).model_dump_json()}
    ]

    # --- Mock LLM action responses using side_effect ---
    from src.core.llm_interaction import create_dynamic_execution_response_model
    box_ids = [elem['element_id'] for elem in SAMPLE_SCREEN_ANALYSIS_RESULT['elements']]
    ActionResponseModel = create_dynamic_execution_response_model(box_ids)

    # First call: Perform the click action
    first_action_data = {
        "reasoning": "Click button 1",
        "next_action": Action.LEFT_CLICK,
        "box_id": 1,
        "coordinates": None,
        "value": None,
        "current_task_id": 0
    }
    first_response = ActionResponseModel(**first_action_data)

    # Second call: Indicate completion/stop
    second_action_data = {
        "reasoning": "Task 1 done, stopping.",
        "next_action": Action.NONE,
        "box_id": None,
        "coordinates": None,
        "value": None,
        "current_task_id": 0 # Or maybe 1 if task increment logic is assumed
    }
    second_response = ActionResponseModel(**second_action_data)

    # Set the side_effect on the mock
    mock_llm_instance.get_next_action.side_effect = [first_response, second_response]

    # --- Patch screen analysis ---
    with patch.object(processor, '_get_current_screen_analysis') as mock_get_analysis:
        mock_get_analysis.return_value = (SAMPLE_SCREEN_ANALYSIS_RESULT, DUMMY_IMAGE_BASE64)

        # --- Execute (will loop once then break because LLM mock only has one response) ---
        with patch('time.sleep', return_value=None): # Patch time.sleep
             processor.execute_tasks()

    # --- Assertions ---
    # Screen analysis should be called twice (once for each loop iteration before stopping)
    assert mock_get_analysis.call_count == 2
    # LLM should be called twice
    assert mock_llm_instance.get_next_action.call_count == 2

    # Check action execution (only the first action should execute)
    expected_x = (10 + 50) // 2
    expected_y = (10 + 30) // 2
    mock_action_instance.execute.assert_called_once_with(
        Action.LEFT_CLICK.value,
        x=expected_x,
        y=expected_y
    )

    # Check history update
    assert len(processor.message_history) == 5 # User req, Plan, LLM action1, System result1, LLM action2 (None)
    assert processor.message_history[2]["role"] == "assistant" # LLM action choice (Click)
    assert processor.message_history[3]["role"] == "system"    # Execution result (Click)
    assert processor.message_history[4]["role"] == "assistant" # LLM action choice (None)
    assert "Action 'left_click' executed" in processor.message_history[3]["content"]

# TODO: Add test for execute_tasks multiple steps
# TODO: Add test for execute_tasks with coordinate usage (box_id = -1)
# TODO: Add test for execute_tasks with TYPE action
# TODO: Add test for execute_tasks with LLM returning Action.NONE
# TODO: Add test for execute_tasks reaching max steps
# TODO: Add test for execute_tasks execution error
# TODO: Add test for execute_tasks analysis error 