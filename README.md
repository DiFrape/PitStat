# PitStat

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![pandas](https://img.shields.io/badge/pandas-2.0+-150458.svg)](https://pandas.pydata.org/)
[![Documentation: Wiki](https://img.shields.io/badge/documentation-GitHub%20Wiki-orange.svg)](https://github.com/DiFrape/PitStat/wiki)

A clean, modular, and extensible Python library and analysis toolkit designed for motorsport enthusiasts, data analysts, and researchers to fetch, explore, and analyze Formula 1 historical race results, standings, and telemetry from free public APIs.

---

## Short Description

**PitStat** provides a unified, object-oriented interface for querying Formula 1 data from multiple leading public services (including [OpenF1](https://openf1.org/), [Jolpica F1 / Ergast](https://api.jolpi.ca/ergast/f1/), [F1API.dev](https://f1api.dev/), and [F1ConnectAPI](https://f1connectapi.vercel.app/)).

Instead of dealing with disparate endpoints, raw JSON payloads, varying response structures, and HTTP boilerplates, PitStat automatically normalizes returned data into clean, structured `pandas.DataFrame` objects—ready for exploratory data analysis (EDA), data visualization, statistical modeling, and machine learning pipelines.

---

## Main Features

- **Unified Facade Interface**: Query data across providers using a simple, high-level function: `pitstat.get_data(endpoint, params=..., api=...)`.
- **Multi-Provider API Support**:
  - **OpenF1 (`api="openf1"`)**: High-frequency telemetry (speed, throttle, brake, RPM, gear, DRS), lap times, sector intervals, tyre stints, team radio audio metadata, and weather sensors.
  - **Jolpica F1 API (`api="jolpica"`)**: Ergast successor with complete historical championship data from 1950 to the present day (race results, driver/constructor standings, qualifying, sprint races, circuits, and drivers).
  - **F1API.dev (`api="f1api"`)**: Fast search queries for drivers, constructors, circuits, and current schedule tracking (`current/next`, `current/last`).
  - **F1ConnectAPI (`api="f1connect"`)**: Granular session results across the entire Grand Prix weekend (`fp1`, `fp2`, `fp3`, `qualy`, `sprint`, `race`) and career statistics.
- **Direct Pandas Normalization**: Raw API payloads are parsed and tabularized into structured `pandas.DataFrame` objects with consistent typing and indexing.
- **Robust Network & Error Handling**: Centralized request handling with configurable timeouts, descriptive User-Agent headers, URL query encoding, and custom typed exceptions (`F1APIError`, `F1RequestError`, `F1DataParseError`).
- **Extensible Object-Oriented Design**: Built upon an abstract `BaseAPI` class adhering to the Open/Closed Principle. Subclass `BaseAPI` to register and integrate new data providers seamlessly with zero modifications to existing code.
- **Interactive Workspace Ready**: Pre-configured for interactive notebooks (e.g. Jupyter notebooks), scripts, and data dashboards.

---

## Installation

PitStat requires **Python 3.9** or higher. We strongly recommend installing dependencies within a Python virtual environment (`.venv`) to keep your project environment isolated.

### 1. Clone the Repository

```bash
git clone https://github.com/DiFrape/PitStat.git
cd PitStat
```

### 2. Create and Activate a Virtual Environment (`.venv`)

**On macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**On Windows (Command Prompt):**

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

**On Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install the Library & Dependencies

You can install PitStat directly in your environment using `pip`:

**Direct installation from GitHub:**

```bash
pip install git+https://github.com/DiFrape/PitStat.git
```

**Direct installation with notebook support:**

```bash
pip install "pitstat[notebook] @ git+https://github.com/DiFrape/PitStat.git"
```

**Local standard installation (from cloned directory):**

```bash
pip install .
```

**Local development (editable mode):**

```bash
pip install -e .
```

**Local installation with optional Jupyter notebook support:**

```bash
pip install ".[notebook]"
```

Alternatively, you can install dependencies using `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

## Quick Start

You can use the high-level `pitstat.get_data` interface directly:

```python
import pitstat

# 1. Fetch telemetry and session information from OpenF1 (default provider)
sessions_df = pitstat.get_data("sessions", params={"year": 2024, "country_name": "Italy"})
print(sessions_df[["session_key", "session_name", "date_start"]])

# 2. Fetch historical race results from Jolpica (Ergast successor)
results_df = pitstat.get_data("2024/1/results", api="jolpica")
print(results_df[["position", "Driver.familyName", "Constructor.name", "points"]])

# 3. Query the next Grand Prix from F1API.dev
next_race_df = pitstat.get_data("current/next", api="f1api")
print(next_race_df)

# 4. Fetch detailed qualifying results from F1Connect
qualy_df = pitstat.get_data("2024/1/qualy", api="f1connect")
print(qualy_df.head())
```

You can also instantiate and configure specific client classes directly:

```python
from pitstat.api import OpenF1API

# Initialize client with a custom timeout of 30 seconds
openf1 = OpenF1API(timeout=30)
laps_df = openf1.get_data("laps", params={"session_key": 9158, "driver_number": 16})
print(laps_df.head())
```

---

## Documentation

Comprehensive documentation, tutorials, schema guides, and architecture references are available on our official **GitHub Wiki**:

👉 **[PitStat GitHub Wiki](https://github.com/DiFrape/PitStat/wiki)**

### Dedicated Guides:
- **[OpenF1 API Guide](https://github.com/DiFrape/PitStat/wiki/OpenF1-API)** — Real-time and historical telemetry, car metrics, lap intervals, tyre stints, and team radio.
- **[Jolpica API Guide](https://github.com/DiFrape/PitStat/wiki/Jolpica-API)** — Historical championship records (1950–present), Ergast migration, and pagination.
- **[F1API.dev Guide](https://github.com/DiFrape/PitStat/wiki/F1API-Dev)** — Fast entity search and upcoming/recent race schedules.
- **[F1Connect API Guide](https://github.com/DiFrape/PitStat/wiki/F1Connect-API)** — Granular Grand Prix weekend sessions (FP1–3, Qualy, Sprint, Race).
- **[Architecture & Extensibility](https://github.com/DiFrape/PitStat/wiki/Architecture-and-Extensibility)** — OOP design overview and registering custom API providers.

---

## Notes & Legal Disclaimer

- **Trademarks**: Formula 1, Formula 1 Grand Prix, Formula 1 Pit Stat, Formula 1 connect, F1API, Formula 1 API, F1Connect, F1ConnectAPI, F1Connect-API, and related marks are registered trademarks or service marks of their respective owners.
- **Non-Affiliation**: This project is an independent open-source software project and is not affiliated, associated, authorized, endorsed by, or in any way officially connected with Formula 1, the FIA (Fédération Internationale de l'Automobile), Formula One Licensing B.V., or any of their subsidiaries, affiliates, or registered trademark owners.
- **User Responsibility**: The user assumes total and sole responsibility for any inappropriate, improper, or illegal use of this software. The use of this software for malicious, fraudulent, abusive, or unauthorized purposes is strictly prohibited.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

