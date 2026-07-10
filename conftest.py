"""Root pytest configuration for OmniWatch 2.0 tests."""
import sys
from pathlib import Path

# Ensure project root is on sys.path so top-level packages resolve
PROJECT_ROOT = str(Path(__file__).resolve().parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
