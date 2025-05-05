import pytest
from unittest.mock import patch, MagicMock
import json
from pydantic import ValidationError, BaseModel
import openai # Import for potential exception testing

# Use src.core... as per pytest.ini configuration
from src.core.llm_interaction import (
    LLMInteraction,
    TaskPlanResponse,
    create_dynamic_execution_response_model,
    Action,
    logger # Import logger if we want to test log messages
)

# Sample data for testing
SAMPLE_CONFIG = {"openai": {"api_key": "test_key", "model": "test_model"}}
SAMPLE_USER_REQUIREMENT = "Open notepad and type hello."
SAMPLE_SCREEN_ANALYSIS = {"elements": [{"element_id": 1, "label": "Start Button"}]}
SAMPLE_IMAGE_BASE64 = "dummy_base64_string"
SAMPLE_TASK_LIST = ["Click Start Button", "Type notepad", "Press Enter", "Type hello"]
SAMPLE_AVAILABLE_BOX_IDS = [1, 2, 3]

# --- Test Fixtures ---

@pytest.fixture
def llm_interaction():
    """Fixture to create an LLMInteraction instance for tests."""
    # Patch the OpenAI client initialization within the fixture's scope
    with patch('src.core.llm_interaction.OpenAI') as MockOpenAI:
        # Configure the mock client instance if needed, or just let LLMInteraction create it
        interaction = LLMInteraction(config=SAMPLE_CONFIG)
        # Store the mock class and instance for assertions if needed later
        interaction._mock_openai_class = MockOpenAI
        interaction._mock_openai_client = MockOpenAI.return_value
        yield interaction

# --- Test Cases ---

def test_llm_interaction_init(llm_interaction):
    """Test if LLMInteraction initializes correctly."""
    assert llm_interaction.config == SAMPLE_CONFIG
    assert llm_interaction.model == SAMPLE_CONFIG['openai']['model']
    # Check that OpenAI client was initialized
    llm_interaction._mock_openai_class.assert_called_once_with(api_key=SAMPLE_CONFIG['openai']['api_key'])
    assert llm_interaction.client == llm_interaction._mock_openai_client

def test_get_task_plan_mocked(llm_interaction):
    """Test get_task_plan with a mocked OpenAI API call."""
    mock_openai_client = llm_interaction._mock_openai_client
    # Expected response object structure (using the model directly)
    expected_response_obj = TaskPlanResponse(
        reasoning="Mock plan reasoning.",
        task_list=["Mock Task 1"]
    )
    # Configure the mock create method to return the Pydantic object
    mock_openai_client.chat.completions.create.return_value = expected_response_obj

    plan = llm_interaction.get_task_plan(
        user_requirement=SAMPLE_USER_REQUIREMENT,
        screen_analysis_results=SAMPLE_SCREEN_ANALYSIS,
        image_base64=SAMPLE_IMAGE_BASE64
    )

    assert plan == expected_response_obj # Response should be the Pydantic object directly

    # Verify the call to the OpenAI API
    mock_openai_client.chat.completions.create.assert_called_once()
    call_args, call_kwargs = mock_openai_client.chat.completions.create.call_args

    assert call_kwargs['model'] == llm_interaction.model
    assert call_kwargs['response_model'] == TaskPlanResponse
    # Check messages structure (should include system prompt, user text, user image)
    messages = call_kwargs['messages']
    assert messages[0]['role'] == 'system'
    assert messages[1]['role'] == 'user'
    assert isinstance(messages[1]['content'], list)
    assert any(item['type'] == 'text' and item['text'] == SAMPLE_USER_REQUIREMENT for item in messages[1]['content'])
    assert any(item['type'] == 'image_url' for item in messages[1]['content'])

def test_get_next_action_mocked(llm_interaction):
    """Test get_next_action with a mocked OpenAI API call."""
    mock_openai_client = llm_interaction._mock_openai_client

    # Define the expected structure and data for the *dynamic* response
    box_ids = [elem['element_id'] for elem in SAMPLE_SCREEN_ANALYSIS['elements']]
    ExpectedDynamicModel = create_dynamic_execution_response_model(box_ids + [-1]) # Add -1 as function does

    expected_response_data = {
        "reasoning": "Mock action reasoning.",
        "next_action": Action.LEFT_CLICK,
        "box_id": 1,
        "coordinates": None,
        "value": None,
        "current_task_id": 0
    }
    expected_response_obj = ExpectedDynamicModel(**expected_response_data)

    # Configure the mock create method
    mock_openai_client.chat.completions.create.return_value = expected_response_obj

    messages = [{"role": "user", "content": "Previous state info..."}]

    action_response = llm_interaction.get_next_action(
        messages=messages,
        task_list=SAMPLE_TASK_LIST,
        screen_analysis_results=SAMPLE_SCREEN_ANALYSIS,
        image_base64=SAMPLE_IMAGE_BASE64,
    )

    assert action_response == expected_response_obj

    # Verify the call to the OpenAI API
    mock_openai_client.chat.completions.create.assert_called_once()
    call_args, call_kwargs = mock_openai_client.chat.completions.create.call_args

    assert call_kwargs['model'] == llm_interaction.model
    # Check that the *correct type* of dynamic model was passed
    assert call_kwargs['response_model'].__name__ == ExpectedDynamicModel.__name__
    # Check messages structure (should include system, history, user text+image)
    api_messages = call_kwargs['messages']
    assert api_messages[0]['role'] == 'system'
    assert api_messages[1]['role'] == 'user' # From history
    assert api_messages[1]['content'] == messages[0]['content']
    assert api_messages[2]['role'] == 'user' # Added by _prepare_messages
    assert isinstance(api_messages[2]['content'], list)
    assert any(item['type'] == 'text' for item in api_messages[2]['content'])
    assert any(item['type'] == 'image_url' for item in api_messages[2]['content'])


def test_create_dynamic_execution_response_model():
    """Test the dynamic creation of the execution response model (remains the same)."""
    box_ids = [5, 10, 15]
    DynamicModel = create_dynamic_execution_response_model(box_ids)
    assert issubclass(DynamicModel, BaseModel)
    valid_data = {"reasoning": "r", "next_action": "left_click", "box_id": 5, "current_task_id": 0}
    instance = DynamicModel(**valid_data)
    assert instance.box_id == 5
    valid_data_neg_one = {"reasoning": "r", "next_action": "left_click", "box_id": -1, "coordinates": [10, 20], "current_task_id": 0}
    instance_neg_one = DynamicModel(**valid_data_neg_one)
    assert instance_neg_one.box_id == -1
    assert instance_neg_one.coordinates == [10, 20]
    valid_data_none = {"reasoning": "r", "next_action": "scroll_down", "box_id": None, "current_task_id": 0}
    instance_none = DynamicModel(**valid_data_none)
    assert instance_none.box_id is None
    with pytest.raises((ValidationError, ValueError)):
        invalid_data = {"reasoning": "r", "next_action": "left_click", "box_id": 99, "current_task_id": 0}
        DynamicModel(**invalid_data)

# TODO: Add tests for API error handling (e.g., APIError, RateLimitError)
# Example:
def test_get_task_plan_api_error(llm_interaction):
    """Test handling of OpenAI APIError during planning."""
    mock_openai_client = llm_interaction._mock_openai_client
    mock_openai_client.chat.completions.create.side_effect = openai.APIError("API Failed", request=None, body=None)

    with pytest.raises(openai.APIError):
        llm_interaction.get_task_plan(
            user_requirement=SAMPLE_USER_REQUIREMENT,
            screen_analysis_results=SAMPLE_SCREEN_ANALYSIS,
            image_base64=SAMPLE_IMAGE_BASE64
        )
    mock_openai_client.chat.completions.create.assert_called_once()

# TODO: Add tests for _prepare_messages helper function
# TODO: Add tests for error handling (e.g., invalid JSON from LLM) 