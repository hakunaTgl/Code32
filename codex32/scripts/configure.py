#!/usr/bin/env python
"""
Configuration wizard entry point.

Usage:
    python scripts/configure.py
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config_wizard import main

if __name__ == "__main__":
    main()
