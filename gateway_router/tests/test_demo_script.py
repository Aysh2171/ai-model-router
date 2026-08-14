"""
Smoke unit test verifying that scripts/demo.py executes cleanly to completion as a subprocess.
"""

import subprocess
import sys
import unittest
from pathlib import Path


DEMO_SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "demo.py"


class TestDemoScript(unittest.TestCase):
    """Test suite verifying Gateway Router demonstration script execution."""

    def test_demo_smoke_execution(self):
        """Execute scripts/demo.py as subprocess and verify exit code 0."""
        self.assertTrue(DEMO_SCRIPT_PATH.exists(), f"Demo script not found at: {DEMO_SCRIPT_PATH}")

        result = subprocess.run(
            [sys.executable, str(DEMO_SCRIPT_PATH)],
            capture_output=True,
            text=True,
            timeout=30
        )

        self.assertEqual(
            result.returncode,
            0,
            f"Demo script failed with exit code {result.returncode}.\nStderr: {result.stderr}\nStdout: {result.stdout}"
        )
        self.assertIn("GATEWAY ROUTER DEMONSTRATION", result.stdout.upper())
        self.assertIn("Gateway Router Demonstration Complete", result.stdout)


if __name__ == "__main__":
    unittest.main()
