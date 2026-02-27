"""
Convenience entry-point that delegates to the main pipeline.

This script ensures the project root is on sys.path so that
``python scripts/run_pipeline.py`` works from any working directory.
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from main import run_pipeline  # noqa: E402


if __name__ == "__main__":
    run_pipeline()
