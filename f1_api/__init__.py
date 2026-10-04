"""
Formula 1 Data Management & Analysis Package.

A modular, extensible Python library for fetching and analyzing Formula 1
historical results, standings, and telemetry from free public APIs.
"""

from .base import BaseAPI, F1APIError, F1DataParseError, F1RequestError
from .openf1 import OpenF1API
from .f1api import F1APIDev, F1ConnectAPI
from .manager import F1APIManager

# Global default manager instance for quick and easy access
default_manager = F1APIManager()
get_data = default_manager.get_data

__all__ = [
    "BaseAPI",
    "F1APIError",
    "F1RequestError",
    "F1DataParseError",
    "OpenF1API",
    "F1APIDev",
    "F1ConnectAPI",
    "F1APIManager",
    "default_manager",
    "get_data",
]
