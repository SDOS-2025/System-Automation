import pytest
from unittest.mock import patch, MagicMock
import json
from pydantic import ValidationError, BaseModel
import openai # Import for potential exception testing

# Use src.core... as per pytest.ini configuration
from src.core.llm_interaction import (
    LLMInteraction,
    TaskPlanResponse,
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
    """Test get_next_action with a mocked OpenAI API call using Tool Calling."""
    mock_openai_client = llm_interaction._mock_openai_client

    # --- Mock the OpenAI API response for tool calls --- #
    # Define the tool call structure the LLM is expected to return
    mock_tool_call_id = "call_abc123"
    mock_tool_function_name = Action.LEFT_CLICK.value
    mock_tool_arguments = json.dumps({
        "box_id": 1,
        "reasoning": "Click the start button."
        # Coordinates are not provided when box_id is used
    })

    # Create a mock ChatCompletionMessage with tool_calls
    mock_response_message = MagicMock()
    mock_response_message.tool_calls = [
        MagicMock(
            id=mock_tool_call_id,
            type='function',
            function=MagicMock(
                name=mock_tool_function_name,
                arguments=mock_tool_arguments
            )
        )
    ]

    # Create a mock Choice object
    mock_choice = MagicMock()
    mock_choice.message = mock_response_message
    mock_choice.finish_reason = 'tool_calls'

    # Create the final mock Completion object
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    # ------------------------------------------------------ #

    # Configure the mock create method to return the prepared mock completion
    mock_openai_client.chat.completions.create.return_value = mock_completion

    # --- Prepare input for get_next_action --- #
    messages = [{"role": "user", "content": "Previous state info..."}]
    current_task = SAMPLE_TASK_LIST[0] # "Click Start Button"
    system_info = {"os": "test_os", "version": "1.0"} # Example system info
    # ----------------------------------------- #

    # --- Call the function under test --- #
    action_sequence = llm_interaction.get_next_action(
        message_history=messages,
        current_task=current_task,
        screen_analysis=SAMPLE_SCREEN_ANALYSIS,
        base64_image=SAMPLE_IMAGE_BASE64,
        system_info=system_info
    )
    # ------------------------------------ #

    # --- Assertions --- #
    # Verify the OpenAI API call arguments
    mock_openai_client.chat.completions.create.assert_called_once()
    call_args, call_kwargs = mock_openai_client.chat.completions.create.call_args
    assert call_kwargs['model'] == llm_interaction.model
    assert 'tools' in call_kwargs # Check that tools schema was passed
    assert call_kwargs['tool_choice'] == "auto" # Check tool_choice setting
    # Verify message structure (system, history, current state)
    api_messages = call_kwargs['messages']
    assert len(api_messages) >= 3 # System, history, current user message
    assert api_messages[0]['role'] == 'system'
    assert api_messages[1]['role'] == 'user' # From history
    assert api_messages[1]['content'] == messages[0]['content']
    assert api_messages[-1]['role'] == 'user' # Last message is the current state/prompt
    assert isinstance(api_messages[-1]['content'], list)
    assert any(item['type'] == 'text' and current_task in item['text'] for item in api_messages[-1]['content'])
    assert any(item['type'] == 'image_url' for item in api_messages[-1]['content'])

    # Assert the parsed action sequence
    assert isinstance(action_sequence, list)
    assert len(action_sequence) == 1 # Expecting one action from the mock
    action, args, reasoning = action_sequence[0]

    assert action == Action.LEFT_CLICK
    assert args == {"box_id": 1, "reasoning": "Click the start button."}
    assert reasoning == "Click the start button."
    # ----------------- #

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