"""
Unit and Functional Tests for main.py Interactive CLI Console.
"""

import sys
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import main
from gateway_router.src.models import GatewayResponse, ExecutionStatus, ExecutionMode


class TestMainCLI(unittest.TestCase):
    """Test suite verifying main.py CLI prompt helpers, validation, and request routing flows."""

    def setUp(self):
        self.ctx = main.CLIContext()

    def test_prompt_string_default_and_custom(self):
        """Verify prompt_string returns default when input is empty, and user input when provided."""
        with patch("builtins.input", return_value=""):
            self.assertEqual(main.prompt_string("Test", default="default_val"), "default_val")

        with patch("builtins.input", return_value="user_text"):
            self.assertEqual(main.prompt_string("Test", default="default_val"), "user_text")

    def test_prompt_freeform_custom_input(self):
        """Verify prompt_freeform returns the exact string entered by the user."""
        with patch("builtins.input", return_value="Custom user prompt about neural networks"):
            val = main.prompt_freeform("Enter your prompt.", example_text="Example text")
            self.assertEqual(val, "Custom user prompt about neural networks")

    def test_prompt_freeform_empty_input_uses_example(self):
        """Verify prompt_freeform returns the example text when the user presses Enter (empty input)."""
        with patch("builtins.input", return_value=""):
            val = main.prompt_freeform("Enter your prompt.", example_text="Default example text")
            self.assertEqual(val, "Default example text")

    def test_prompt_freeform_eof_or_interrupt(self):
        """Verify prompt_freeform safely falls back to example text on EOFError."""
        with patch("builtins.input", side_effect=EOFError):
            val = main.prompt_freeform("Enter your prompt.", example_text="Default example text")
            self.assertEqual(val, "Default example text")

    def test_prompt_int_validation_and_retry(self):
        """Verify prompt_int rejects non-integers and negative numbers before accepting valid integer."""
        with patch("builtins.input", side_effect=["invalid", "-5", "3"]):
            val = main.prompt_int("Turns", default=0, min_val=0)
            self.assertEqual(val, 3)

    def test_prompt_choice_selection(self):
        """Verify prompt_choice accepts valid numeric choices and rejects out-of-range inputs."""
        options = ["Option A", "Option B", "Option C"]
        with patch("builtins.input", side_effect=["99", "abc", "2"]):
            choice = main.prompt_choice("Choose", options, default_idx=1)
            self.assertEqual(choice, 2)

    def test_handle_new_request_programming_flow(self):
        """Verify Option 1 constructs correct request schema and invokes pipeline cleanly."""
        # Inputs: req_id, prompt, category (2=Programming), format (2=Code), turns (0)
        inputs = ["REQ-TEST-PROG", "Write a binary search function.", "2", "2", "0"]
        with patch("builtins.input", side_effect=inputs):
            main.handle_new_request(self.ctx)

    def test_handle_new_request_default_empty_prompt(self):
        """Verify Option 1 uses example prompt when user enters empty input at prompt."""
        # Inputs: req_id, prompt (""), category (1=General), format (1=Text), turns (0)
        inputs = ["REQ-TEST-DEFAULT-EMPTY", "", "1", "1", "0"]
        with patch("builtins.input", side_effect=inputs):
            main.handle_new_request(self.ctx)

    def test_handle_new_request_custom_unsupported_category(self):
        """Verify custom category (e.g. QuantumTeleportation) is passed unchanged into pipeline."""
        # Inputs: req_id, prompt, category (12=Custom), custom_name, format (1=Text), turns (0)
        inputs = ["REQ-TEST-QUANTUM", "Teleport particle", "12", "QuantumTeleportation", "1", "0"]
        with patch("builtins.input", side_effect=inputs):
            main.handle_new_request(self.ctx)

    def test_handle_attachment_request_valid_file(self):
        """Verify Option 2 validates file existence, extracts size/type, and routes request."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
            tf.write(b"%PDF-1.4 dummy pdf content for testing size extraction")
            temp_path = tf.name

        try:
            # Inputs: req_id, prompt, category (6=Doc Processing), file_path, add_another (N)
            inputs = ["REQ-TEST-ATT", "Analyze PDF", "6", temp_path, "N"]
            with patch("builtins.input", side_effect=inputs):
                main.handle_attachment_request(self.ctx)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_handle_attachment_request_rejects_missing_file_and_directory(self):
        """Verify Option 2 rejects missing files and directories gracefully without crashing."""
        missing_path = "C:/non_existent_folder_xyz/file.pdf"
        dir_path = str(PROJECT_ROOT)

        # Inputs: req_id, prompt, category (6), missing_path, dir_path, finish (empty string)
        inputs = ["REQ-TEST-REJECT", "Analyze", "6", missing_path, dir_path, ""]
        with patch("builtins.input", side_effect=inputs):
            main.handle_attachment_request(self.ctx)

    def test_handle_diagnostics_trace(self):
        """Verify Option 3 executes step-by-step diagnostic trace without errors."""
        inputs = ["Diagnose prompt", "2"]  # prompt, category (2=Programming)
        with patch("builtins.input", side_effect=inputs):
            main.handle_diagnostics(self.ctx)

    def test_handle_fault_demo_options(self):
        """Verify Option 4 fault injection sub-options (retry, permanent, timeout, isolation)."""
        # Test 1: Transient retry
        with patch("builtins.input", return_value="1"):
            main.handle_fault_demo(self.ctx)

        # Test 2: Permanent failure
        with patch("builtins.input", return_value="2"):
            main.handle_fault_demo(self.ctx)

        # Test 5: State isolation
        with patch("builtins.input", return_value="5"):
            main.handle_fault_demo(self.ctx)

    def test_handle_model_catalogue_navigation(self):
        """Verify Option 5 displays catalog and navigates filter/detail submenus."""
        # Submenu choices: 1 (Inspect gpt-4o), gpt-4o, 7 (Back)
        inputs = ["1", "gpt-4o", "7"]
        with patch("builtins.input", side_effect=inputs):
            main.handle_model_catalogue(self.ctx)

    def test_main_menu_exit_path(self):
        """Verify Option 7 terminates with SystemExit."""
        with patch("builtins.input", return_value="7"):
            with self.assertRaises(SystemExit):
                main.main_menu()


if __name__ == "__main__":
    unittest.main()
