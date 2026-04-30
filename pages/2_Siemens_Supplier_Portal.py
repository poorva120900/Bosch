"""Streamlit page wrapper for the Siemens supplier portal."""

from pathlib import Path
import runpy


PROJECT_ROOT = Path(__file__).resolve().parent.parent
runpy.run_path(str(PROJECT_ROOT / "dashboard" / "customer_portal.py"), run_name="__main__")