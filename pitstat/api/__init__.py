"""
API providers and manager for Formula 1 data retrieval.
"""

from .base import BaseAPI, F1APIError, F1DataParseError, F1RequestError
from .openf1 import OpenF1API
from .f1api import F1APIDev, F1ConnectAPI
from .jolpica import JolpicaAPI
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
    "JolpicaAPI",
    "F1APIManager",
    "default_manager",
    "get_data",
]
