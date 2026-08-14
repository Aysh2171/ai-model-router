"""
Smoke Test for Feedback Pipeline Demonstration Script.
"""

import sys
import subprocess
import unittest
from pathlib import Path


class TestDemoScript(unittest.TestCase):
    """Verifies that feedback_pipeline/scripts/demo.py executes cleanly to completion."""

    def test_demo_smoke_execution(self):
        """Execute scripts/demo.py as subprocess and verify exit code 0."""
        demo_script = Path(__file__).resolve().parent.parent / "scripts" / "demo.py"
        self.assertTrue(demo_script.exists(), f"Demo script not found at {demo_script}")

        result = subprocess.run(
            [sys.executable, str(demo_script)],
            capture_output=True,
            text=True,
            timeout=30
        )

        self.assertEqual(
            result.returncode,
            0,
            f"Demo script failed with code {result.returncode}.\nSTDERR:\n{result.stderr}\nSTDOUT:\n{result.stdout}"
        )
        self.assertIn("FEEDBACK PIPELINE DEMONSTRATION COMPLETE", result.stdout.upper())


if __name__ == "__main__":
    unittest.main()
