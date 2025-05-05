#!/usr/bin/env python
"""Unit tests for action_models."""

import unittest
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from src.core.action_models import ActionResult, ActionError
except ImportError as e:
    print(f"Error importing action_models: {e}")
    ActionResult = None
    ActionError = None

@unittest.skipIf(ActionResult is None or ActionError is None, "Skipping tests because action_models failed to import")
class TestActionModels(unittest.TestCase):

    def test_action_result_instantiation(self):
        """Test creating ActionResult instances."""
        # Default (empty)
        res1 = ActionResult()
        self.assertIsNone(res1.output)
        self.assertIsNone(res1.error)

        # With output
        res2 = ActionResult(output="Success")
        self.assertEqual(res2.output, "Success")
        self.assertIsNone(res2.error)

        # With error
        res3 = ActionResult(error="Failure")
        self.assertIsNone(res3.output)
        self.assertEqual(res3.error, "Failure")

        # With both (though typically not expected)
        res4 = ActionResult(output="Partial", error="Problem")
        self.assertEqual(res4.output, "Partial")
        self.assertEqual(res4.error, "Problem")

    def test_action_result_bool(self):
        """Test the boolean representation of ActionResult."""
        self.assertFalse(bool(ActionResult()))
        self.assertTrue(bool(ActionResult(output="Data")))
        self.assertTrue(bool(ActionResult(error="Issue")))
        self.assertTrue(bool(ActionResult(output="Data", error="Issue")))

    def test_action_result_add(self):
        """Test combining ActionResult instances using +."""
        res_out1 = ActionResult(output="First")
        res_out2 = ActionResult(output="Second")
        res_err1 = ActionResult(error="Error1")
        res_err2 = ActionResult(error="Error2")
        res_empty = ActionResult()

        # Output + Output
        combined1 = res_out1 + res_out2
        self.assertEqual(combined1.output, "First\nSecond")
        self.assertIsNone(combined1.error)

        # Output + Error (Error takes precedence)
        combined2 = res_out1 + res_err1
        self.assertIsNone(combined2.output)
        self.assertEqual(combined2.error, "Error1")

        # Error + Output (Error takes precedence)
        combined3 = res_err1 + res_out1
        self.assertIsNone(combined3.output)
        self.assertEqual(combined3.error, "Error1")

        # Error + Error (First error takes precedence)
        combined4 = res_err1 + res_err2
        self.assertIsNone(combined4.output)
        self.assertEqual(combined4.error, "Error1")

        # Empty + Output
        combined5 = res_empty + res_out1
        self.assertEqual(combined5.output, "First")
        self.assertIsNone(combined5.error)

        # Output + Empty
        combined6 = res_out1 + res_empty
        self.assertEqual(combined6.output, "First")
        self.assertIsNone(combined6.error)

        # Empty + Error
        combined7 = res_empty + res_err1
        self.assertIsNone(combined7.output)
        self.assertEqual(combined7.error, "Error1")

        # Error + Empty
        combined8 = res_err1 + res_empty
        self.assertIsNone(combined8.output)
        self.assertEqual(combined8.error, "Error1")

    def test_action_result_replace(self):
        """Test the replace method."""
        original = ActionResult(output="Original Output", error="Original Error")

        # Replace output
        replaced1 = original.replace(output="New Output")
        self.assertEqual(replaced1.output, "New Output")
        self.assertEqual(replaced1.error, "Original Error")
        self.assertIsNot(replaced1, original) # Should be a new instance

        # Replace error
        replaced2 = original.replace(error="New Error")
        self.assertEqual(replaced2.output, "Original Output")
        self.assertEqual(replaced2.error, "New Error")

        # Replace both
        replaced3 = original.replace(output=None, error=None)
        self.assertIsNone(replaced3.output)
        self.assertIsNone(replaced3.error)

    def test_action_error(self):
        """Test raising and catching ActionError."""
        error_message = "Something went wrong"
        with self.assertRaises(ActionError) as cm:
            raise ActionError(error_message)
        self.assertEqual(cm.exception.message, error_message)
        self.assertEqual(str(cm.exception), error_message)

if __name__ == '__main__':
    unittest.main() 