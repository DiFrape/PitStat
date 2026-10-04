# Project Guidelines & Agent Conventions (AGENTS.md)

This document defines the project vision, architectural standards, and the operational boundaries for AI coding assistants collaborating on the **Formula 1 Data Management & Analysis** project.

---

## 1. Project Vision & Goals

- **Purpose**: A clean, modular, and open-source Python library and Jupyter workspace for the Formula 1 community to analyze historical race results, standings, and telemetry using free, public APIs (such as OpenF1, F1API.dev, and F1ConnectAPI).
- **Target Audience**: Data enthusiasts, motorsport fans, and open-source contributors worldwide.
- **International Standard**: All code, docstrings, comments, documentation, and commit messages must be in **English**.
- **Environment Agnostic**: No personal paths, local username references, or machine-specific configs should ever appear in repository files. The project must run cleanly in any standard Python environment.

---

## 2. AI Assistant Role & Decision-Making Constraints

1. **Executive & Supportive Pair Programmer**:
   - The AI agent acts strictly as an executive pair programmer assisting in writing, refactoring, testing, and documenting code.
   - **Architectural and structural ownership belongs exclusively to the developer/maintainer**.

2. **No Autonomous Initiatives**:
   - The agent must **NEVER make unilateral architectural decisions**, create unrequested structural files, or install unapproved dependencies.
   - **Strict Specifications & No Speculative Aliases**: Stick strictly to canonical, explicitly defined parameter names, endpoints, and interfaces. Never introduce unrequested shorthand aliases, informal abbreviations, or unsolicited convenience behaviors without explicit developer approval.
   - When facing technical trade-offs or design choices, the agent must **only formulate clear, reasoned proposals with pros and cons**, waiting for explicit developer approval before implementing changes.

3. **Core Scope of Assistance**:
   - **API Management**: request creation, endpoint routing, parameter validation, error handling, rate limiting, and response normalization into structured pandas DataFrames.
   - **Data Analysis**: Statistical exploration, data visualization, and notebook modeling are driven by the developer; the agent assists on technical implementation upon request.

---

## 3. Architecture & Design Principles

### 3.1 Object-Oriented Architecture (OOP)
API handling must follow a clean, modular, and extensible object-oriented design:

1. **Abstract Base Class (`BaseAPI`)**:
   - Defines the standard interface for all API clients (e.g., abstract `get_data`, URL construction, response normalization).
   - Centralizes shared concerns: session/request management, timeout configuration, custom User-Agent, parameter encoding, and standardized HTTP/network error handling.

2. **Dedicated Concrete Provider Classes**:
   - Separate, specialized client for each data provider:
     - `OpenF1API`: handles `api.openf1.org` (telemetry, laps, car data, weather, team radio, etc.).
     - `F1APIDev`: handles `f1api.dev` endpoints.
     - `F1ConnectAPI`: handles `f1connectapi.vercel.app` endpoints.
   - Each class encapsulates its own endpoint rules, regex patterns, key extraction, and specific normalization logic.

3. **Coordinator / Facade (`F1APIManager`)**:
   - Unified entry point allowing queries across available providers (e.g., `api="openf1"`, `api="f1api"`).
   - Manages client instances and provides a unified interface.

4. **Extensibility for Future Contributors**:
   - The architecture adheres to the Open/Closed Principle: adding a new data source (e.g., Ergast, FastF1 wrapper, custom endpoints) only requires subclassing `BaseAPI` and registering the new client, with zero changes to existing provider code.

### 3.2 Modular File Organization & Backward Compatibility

- **Modular Package (`f1_api/`)**:
  - `base.py`: `BaseAPI` abstract class and custom exceptions.
  - `openf1.py`: `OpenF1API` client implementation.
  - `f1api.py`: `F1APIDev` and `F1ConnectAPI` implementations.
  - `manager.py`: `F1APIManager` unified facade.
  - `__init__.py`: Clean public API exports.
- **Backward Compatibility**:
  - The root `API_Manager.py` must be maintained as a compatibility wrapper to ensure existing notebooks (like `F1_Stats.ipynb`) and legacy scripts continue working without breaking changes.

---

## 4. Coding & Style Conventions

- **Language & Runtime**: Python 3.9+.
- **Data Structures**: All data fetching methods must return structured `pandas.DataFrame` objects.
- **Type Annotations**: Comprehensive type hinting across all functions and methods (`str`, `dict`, `pd.DataFrame`, `Optional`, etc.).
- **Documentation**: Clear docstrings and comments in **English** using standard conventions (e.g., Google or Sphinx style).
- **Clean Git Hygiene**: Maintain clean `.gitignore` to prevent committing virtual environments (`.OpenF1`, `.venv`), OS metadata (`.DS_Store`), or temporary notebooks/checkpoints.
