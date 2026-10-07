"""
Formula 1 Data Management & Analysis Package.

A modular, extensible Python library for fetching and analyzing Formula 1
historical results, standings, and telemetry from free public APIs.
"""

from .api import (
    BaseAPI,
    F1APIError,
    F1DataParseError,
    F1RequestError,
    OpenF1API,
    F1APIDev,
    F1ConnectAPI,
    JolpicaAPI,
    F1APIManager,
    default_manager,
    get_data,
)

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
