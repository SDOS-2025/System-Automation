import sys
import pytest
from unittest.mock import MagicMock, patch, call # Make sure patch/call are imported

# Setup mocks before importing the module under test
mock_pyautogui = MagicMock()
mock_pyautogui.size.return_value = (1920, 1080)

mock_pyperclip = MagicMock()
sys.modules['pyautogui'] = mock_pyautogui
sys.modules['pyperclip'] = mock_pyperclip

from src.core.action_executor import ActionExecutor, ActionError
from src.core import action_executor # Import module for constants

# Define fixture at the top
@pytest.fixture
def executor():
    # Reset mocks each time fixture is used for isolation
    mock_pyautogui.reset_mock()
    mock_pyperclip.reset_mock()
    mock_pyperclip.paste.return_value = "initial_fixture_clipboard"
    # Configure default side effects (can be overridden in tests)
    mock_pyautogui.moveTo.side_effect = None
    mock_pyautogui.click.side_effect = None
    mock_pyautogui.rightClick.side_effect = None
    mock_pyautogui.doubleClick.side_effect = None
    mock_pyautogui.press.side_effect = None
    mock_pyautogui.hotkey.side_effect = None
    mock_pyautogui.scroll.side_effect = None
    return ActionExecutor()

@patch('time.sleep')
def test_execute_key_single(mock_sleep, executor):
    mock_pyautogui.reset_mock()
    result = executor.execute("key", keys="Enter")
    mock_pyautogui.press.assert_called_once_with("enter") # Check mapping
    mock_sleep.assert_called_once()
    assert result.output == "Pressed key(s): Enter"

@patch('time.sleep')
def test_execute_key_unmapped(mock_sleep, executor):
    mock_pyautogui.reset_mock()
    result = executor.execute("key", keys="a")
    mock_pyautogui.press.assert_called_once_with("a")
    assert result.output == "Pressed key(s): a"

@patch('time.sleep')
def test_execute_key_hotkey(mock_sleep, executor):
    mock_pyautogui.reset_mock()
    result = executor.execute("key", keys="Ctrl+C")
    mock_pyautogui.hotkey.assert_called_once_with("ctrl", "c")
    mock_sleep.assert_called_once()
    assert result.output == "Pressed key(s): Ctrl+C"

@patch('time.sleep')
def test_execute_key_hotkey_with_mapping(mock_sleep, executor):
    mock_pyautogui.reset_mock()
    result = executor.execute("key", keys="Super_L+Tab")
    mock_pyautogui.hotkey.assert_called_once_with("win", "tab") # Check mapping
    assert result.output == "Pressed key(s): Super_L+Tab"

def test_execute_key_missing_text(executor):
    result = executor.execute("key") # Missing keys kwarg
    assert result.error is not None
    assert "'keys' argument required" in result.error
    assert not result.success

@patch('time.sleep')
@patch('pyautogui.press', side_effect=Exception("Keypress error"))
def test_execute_key_press_error(mock_press_error, mock_sleep, executor):
    mock_pyautogui.reset_mock()
    mock_pyautogui.hotkey.reset_mock()
    result = executor.execute("key", keys="Enter")
    assert result.error is not None
    assert "Failed to press key(s) 'Enter': Keypress error" in result.error
    assert not result.success
    mock_press_error.assert_called_once_with('enter')
    mock_pyautogui.hotkey.assert_not_called() # Explicitly check hotkey wasn't called

@patch('time.sleep')
def test_execute_scroll_up(mock_sleep, executor):
    mock_pyautogui.reset_mock()
    result = executor.execute("scroll", direction="up")
    mock_pyautogui.scroll.assert_called_once_with(150)
    mock_sleep.assert_called_once()
    assert result.output == "Scrolled up"

@patch('time.sleep')
def test_execute_scroll_down(mock_sleep, executor):
    mock_pyautogui.reset_mock()
    result = executor.execute("scroll", direction="down")
    mock_pyautogui.scroll.assert_called_once_with(-150)
    mock_sleep.assert_called_once()
    assert result.output == "Scrolled down"

def test_execute_scroll_missing_direction(executor):
    """Test scroll action fails if direction is missing."""
    mock_pyautogui.reset_mock()
    result = executor.execute("scroll")
    assert not result.success
    assert "Invalid scroll direction" in result.error
    mock_pyautogui.scroll.assert_not_called()

def test_execute_scroll_invalid_direction(executor):
    """Test scroll action fails if direction is invalid."""
    mock_pyautogui.reset_mock()
    result = executor.execute("scroll", direction="sideways")
    assert not result.success
    assert "Invalid scroll direction" in result.error
    mock_pyautogui.scroll.assert_not_called()

@patch('time.sleep')
@patch('pyautogui.scroll', side_effect=Exception("Scroll error"))
def test_execute_scroll_error(mock_scroll_error, mock_sleep, executor):
    # Test scroll up error
    mock_pyautogui.reset_mock()
    result_up = executor.execute("scroll", direction="up")
    assert result_up.error is not None
    assert "Failed to scroll up: Scroll error" in result_up.error
    assert not result_up.success
    mock_scroll_error.assert_called_once_with(150)

    # Test scroll down error
    mock_pyautogui.reset_mock()
    mock_scroll_error.reset_mock()
    result_down = executor.execute("scroll", direction="down")
    assert result_down.error is not None
    assert "Failed to scroll down: Scroll error" in result_down.error
    assert not result_down.success
    mock_scroll_error.assert_called_once_with(-150)

@patch('time.sleep')
def test_execute_wait_default(mock_sleep, executor):
    mock_pyautogui.reset_mock()
    result = executor.execute("wait")
    mock_sleep.assert_called_once_with(action_executor.WAIT_DELAY_SECS)
    assert result.output.startswith("Waited for")

@patch('time.sleep')
def test_execute_wait_custom_duration(mock_sleep, executor):
    mock_pyautogui.reset_mock()
    custom_duration = 2.5
    result = executor.execute("wait", duration_secs=custom_duration)
    mock_sleep.assert_called_once_with(custom_duration)
    assert result.output == f"Waited for {custom_duration:.1f} seconds"

@patch('time.sleep')
def test_execute_wait_clamping(mock_sleep, executor):
    mock_pyautogui.reset_mock()
    # Too short
    executor.execute("wait", duration_secs=0.01)
    mock_sleep.assert_called_with(0.1)
    mock_sleep.reset_mock()
    # Too long
    executor.execute("wait", duration_secs=100.0)
    mock_sleep.assert_called_with(30.0)

@patch('time.sleep', side_effect=ValueError("Invalid time"))
def test_execute_wait_error(mock_sleep_error, executor):
    mock_pyautogui.reset_mock()
    result = executor.execute("wait")
    assert result.error is not None
    assert "Failed to wait: Invalid time" in result.error

def test_execute_unsupported_action(executor):
    result = executor.execute("fly_to_moon")
    assert result.error is not None
    assert "Unsupported action: fly_to_moon" in result.error

def test_execute_none_action(executor):
    result = executor.execute("None")
    assert result.output == "No action performed (None)."
    assert result.error is None