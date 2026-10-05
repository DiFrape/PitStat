from typing import Any, Dict, Optional, Union
import pandas as pd

from .base import BaseAPI
from .openf1 import OpenF1API
from .f1api import F1APIDev, F1ConnectAPI
from .jolpica import JolpicaAPI


class F1APIManager:
    """
    Unified manager and facade for all Formula 1 API providers.
    Coordinates requests across OpenF1, F1API.dev, F1ConnectAPI, and JolpicaAPI,
    and supports dynamic registration of new API clients.
    """

    def __init__(
        self,
        openf1_client: Optional[OpenF1API] = None,
        f1api_dev_client: Optional[F1APIDev] = None,
        f1connect_client: Optional[F1ConnectAPI] = None,
        jolpica_client: Optional[JolpicaAPI] = None,
    ) -> None:
        self.openf1 = openf1_client or OpenF1API()
        self.f1api_dev = f1api_dev_client or F1APIDev()
        self.f1connect = f1connect_client or F1ConnectAPI()
        self.jolpica = jolpica_client or JolpicaAPI()

        self._clients: Dict[str, BaseAPI] = {
            "openf1": self.openf1,
            "open": self.openf1,
            "f1apidev": self.f1api_dev,
            "f1connect": self.f1connect,
            "jolpica": self.jolpica,
        }

    def register_client(self, name: str, client: BaseAPI) -> None:
        """
        Register a new API client provider.

        :param name: Unique identifier for the provider (case-insensitive).
        :param client: Instance of a class inheriting from BaseAPI.
        """
        if not isinstance(client, BaseAPI):
            raise TypeError(f"Client must inherit from BaseAPI, got {type(client).__name__}")
        self._clients[name.lower().strip()] = client

    def get_client(self, name: str) -> BaseAPI:
        """
        Retrieve a registered API client by name.

        :param name: Provider name (e.g., 'openf1', 'f1connect').
        :return: BaseAPI client instance.
        :raises KeyError: If the provider is not registered.
        """
        normalized_name = name.lower().strip().replace("-", "").replace("_", "")
        if normalized_name in self._clients:
            return self._clients[normalized_name]
        raise KeyError(
            f"Provider '{name}' not found. Registered providers: {list(self._clients.keys())}"
        )

    def get_data(
        self,
        endpoint: str,
        params: Optional[Union[Dict[str, Any], str]] = None,
        api: str = "openf1",
    ) -> pd.DataFrame:
        """
        Query data from the specified API provider and normalize into a pandas DataFrame.

        :param endpoint: Target endpoint path (e.g., 'sessions', 'current/drivers', '2024/1/race').
        :param params: Optional query parameters dictionary or string.
        :param api: API provider selector: 'openf1' (default), 'f1api' (auto-routes f1api.dev/f1connect),
                    'f1connect', 'jolpica', or any custom registered provider name.
        :return: Normalized pandas DataFrame.
        """
        api_norm = api.lower().strip().replace("-", "").replace("_", "")

        if api_norm == "openf1":
            return self.openf1.get_data(endpoint=endpoint, params=params)

        if api_norm == "jolpica":
            return self.jolpica.get_data(endpoint=endpoint, params=params)

        if api_norm == "f1api":
            # Route between F1APIDev and F1ConnectAPI based on endpoint rules
            clean = endpoint.strip("/")
            if clean.startswith("api/"):
                clean = clean[4:].lstrip("/")
            path_only = clean.split("?")[0]

            for rule in self.f1api_dev.ENDPOINT_RULES:
                if rule["pattern"].match(path_only):
                    return self.f1api_dev.get_data(endpoint=clean, params=params)

            return self.f1connect.get_data(endpoint=clean, params=params)

        if api_norm == "f1connect":
            return self.f1connect.get_data(endpoint=endpoint, params=params)

        if api_norm in self._clients:
            return self._clients[api_norm].get_data(endpoint=endpoint, params=params)

        raise ValueError(
            f"Unknown API provider '{api}'. Supported values include: 'openf1', 'f1api', 'f1connect', 'jolpica', "
            f"or any registered custom provider."
        )
