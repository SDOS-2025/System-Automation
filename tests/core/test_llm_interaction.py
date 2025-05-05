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
# SAMPLE_CONFIG = {"openai": {"api_key": "test_key", "model": "test_model"}} # OLD flat structure
SAMPLE_CONFIG = {
    "openai": {"api_key": "test_key", "model": "test_model"}
} # Correct nested structure
SAMPLE_USER_REQUIREMENT = "Open notepad and type hello."
SAMPLE_SCREEN_ANALYSIS = {"elements": [{"element_id": 1, "label": "Start Button"}]}
SAMPLE_IMAGE_BASE64 = "dummy_base64_string"
SAMPLE_TASK_LIST = ["Click Start Button", "Type notepad", "Press Enter", "Type hello"]
SAMPLE_AVAILABLE_BOX_IDS = [1, 2, 3]
SAMPLE_SYSTEM_INFO = {"os": "test_os", "version": "1.0"}

# --- Test Fixtures ---

@pytest.fixture
def llm_interaction():
    """Fixture to create an LLMInteraction instance for tests."""
    # Patch OpenAI client AND config loading utilities
    with patch('src.core.llm_interaction.OpenAI') as MockOpenAI, \
         patch('src.utils.config_loader.load_config') as mock_load_config, \
         patch('src.utils.config_loader.get_config_value') as mock_get_config_value:

        # Configure mock_get_config_value to return values from SAMPLE_CONFIG
        def side_effect(key, default=None):
            if key == "openai.api_key":
                return SAMPLE_CONFIG['openai']['api_key']
            if key == "openai.model":
                return SAMPLE_CONFIG['openai']['model']
            return default
        mock_get_config_value.side_effect = side_effect

        # Ensure load_config returns something (not strictly necessary if get_config is mocked)
        mock_load_config.return_value = SAMPLE_CONFIG

        # Init should use mocked values. Pass dummy config as it's not used directly.
        interaction = LLMInteraction(config={})

        interaction._mock_openai_class = MockOpenAI
        interaction._mock_openai_client = MockOpenAI.return_value
        yield interaction

# --- Test Cases ---

def test_llm_interaction_init(llm_interaction):
    """Test if LLMInteraction initializes correctly."""
    assert llm_interaction.model == SAMPLE_CONFIG['openai']['model']
    llm_interaction._mock_openai_class.assert_called_once_with(api_key=SAMPLE_CONFIG['openai']['api_key'])
    assert llm_interaction.client == llm_interaction._mock_openai_client

def test_get_task_plan_mocked(llm_interaction):
    """Test get_task_plan with a mocked OpenAI API call."""
    mock_openai_client = llm_interaction._mock_openai_client
    # Expected response object structure
    expected_plan = TaskPlanResponse(
        reasoning="Mock plan reasoning.",
        task_list=["Mock Task 1"]
    )

    # --- Mock the OpenAI API response structure --- #
    # The code expects response.choices[0].message.content to be a JSON string
    mock_response_content = expected_plan.model_dump_json()

    # Create mock message and choice
    mock_response_message = MagicMock()
    mock_response_message.content = mock_response_content
    mock_choice = MagicMock()
    mock_choice.message = mock_response_message

    # Create the final mock Completion object
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    # --------------------------------------------- #

    # Configure the mock create method to return the prepared mock completion
    mock_openai_client.chat.completions.create.return_value = mock_completion

    plan = llm_interaction.get_task_plan(
        user_requirement=SAMPLE_USER_REQUIREMENT,
        screen_analysis=SAMPLE_SCREEN_ANALYSIS,
        system_info=SAMPLE_SYSTEM_INFO,
        base64_image=SAMPLE_IMAGE_BASE64
    )

    assert plan == expected_plan # Check if the parsed plan matches the expected one

    # Verify the call to the OpenAI API
    mock_openai_client.chat.completions.create.assert_called_once()
    call_args, call_kwargs = mock_openai_client.chat.completions.create.call_args

    assert call_kwargs['model'] == llm_interaction.model
    # assert call_kwargs['response_model'] == TaskPlanResponse # REMOVED: Not used in planning call
    # Check messages structure (should include system prompt, user text, user image)
    messages = call_kwargs['messages']
    assert messages[0]['role'] == 'system'
    assert messages[1]['role'] == 'user'
    assert isinstance(messages[1]['content'], list)
    assert any(item['type'] == 'text' and SAMPLE_USER_REQUIREMENT in item['text'] for item in messages[1]['content'])
    assert any(item['type'] == 'image_url' for item in messages[1]['content'])
    # assert "system_info" in call_kwargs # Check system_info was passed? API call doesn't include it directly

def test_get_next_action_mocked(llm_interaction):
    """Test get_next_action with a mocked OpenAI API call using Tool Calling."""
    mock_openai_client = llm_interaction._mock_openai_client

    # --- Mock the OpenAI API response for tool calls --- #
    mock_tool_call_id = "call_abc123"
    mock_tool_function_name_str = Action.LEFT_CLICK.value # Use the string value
    mock_tool_arguments_dict = {
        "box_id": 1,
        "reasoning": "Click the start button."
    }
    expected_args_after_pop = {"box_id": 1} # Reasoning is popped
    mock_tool_arguments_json = json.dumps(mock_tool_arguments_dict)

    # Create mock function object with correct 'name' attribute
    mock_function = MagicMock()
    mock_function.name = mock_tool_function_name_str # Set the name explicitly
    mock_function.arguments = mock_tool_arguments_json

    # Create a mock ToolCall object
    mock_tool_call = MagicMock(
        id=mock_tool_call_id,
        type='function',
        function=mock_function # Assign the configured mock function
    )

    # Create mock message and choice
    mock_response_message = MagicMock()
    mock_response_message.tool_calls = [mock_tool_call]
    mock_choice = MagicMock()
    mock_choice.message = mock_response_message
    mock_choice.finish_reason = 'tool_calls'

    # Create the final mock Completion object
    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]
    # ------------------------------------------------------ #

    mock_openai_client.chat.completions.create.return_value = mock_completion

    # --- Prepare input for get_next_action --- #
    messages = [{"role": "user", "content": "Previous state info..."}]
    current_task = SAMPLE_TASK_LIST[0]
    # system_info = {"os": "test_os", "version": "1.0"} # Defined globally now
    # ----------------------------------------- #

    # --- Call the function under test --- #
    action_sequence = llm_interaction.get_next_action(
        message_history=messages,
        current_task=current_task,
        screen_analysis=SAMPLE_SCREEN_ANALYSIS,
        base64_image=SAMPLE_IMAGE_BASE64,
        system_info=SAMPLE_SYSTEM_INFO # Pass system info
    )
    # ------------------------------------ #

    # --- Assertions --- #
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
    # assert "system_info" in call_kwargs # REMOVED: system_info is not passed directly to API

    # Assert the parsed action sequence
    assert isinstance(action_sequence, list)
    assert len(action_sequence) == 1 # Expecting one action from the mock
    action, args, reasoning = action_sequence[0]

    assert action == Action.LEFT_CLICK
    # Arguments dict should be parsed from JSON AND reasoning popped
    assert args == expected_args_after_pop # NEW
    assert reasoning == "Click the start button."
    # ----------------- #

# TODO: Add tests for API error handling (e.g., APIError, RateLimitError)
# Example:
# def test_get_task_plan_api_error(llm_interaction): # REMOVED
#     """Test handling of OpenAI APIError during planning.""" # REMOVED
#     mock_openai_client = llm_interaction._mock_openai_client # REMOVED
#     error_message = "API Failed Badly" # REMOVED
#     mock_openai_client.chat.completions.create.side_effect = openai.APIError(error_message, request=None, body=None) # REMOVED
#
#     # The function should catch the error and return an error TaskPlanResponse # REMOVED
#     plan_response = llm_interaction.get_task_plan( # REMOVED
#         user_requirement=SAMPLE_USER_REQUIREMENT, # REMOVED
#         screen_analysis=SAMPLE_SCREEN_ANALYSIS, # REMOVED
#         system_info=SAMPLE_SYSTEM_INFO, # REMOVED
#         base64_image=SAMPLE_IMAGE_BASE64 # REMOVED
#     ) # REMOVED
#
#     mock_openai_client.chat.completions.create.assert_called_once() # REMOVED
#     # Assert that the returned response contains the error # REMOVED
#     assert not plan_response.task_list # REMOVED
#     assert f"Error: API call failed - {error_message}" in plan_response.reasoning # REMOVED

# TODO: Add tests for _prepare_messages helper function
# TODO: Add tests for error handling (e.g., invalid JSON from LLM) 