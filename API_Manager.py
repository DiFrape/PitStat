from urllib.request import urlopen, Request
from urllib.parse import urlencode
import json
import re
import pandas as pd

BASE_URL_OPENF1 = 'https://api.openf1.org/v1/'
BASE_URL_F1API = 'https://f1api.dev/api/'
BASE_URL_F1CONNECT = 'https://f1connectapi.vercel.app/api/'


def _extract_data(data: dict, keys: tuple) -> pd.DataFrame:
    """Estrae e normalizza la prima chiave presente tra quelle indicate, con fallback al default."""
    if isinstance(data, dict):
        for k in keys:
            if k in data and data[k] is not None:
                return pd.json_normalize(data[k])
    return _default_extract(data)


def _extract_driver_results(data: dict) -> pd.DataFrame:
    """Estrae i risultati di stagione del pilota arricchendoli con le info pilota se disponibili."""
    if isinstance(data, dict):
        if "results" in data and isinstance(data["results"], list) and data["results"]:
            df = pd.json_normalize(data["results"])
            if "driver" in data and isinstance(data["driver"], dict):
                for col in ("driverId", "name", "surname"):
                    if col in data["driver"] and col not in df.columns:
                        df[f"driver.{col}"] = data["driver"][col]
            return df
        if "driver" in data and data["driver"] is not None:
            return pd.json_normalize(data["driver"])
    return _default_extract(data)


def _extract_session_results(data: dict) -> pd.DataFrame:
    """Estrae e spacchetta i risultati dettagliati di una sessione (gara, qualifica, sprint, prove libere)."""
    if isinstance(data, dict):
        race_obj = data.get("races") or data.get("race")
        if isinstance(race_obj, list) and race_obj:
            race_obj = race_obj[0]

        session_keys = (
            "results", "qualyResults", "sprintRaceResults",
            "sprintQualyResults", "fp1Results", "fp2Results", "fp3Results"
        )

        if isinstance(race_obj, dict):
            for k in session_keys:
                if k in race_obj and isinstance(race_obj[k], list) and race_obj[k]:
                    df = pd.json_normalize(race_obj[k])
                    # Arricchisce il DataFrame con i metadati della gara (raceId, raceName, round, date, season)
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


def _default_extract(data) -> pd.DataFrame:
    """Gestione generica della response F1API: estrae chiavi primarie note o liste di dati."""
    if isinstance(data, dict):
        for key in (
            "drivers", "teams", "circuits", "championships",
            "constructors_championship", "drivers_championship",
            "races", "race", "results", "driver", "team", "circuit", "championship"
        ):
            if key in data and data[key] is not None:
                return pd.json_normalize(data[key])
        for key, value in data.items():
            if isinstance(value, list) and key not in ("api", "url"):
                return pd.json_normalize(value)
    return pd.json_normalize(data)


# Struttura dati che associa i pattern regex degli endpoint all'URL corretto e alla gestione della response
F1API_ENDPOINT_CONFIG = [
    # --- ENDPOINT F1API.DEV ---
    # 1. Ricerche testuali (search)
    {
        "pattern": re.compile(r"^(?:drivers|teams|circuits)/search$"),
        "base_url": BASE_URL_F1API,
        "handler": lambda data: _extract_data(data, ("drivers", "teams", "circuits")),
        "description": "Ricerche F1API",
    },
    # 2. Gare corrente / precedente / successiva
    {
        "pattern": re.compile(r"^current/(?:last|next)$"),
        "base_url": BASE_URL_F1API,
        "handler": lambda data: _extract_data(data, ("race",)),
        "description": "Gara precedente o successiva",
    },
    # 3. Gara per anno e round: [year]/[round] (es. 2024/5)
    {
        "pattern": re.compile(r"^\d{4}/\d+$"),
        "base_url": BASE_URL_F1API,
        "handler": lambda data: _extract_data(data, ("race",)),
        "description": "Gara specifica per anno e round",
    },
    # 4. Classifica costruttori stagione corrente
    {
        "pattern": re.compile(r"^current/constructors-championship$"),
        "base_url": BASE_URL_F1API,
        "handler": lambda data: _extract_data(data, ("constructors_championship",)),
        "description": "Classifica costruttori corrente",
    },
    # 5. Lista team stagione corrente
    {
        "pattern": re.compile(r"^current/teams$"),
        "base_url": BASE_URL_F1API,
        "handler": lambda data: _extract_data(data, ("teams",)),
        "description": "Lista team stagione corrente",
    },

    # --- ENDPOINT F1CONNECTAPI (VERCEL) ---
    # 6. Risultati sessioni (FP1-3, Qualy, Race, Sprint) sia current che per round specifico
    {
        "pattern": re.compile(r"^(?:current/last|\d{4}/\d+)/(?:fp[1-3]|qualy|race|sprint/(?:race|qualy))$"),
        "base_url": BASE_URL_F1CONNECT,
        "handler": lambda data: _extract_session_results(data),
        "description": "Risultati sessioni (FP, Qualy, Sprint, Race)",
    },
    # 7. Piloti di un team: current/teams/[teamId]/drivers o [year]/teams/[teamId]/drivers
    {
        "pattern": re.compile(r"^(?:current|\d{4})/teams/[^/]+/drivers$"),
        "base_url": BASE_URL_F1CONNECT,
        "handler": lambda data: _extract_data(data, ("drivers",)),
        "description": "Piloti di un team",
    },
    # 8. Dettaglio pilota con risultati: current/drivers/[driverId] o [year]/drivers/[driverId]
    {
        "pattern": re.compile(r"^(?:current|\d{4})/drivers/[^/]+$"),
        "base_url": BASE_URL_F1CONNECT,
        "handler": lambda data: _extract_driver_results(data),
        "description": "Dettaglio pilota e risultati stagione",
    },
    # 9. Singolo team: teams/[teamId], current/teams/[teamId], [year]/teams/[teamId]
    {
        "pattern": re.compile(r"^(?:current/teams|teams|\d{4}/teams)/[^/]+$"),
        "base_url": BASE_URL_F1CONNECT,
        "handler": lambda data: _extract_data(data, ("team",)),
        "description": "Dettaglio singolo team",
    },
    # 10. Singolo pilota: drivers/[driverId]
    {
        "pattern": re.compile(r"^drivers/[^/]+$"),
        "base_url": BASE_URL_F1CONNECT,
        "handler": lambda data: _extract_data(data, ("driver",)),
        "description": "Dettaglio singolo pilota",
    },
    # 11. Singolo circuito: circuits/[circuitId]
    {
        "pattern": re.compile(r"^circuits/[^/]+$"),
        "base_url": BASE_URL_F1CONNECT,
        "handler": lambda data: _extract_data(data, ("circuit",)),
        "description": "Dettaglio singolo circuito",
    },
    # 12. Liste piloti: drivers, current/drivers, [year]/drivers
    {
        "pattern": re.compile(r"^(?:drivers|current/drivers|\d{4}/drivers)$"),
        "base_url": BASE_URL_F1CONNECT,
        "handler": lambda data: _extract_data(data, ("drivers",)),
        "description": "Lista piloti",
    },
    # 13. Liste team: teams, [year]/teams
    {
        "pattern": re.compile(r"^(?:teams|\d{4}/teams)$"),
        "base_url": BASE_URL_F1CONNECT,
        "handler": lambda data: _extract_data(data, ("teams",)),
        "description": "Lista team",
    },
    # 14. Lista circuiti: circuits
    {
        "pattern": re.compile(r"^circuits$"),
        "base_url": BASE_URL_F1CONNECT,
        "handler": lambda data: _extract_data(data, ("circuits",)),
        "description": "Lista circuiti",
    },
    # 15. Lista stagioni: seasons
    {
        "pattern": re.compile(r"^seasons$"),
        "base_url": BASE_URL_F1CONNECT,
        "handler": lambda data: _extract_data(data, ("championships",)),
        "description": "Lista stagioni",
    },
    # 16. Classifiche piloti: current/drivers-championship, [year]/drivers-championship
    {
        "pattern": re.compile(r"^(?:current|\d{4})/drivers-championship$"),
        "base_url": BASE_URL_F1CONNECT,
        "handler": lambda data: _extract_data(data, ("drivers_championship",)),
        "description": "Classifica piloti",
    },
    # 17. Classifica costruttori storica: [year]/constructors-championship
    {
        "pattern": re.compile(r"^\d{4}/constructors-championship$"),
        "base_url": BASE_URL_F1CONNECT,
        "handler": lambda data: _extract_data(data, ("constructors_championship",)),
        "description": "Classifica costruttori storica",
    },
    # 18. Calendario gare: current, [year]
    {
        "pattern": re.compile(r"^(?:current|\d{4})$"),
        "base_url": BASE_URL_F1CONNECT,
        "handler": lambda data: _extract_data(data, ("races", "race")),
        "description": "Calendario gare",
    },
]


def get_data(endpoint: str, params=None, api: str = "openf1") -> pd.DataFrame:
    """
    Funzione unificata per effettuare chiamate alle API, specificando quale sorgente utilizzare.

    :param endpoint: Il nome dell'endpoint da interrogare (es. 'sessions', 'current/drivers')
    :param params: Parametri di filtro (dizionario o stringa)
    :param api: Stringa che specifica l'API da usare: 'openf1' (default) oppure 'f1api'
    :return: DataFrame pandas con i dati normalizzati
    """
    api_normalized = api.lower().replace("_", "").replace("-", "")
    if api_normalized in ("openf1", "open"):
        return get_data_openF1(endpoint, params)
    elif api_normalized in ("f1api", "f1"):
        return get_data_f1api(endpoint, params)
    else:
        raise ValueError(f"API '{api}' non riconosciuta. Valori supportati: 'openf1', 'f1api'.")



def get_data_openF1(endpoint: str, params=None) -> pd.DataFrame:
    """
    Effettua una chiamata all'API di OpenF1 per l'endpoint e i parametri specificati,
    restituendo un DataFrame pandas con i dati normalizzati.

    :param endpoint: Il nome dell'endpoint (es. 'sessions', 'car_data', 'drivers')
    :param params: Dizionario di parametri (es. {'year': 2025}) o stringa query
    :return: DataFrame pandas con i dati ricevuti
    """
    if params:
        if isinstance(params, dict):
            query = urlencode(params)
        else:
            query = str(params).lstrip("?")
        url = f"{BASE_URL_OPENF1}{endpoint}?{query}"
    else:
        url = f"{BASE_URL_OPENF1}{endpoint}"

    with urlopen(url) as response:
        data = json.loads(response.read().decode("utf-8"))

    return pd.json_normalize(data)


def get_data_f1api(endpoint: str, params=None) -> pd.DataFrame:
    """
    Effettua una chiamata all'API di F1API (f1api.dev o f1connectapi.vercel.app)
    per l'endpoint e i parametri specificati, selezionando l'URL corretto e normalizzando
    la risposta in un DataFrame pandas.

    :param endpoint: Il nome dell'endpoint (es. 'current/drivers', 'seasons', 'teams', 'circuits')
    :param params: Dizionario di parametri (es. {'limit': 50}) o stringa query
    :return: DataFrame pandas con i dati ricevuti
    """
    clean_endpoint = endpoint.strip("/")
    if clean_endpoint.startswith("api/"):
        clean_endpoint = clean_endpoint[4:].lstrip("/")

    path_only = clean_endpoint.split("?")[0]

    # Ricerca dell'URL e dell'handler corrispondente tramite pattern regex
    target_base_url = BASE_URL_F1API
    response_handler = _default_extract

    for rule in F1API_ENDPOINT_CONFIG:
        if rule["pattern"].match(path_only):
            target_base_url = rule["base_url"]
            response_handler = rule["handler"]
            break

    # Costruzione URL finale con i parametri
    if params:
        if isinstance(params, dict):
            query = urlencode(params)
        else:
            query = str(params).lstrip("?")
        separator = "&" if "?" in clean_endpoint else "?"
        url = f"{target_base_url}{clean_endpoint}{separator}{query}"
    else:
        url = f"{target_base_url}{clean_endpoint}"

    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req) as response:
        data = json.loads(response.read().decode("utf-8"))

    return response_handler(data)