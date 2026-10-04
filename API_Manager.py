"""
Backward-compatibility wrapper for legacy scripts and notebooks (e.g., F1_Stats.ipynb).
Redirects procedural calls to the modular OOP classes in the f1_api package.
"""

from typing import Any, Dict, Optional, Union
import pandas as pd

from f1_api import (
    BaseAPI,
    F1APIDev,
    F1APIError,
    F1APIManager,
    F1ConnectAPI,
    F1DataParseError,
    F1RequestError,
    OpenF1API,
    default_manager,
)
from f1_api.openf1 import OpenF1API
from f1_api.f1api import F1APIDev, F1ConnectAPI

# Legacy base URL constants maintained for backward compatibility
BASE_URL_OPENF1: str = OpenF1API.BASE_URL
BASE_URL_F1API: str = F1APIDev.BASE_URL
BASE_URL_F1CONNECT: str = F1ConnectAPI.BASE_URL


def get_data(
    endpoint: str,
    params: Optional[Union[Dict[str, Any], str]] = None,
    api: str = "openf1",
) -> pd.DataFrame:
    """
    Unified entry point to fetch data from the specified API provider.

    :param endpoint: Target endpoint path (e.g., 'sessions', 'current/drivers').
    :param params: Optional query parameters dictionary or string.
    :param api: API provider ('openf1', 'f1api', 'f1connect').
    :return: Structured pandas DataFrame.
    """
    return default_manager.get_data(endpoint=endpoint, params=params, api=api)


def get_data_openF1(
    endpoint: str,
    params: Optional[Union[Dict[str, Any], str]] = None,
) -> pd.DataFrame:
    """
    Query OpenF1 endpoint and return a structured pandas DataFrame.

    :param endpoint: Target OpenF1 endpoint (e.g., 'sessions', 'car_data', 'drivers').
    :param params: Optional query parameters dictionary or string.
    :return: Structured pandas DataFrame.
    """
    return default_manager.openf1.get_data(endpoint=endpoint, params=params)


def get_data_f1api(
    endpoint: str,
    params: Optional[Union[Dict[str, Any], str]] = None,
) -> pd.DataFrame:
    """
    Query F1API / F1Connect endpoint and return a structured pandas DataFrame.

    :param endpoint: Target endpoint (e.g., 'current/drivers', 'seasons', 'current/last/qualy').
    :param params: Optional query parameters dictionary or string.
    :return: Structured pandas DataFrame.
    """
    return default_manager.get_data(endpoint=endpoint, params=params, api="f1api")


__all__ = [
    "BASE_URL_OPENF1",
    "BASE_URL_F1API",
    "BASE_URL_F1CONNECT",
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
    "get_data_openF1",
    "get_data_f1api",
]