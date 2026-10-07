from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
import pandas as pd


class F1APIError(Exception):
    """Base exception for all F1 API related errors."""
    pass


class F1RequestError(F1APIError):
    """Exception raised when an HTTP request or network connection fails."""
    pass


class F1DataParseError(F1APIError):
    """Exception raised when parsing or normalizing API response fails."""
    pass


class BaseAPI(ABC):
    """
    Abstract base class for all Formula 1 API client implementations.
    Centralizes URL construction, HTTP dispatch, and error handling.
    """

    DEFAULT_USER_AGENT: str = "Formula1-Data-Client/1.0"
    DEFAULT_TIMEOUT: int = 15

    def __init__(
        self,
        base_url: str,
        timeout: int = DEFAULT_TIMEOUT,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Initialize the base API client.

        :param base_url: Root endpoint URL for the API provider.
        :param timeout: Timeout in seconds for HTTP requests.
        :param headers: Optional custom HTTP headers dictionary.
        """
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout = timeout
        self.headers = headers or {"User-Agent": self.DEFAULT_USER_AGENT}

    def _build_url(self, endpoint: str, params: Optional[Union[Dict[str, Any], str]] = None) -> str:
        """
        Construct the complete target URL by merging base URL, endpoint, and query parameters.

        :param endpoint: Target endpoint path.
        :param params: Optional query parameters as dictionary or raw string.
        :return: Complete URL string.
        """
        clean_endpoint = endpoint.strip("/")
        base = f"{self.base_url}{clean_endpoint}"

        if not params:
            return base

        if isinstance(params, dict):
            query = urlencode(params)
        else:
            query = str(params).lstrip("?")

        separator = "&" if "?" in clean_endpoint else "?"
        return f"{base}{separator}{query}"

    def _fetch_json(self, url: str) -> Any:
        """
        Execute an HTTP GET request to the specified URL and parse JSON response.

        :param url: Complete URL to request.
        :return: Parsed JSON content (dict, list, etc.).
        :raises F1RequestError: On network or HTTP error.
        :raises F1DataParseError: If response body cannot be decoded as valid JSON.
        """
        req = Request(url, headers=self.headers)
        try:
            with urlopen(req, timeout=self.timeout) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                raw_bytes = response.read()
                return json.loads(raw_bytes.decode(charset))
        except (HTTPError, URLError) as err:
            raise F1RequestError(f"HTTP request failed for URL '{url}': {err}") from err
        except (json.JSONDecodeError, UnicodeDecodeError) as err:
            raise F1DataParseError(f"Failed to decode JSON response from '{url}': {err}") from err

    @abstractmethod
    def get_data(
        self,
        endpoint: str,
        params: Optional[Union[Dict[str, Any], str]] = None,
    ) -> pd.DataFrame:
        """
        Fetch data from the specified endpoint and return a structured pandas DataFrame.

        :param endpoint: Target API endpoint.
        :param params: Optional parameters dictionary or query string.
        :return: Normalized pandas DataFrame.
        """
        pass
