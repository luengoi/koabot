"""
This module provides a method to detect if a given file object supports
virtual terminal escape codes.

Currently we only support this for non-windows systems.
"""

import os
from typing import IO


if os.name == "nt":
    def is_supported(f: IO) -> bool:
        return False
else:
    def is_supported(f: IO) -> bool:
        return f.isatty()

