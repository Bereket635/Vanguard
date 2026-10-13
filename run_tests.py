#!/usr/bin/env python3
"""Run the Vanguard test suite from the project root."""
import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

if __name__ == "__main__":
    verbosity = 2 if "-v" in sys.argv else 1
    suite = unittest.TestLoader().discover(
        start_dir=str(_ROOT / "tests"),
        top_level_dir=str(_ROOT),
    )
    result = unittest.TextTestRunner(verbosity=verbosity).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
