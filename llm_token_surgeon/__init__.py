"""
llm-token-surgeon 🔪
Cut your LLM API bill by 30-70%. No accuracy loss.
"""

from .surgeon import Surgeon, OptimizationResult, PRICING
from .middleware import SurgeonMiddleware
from .scanner import scan_file, scan_directory

__version__ = "0.1.0"
__author__ = "Ashish"
__license__ = "MIT"

__all__ = [
    "Surgeon",
    "OptimizationResult",
    "SurgeonMiddleware",
    "PRICING",
    "scan_file",
    "scan_directory",
]
