from typing import Any, Dict, List, Optional, Union
import pandas as pd

from .base import BaseAPI


def _unpack_race_results(
    races: List[Dict[str, Any]],
    sub_key: str,
) -> pd.DataFrame:
    """
    Unpack session results (Results, QualifyingResults, SprintResults) from each race,
    enriching each row with race-level metadata and circuit information.
    """
    rows: List[Dict[str, Any]] = []

    for race in races:
        # Extract race-level metadata
        race_meta: Dict[str, Any] = {
            "season": race.get("season"),
            "round": race.get("round"),
            "raceName": race.get("raceName"),
            "date": race.get("date"),
            "time": race.get("time"),
            "url": race.get("url"),
        }

        # Enrich with circuit metadata if available
        circuit = race.get("Circuit")
        if isinstance(circuit, dict):
            race_meta["circuitId"] = circuit.get("circuitId")
            race_meta["circuitName"] = circuit.get("circuitName")
            location = circuit.get("Location")
            if isinstance(location, dict):
                race_meta["locality"] = location.get("locality")
                race_meta["country"] = location.get("country")

        sub_items = race.get(sub_key, [])
        if isinstance(sub_items, list):
            for item in sub_items:
                if isinstance(item, dict):
                    # Combine race metadata with individual item
                    combined = {**race_meta, **item}
                    rows.append(combined)

    if rows:
        return pd.json_normalize(rows)
    return pd.DataFrame()


def _unpack_standings(standings_lists: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Unpack DriverStandings or ConstructorStandings across standings lists.
    """
    rows: List[Dict[str, Any]] = []

    for item in standings_lists:
        season = item.get("season")
        round_num = item.get("round")
        standings = item.get("DriverStandings") or item.get("ConstructorStandings") or []

        if isinstance(standings, list):
            for entry in standings:
                if isinstance(entry, dict):
                    row = {"season": season, "round": round_num, **entry}
                    rows.append(row)

    if rows:
        return pd.json_normalize(rows)
    return pd.DataFrame()


def _parse_jolpica_response(data: Any) -> pd.DataFrame:
    """
    Parse Ergast/Jolpica MRData response structure into a normalized pandas DataFrame.
    """
    if not isinstance(data, dict):
        return pd.DataFrame()

    mr_data = data.get("MRData", data)
    if not isinstance(mr_data, dict):
        return pd.DataFrame()

    # Look for known tables in MRData
    for key, value in mr_data.items():
        if not (key.endswith("Table") and isinstance(value, dict)):
            continue

        table = value

        # 1. RaceTable
        if "Races" in table and isinstance(table["Races"], list):
            races = table["Races"]
            if not races:
                return pd.DataFrame()

            # Check for nested sub-results
            first_race = races[0]
            if isinstance(first_race, dict):
                if "Results" in first_race:
                    return _unpack_race_results(races, "Results")
                if "QualifyingResults" in first_race:
                    return _unpack_race_results(races, "QualifyingResults")
                if "SprintResults" in first_race:
                    return _unpack_race_results(races, "SprintResults")

            # Simple race calendar/schedule
            return pd.json_normalize(races)

        # 2. StandingsTable
        if "StandingsLists" in table and isinstance(table["StandingsLists"], list):
            return _unpack_standings(table["StandingsLists"])

        # 3. Known entity lists
        for entity_key in ("Drivers", "Constructors", "Circuits", "Status", "Seasons"):
            if entity_key in table and isinstance(table[entity_key], list):
                return pd.json_normalize(table[entity_key])

        # 4. Fallback for any list inside the table
        for sub_key, sub_val in table.items():
            if isinstance(sub_val, list) and sub_val:
                return pd.json_normalize(sub_val)

        return pd.json_normalize(table)

    # Fallback: scan MRData for any list
    for key, val in mr_data.items():
        if key not in ("xmlns", "series", "url", "limit", "offset", "total") and isinstance(val, list):
            return pd.json_normalize(val)

    return pd.DataFrame()


class JolpicaAPI(BaseAPI):
    """
    Client for Jolpica F1 API (https://api.jolpi.ca/ergast/f1/).
    The community-maintained successor to the Ergast F1 API.
    Provides comprehensive historical race results, circuit records, driver/constructor standings,
    and multi-year aggregations in structured pandas DataFrames.
    """

    BASE_URL: str = "https://api.jolpi.ca/ergast/f1/"

    def __init__(
        self,
        base_url: str = BASE_URL,
        timeout: int = BaseAPI.DEFAULT_TIMEOUT,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Initialize the Jolpica API client.

        :param base_url: Root endpoint URL (defaults to https://api.jolpi.ca/ergast/f1/).
        :param timeout: Timeout in seconds for HTTP requests.
        :param headers: Optional custom HTTP headers.
        """
        super().__init__(base_url=base_url, timeout=timeout, headers=headers)

    def _prepare_endpoint(self, endpoint: str) -> str:
        """
        Normalize endpoint path by ensuring .json suffix is present.
        """
        clean = endpoint.strip("/")
        path, sep, query = clean.partition("?")

        if not path.endswith(".json"):
            path = f"{path}.json"

        return f"{path}{sep}{query}" if sep else path

    def get_data(
        self,
        endpoint: str,
        params: Optional[Union[Dict[str, Any], str]] = None,
    ) -> pd.DataFrame:
        """
        Query Jolpica endpoint and return a normalized pandas DataFrame.

        :param endpoint: Target endpoint path (e.g., 'circuits/marina_bay/races', '2024/results').
        :param params: Optional query parameters dictionary or string (e.g., {'limit': 100}).
        :return: Normalized pandas DataFrame.
        """
        prepared_endpoint = self._prepare_endpoint(endpoint)
        url = self._build_url(endpoint=prepared_endpoint, params=params)
        data = self._fetch_json(url)
        return _parse_jolpica_response(data)
