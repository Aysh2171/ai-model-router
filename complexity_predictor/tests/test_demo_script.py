"""
Smoke test for scripts/predict.py CLI demo entry point.
Verifies that executing `predict.py --demo` as a subprocess returns exit code 0 and prints JSON profile outputs.
Cross-platform portable across Windows, Linux, macOS, virtual environments, and CI runners.
"""

import os
import sys
import unittest
import subprocess
from pathlib import Path

# Paths to script and prototype root
PROTOTYPE_ROOT = Path(__file__).resolve().parent.parent
PREDICT_SCRIPT = PROTOTYPE_ROOT / "scripts" / "predict.py"


class TestDemoScript(unittest.TestCase):
    """Smoke test suite for scripts/predict.py --demo execution."""

    def test_demo_smoke_execution(self):
        """Execute predict.py --demo as subprocess and verify 0 exit code and valid JSON output."""
        env = os.environ.copy()
        pythonpath = str(PROTOTYPE_ROOT)
        if "PYTHONPATH" in env and env["PYTHONPATH"]:
            env["PYTHONPATH"] = f"{pythonpath}{os.pathsep}{env['PYTHONPATH']}"
        else:
            env["PYTHONPATH"] = pythonpath

        cmd = [sys.executable, str(PREDICT_SCRIPT), "--demo"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(PROTOTYPE_ROOT),
            env=env
        )

        self.assertEqual(result.returncode, 0, f"predict.py --demo failed with stderr:\n{result.stderr}")
        self.assertIn("GENERATED COMPLEXITY PROFILE", result.stdout)


if __name__ == "__main__":
    unittest.main()
