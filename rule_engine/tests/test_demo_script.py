"""
Smoke test for scripts/demo.py CLI demonstration entry point.
Verifies that executing `demo.py` as a subprocess returns exit code 0.
"""

import os
import sys
import unittest
import subprocess
from pathlib import Path

PROTOTYPE_ROOT = Path(__file__).resolve().parent.parent
ROUTER_ROOT = PROTOTYPE_ROOT.parent
DEMO_SCRIPT = PROTOTYPE_ROOT / "scripts" / "demo.py"


class TestDemoScript(unittest.TestCase):
    """Smoke test suite for scripts/demo.py execution."""

    def test_demo_smoke_execution(self):
        """Execute scripts/demo.py as subprocess and verify exit code 0."""
        env = os.environ.copy()
        pythonpath = f"{PROTOTYPE_ROOT}{os.pathsep}{ROUTER_ROOT}"
        if "PYTHONPATH" in env and env["PYTHONPATH"]:
            env["PYTHONPATH"] = f"{pythonpath}{os.pathsep}{env['PYTHONPATH']}"
        else:
            env["PYTHONPATH"] = pythonpath

        cmd = [sys.executable, str(DEMO_SCRIPT)]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(PROTOTYPE_ROOT),
            env=env
        )

        self.assertEqual(result.returncode, 0, f"demo.py failed with stderr:\n{result.stderr}")
        self.assertIn("Rule Engine Demonstration Complete", result.stdout)


if __name__ == "__main__":
    unittest.main()
