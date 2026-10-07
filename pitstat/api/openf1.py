from typing import Any, Dict, Optional, Union
import pandas as pd

from .base import BaseAPI


class OpenF1API(BaseAPI):
    """
    Client for OpenF1 API (https://openf1.org).
    Provides telemetry, laps, car data, intervals, weather, and session stats.
    """

    BASE_URL: str = "https://api.openf1.org/v1/"

    def __init__(
        self,
        base_url: str = BASE_URL,
        timeout: int = BaseAPI.DEFAULT_TIMEOUT,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Initialize the OpenF1 API client.

        :param base_url: Base endpoint URL for OpenF1 (defaults to https://api.openf1.org/v1/).
        :param timeout: Request timeout in seconds.
        :param headers: Optional custom HTTP headers.
        """
        super().__init__(base_url=base_url, timeout=timeout, headers=headers)

    def get_data(
        self,
        endpoint: str,
        params: Optional[Union[Dict[str, Any], str]] = None,
    ) -> pd.DataFrame:
        """
        Query OpenF1 endpoint and return a structured pandas DataFrame.

        :param endpoint: Target endpoint (e.g., 'sessions', 'car_data', 'laps', 'drivers').
        :param params: Optional query parameters dictionary or string.
        :return: Normalized pandas DataFrame.
        """
        url = self._build_url(endpoint=endpoint, params=params)
        data = self._fetch_json(url)

        if not data:
            return pd.DataFrame()

        return pd.json_normalize(data)
