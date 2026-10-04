from typing import Any, Callable, Dict, List, Optional, Pattern, Tuple, Union
import re
import pandas as pd

from .base import BaseAPI


def _default_extract(data: Any) -> pd.DataFrame:
    """Generic response handler: extracts primary known keys or nested lists."""
    if isinstance(data, dict):
        priority_keys = (
            "drivers",
            "teams",
            "circuits",
            "championships",
            "constructors_championship",
            "drivers_championship",
            "races",
            "race",
            "results",
            "driver",
            "team",
            "circuit",
            "championship",
        )
        for key in priority_keys:
            if key in data and data[key] is not None:
                return pd.json_normalize(data[key])

        for key, value in data.items():
            if isinstance(value, list) and key not in ("api", "url"):
                return pd.json_normalize(value)

    if data is None:
        return pd.DataFrame()

    return pd.json_normalize(data)


def _extract_keys(data: Any, keys: Tuple[str, ...]) -> pd.DataFrame:
    """Extract and normalize the first matching key, falling back to default extraction."""
    if isinstance(data, dict):
        for k in keys:
            if k in data and data[k] is not None:
                return pd.json_normalize(data[k])
    return _default_extract(data)


def _extract_driver_results(data: Any) -> pd.DataFrame:
    """Extract driver season results and enrich rows with driver metadata if available."""
    if isinstance(data, dict):
        results = data.get("results")
        if isinstance(results, list) and results:
            df = pd.json_normalize(results)
            driver = data.get("driver")
            if isinstance(driver, dict):
                for col in ("driverId", "name", "surname"):
                    if col in driver and col not in df.columns:
                        df[f"driver.{col}"] = driver[col]
            return df

        driver = data.get("driver")
        if driver is not None:
            return pd.json_normalize(driver)

    return _default_extract(data)


def _extract_session_results(data: Any) -> pd.DataFrame:
    """Extract and unpack detailed session results (Race, Qualy, Sprint, FP1-3)."""
    if isinstance(data, dict):
        race_obj = data.get("races") or data.get("race")
        if isinstance(race_obj, list) and race_obj:
            race_obj = race_obj[0]

        session_keys = (
            "results",
            "qualyResults",
            "sprintRaceResults",
            "sprintQualyResults",
            "fp1Results",
            "fp2Results",
            "fp3Results",
        )

        if isinstance(race_obj, dict):
            for k in session_keys:
                if k in race_obj and isinstance(race_obj[k], list) and race_obj[k]:
                    df = pd.json_normalize(race_obj[k])
                    # Enrich DataFrame with race metadata
                    for meta in reversed(["raceId", "raceName", "round", "date"]):
                        if meta in race_obj and meta not in df.columns:
                            df.insert(0, meta, race_obj[meta])
                    if "season" in data and "season" not in df.columns:
                        df.insert(0, "season", data["season"])
                    return df
            return pd.json_normalize(race_obj)

        for k in session_keys:
            if k in data and isinstance(data[k], list) and data[k]:
                return pd.json_normalize(data[k])

    return _default_extract(data)


class F1APIDev(BaseAPI):
    """
    Client for F1API.dev (https://f1api.dev/api/).
    Provides basic driver/team search, current season next/last races, and round results.
    """

    BASE_URL: str = "https://f1api.dev/api/"

    ENDPOINT_RULES: List[Dict[str, Any]] = [
        {
            "pattern": re.compile(r"^(?:drivers|teams|circuits)/search$"),
            "handler": lambda data: _extract_keys(data, ("drivers", "teams", "circuits")),
            "description": "F1API entity searches",
        },
        {
            "pattern": re.compile(r"^current/(?:last|next)$"),
            "handler": lambda data: _extract_keys(data, ("race",)),
            "description": "Current previous or next race",
        },
        {
            "pattern": re.compile(r"^\d{4}/\d+$"),
            "handler": lambda data: _extract_keys(data, ("race",)),
            "description": "Specific race by year and round",
        },
        {
            "pattern": re.compile(r"^current/constructors-championship$"),
            "handler": lambda data: _extract_keys(data, ("constructors_championship",)),
            "description": "Current constructors championship",
        },
        {
            "pattern": re.compile(r"^current/teams$"),
            "handler": lambda data: _extract_keys(data, ("teams",)),
            "description": "Current season teams list",
        },
    ]

    def __init__(
        self,
        base_url: str = BASE_URL,
        timeout: int = BaseAPI.DEFAULT_TIMEOUT,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        super().__init__(base_url=base_url, timeout=timeout, headers=headers)

    def _get_handler(self, clean_endpoint: str) -> Callable[[Any], pd.DataFrame]:
        path_only = clean_endpoint.split("?")[0]
        for rule in self.ENDPOINT_RULES:
            if rule["pattern"].match(path_only):
                return rule["handler"]
        return _default_extract

    def get_data(
        self,
        endpoint: str,
        params: Optional[Union[Dict[str, Any], str]] = None,
    ) -> pd.DataFrame:
        clean_endpoint = endpoint.strip("/")
        if clean_endpoint.startswith("api/"):
            clean_endpoint = clean_endpoint[4:].lstrip("/")

        url = self._build_url(endpoint=clean_endpoint, params=params)
        data = self._fetch_json(url)
        handler = self._get_handler(clean_endpoint)
        return handler(data)


class F1ConnectAPI(BaseAPI):
    """
    Client for F1ConnectAPI (https://f1connectapi.vercel.app/api/).
    Provides detailed session results (FP, Qualy, Sprint, Race), driver career details, and standings.
    """

    BASE_URL: str = "https://f1connectapi.vercel.app/api/"

    ENDPOINT_RULES: List[Dict[str, Any]] = [
        {
            "pattern": re.compile(r"^(?:current/last|\d{4}/\d+)/(?:fp[1-3]|qualy|race|sprint/(?:race|qualy))$"),
            "handler": _extract_session_results,
            "description": "Session results (FP, Qualy, Sprint, Race)",
        },
        {
            "pattern": re.compile(r"^(?:current|\d{4})/teams/[^/]+/drivers$"),
            "handler": lambda data: _extract_keys(data, ("drivers",)),
            "description": "Drivers of a team",
        },
        {
            "pattern": re.compile(r"^(?:current|\d{4})/drivers/[^/]+$"),
            "handler": _extract_driver_results,
            "description": "Driver details and season results",
        },
        {
            "pattern": re.compile(r"^(?:current/teams|teams|\d{4}/teams)/[^/]+$"),
            "handler": lambda data: _extract_keys(data, ("team",)),
            "description": "Single team details",
        },
        {
            "pattern": re.compile(r"^drivers/[^/]+$"),
            "handler": lambda data: _extract_keys(data, ("driver",)),
            "description": "Single driver details",
        },
        {
            "pattern": re.compile(r"^circuits/[^/]+$"),
            "handler": lambda data: _extract_keys(data, ("circuit",)),
            "description": "Single circuit details",
        },
        {
            "pattern": re.compile(r"^(?:drivers|current/drivers|\d{4}/drivers)$"),
            "handler": lambda data: _extract_keys(data, ("drivers",)),
            "description": "Drivers list",
        },
        {
            "pattern": re.compile(r"^(?:teams|\d{4}/teams)$"),
            "handler": lambda data: _extract_keys(data, ("teams",)),
            "description": "Teams list",
        },
        {
            "pattern": re.compile(r"^circuits$"),
            "handler": lambda data: _extract_keys(data, ("circuits",)),
            "description": "Circuits list",
        },
        {
            "pattern": re.compile(r"^seasons$"),
            "handler": lambda data: _extract_keys(data, ("championships",)),
            "description": "Seasons list",
        },
        {
            "pattern": re.compile(r"^(?:current|\d{4})/drivers-championship$"),
            "handler": lambda data: _extract_keys(data, ("drivers_championship",)),
            "description": "Drivers championship standings",
        },
        {
            "pattern": re.compile(r"^\d{4}/constructors-championship$"),
            "handler": lambda data: _extract_keys(data, ("constructors_championship",)),
            "description": "Historical constructors championship standings",
        },
        {
            "pattern": re.compile(r"^(?:current|\d{4})$"),
            "handler": lambda data: _extract_keys(data, ("races", "race")),
            "description": "Season race calendar",
        },
    ]

    def __init__(
        self,
        base_url: str = BASE_URL,
        timeout: int = BaseAPI.DEFAULT_TIMEOUT,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        super().__init__(base_url=base_url, timeout=timeout, headers=headers)

    def _get_handler(self, clean_endpoint: str) -> Callable[[Any], pd.DataFrame]:
        path_only = clean_endpoint.split("?")[0]
        for rule in self.ENDPOINT_RULES:
            if rule["pattern"].match(path_only):
                return rule["handler"]
        return _default_extract

    def get_data(
        self,
        endpoint: str,
        params: Optional[Union[Dict[str, Any], str]] = None,
    ) -> pd.DataFrame:
        clean_endpoint = endpoint.strip("/")
        if clean_endpoint.startswith("api/"):
            clean_endpoint = clean_endpoint[4:].lstrip("/")

        url = self._build_url(endpoint=clean_endpoint, params=params)
        data = self._fetch_json(url)
        handler = self._get_handler(clean_endpoint)
        return handler(data)
