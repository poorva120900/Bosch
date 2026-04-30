"""Streamlit page wrapper for the Bosch ticket dashboard."""

from pathlib import Path
import runpy


PROJECT_ROOT = Path(__file__).resolve().parent.parent
runpy.run_path(str(PROJECT_ROOT / "dashboard" / "app.py"), run_name="__main__")