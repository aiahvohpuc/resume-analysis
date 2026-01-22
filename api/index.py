"""Vercel Serverless Function entry point for FastAPI."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import app

# Vercel expects the app to be named 'app' or 'handler'
# FastAPI app is already named 'app' in src/main.py
