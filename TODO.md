# Future Implementations

## 1. SQLite Caching System

Implement a local, high-performance caching layer to prevent flooding public API providers with duplicate requests and speed up historical data analysis.

### Design Specifications

- **Storage Engine**: SQLite database stored in a project-relative path (`.cache/pitstat.sqlite`, ignored in `.gitignore`).
  - Benefits: Fast indexed lookups (B-tree), atomic reads/writes, zero filesystem clutter (no thousands of small files), and built-in SQL TTL expiration management.
- **Caching Layer**: Integrated into `BaseAPI` (`_fetch_json`) via a dedicated `CacheManager` module (`pitstat/api/cache.py`), caching raw JSON responses before DataFrame normalization.
- **Season Caching Policy**:
  - **Past Seasons** (`season < current_season`): Cached **permanently** (`expires_at = NULL`). Historical race results are treated as immutable.
  - **Current Season & Unversioned Queries**: Cached with a configurable **TTL** (default: 24 hours / 86,400s) to balance freshness with rate limits.
  - **Season Detection**: Detected via regex patterns in request endpoint URLs and query parameters (e.g. `/<year>/`, `year=<year>`), compared against `datetime.now().year` (with configurable override).
- **Control & Invalidation**:
  - `get_data(..., refresh=True)` flag to force cache bypass and refresh for any query.
  - `clear_cache(season=None, provider=None)` method on both `F1APIManager` and individual API clients.
  - Global/instance toggle `cache_enabled: bool` (default `True`).

### Database Schema

```sql
CREATE TABLE IF NOT EXISTS api_cache (
    cache_key TEXT PRIMARY KEY,       -- SHA256(provider + canonical_url + sorted_params)
    provider TEXT NOT NULL,           -- e.g. 'openf1', 'jolpica', 'f1apidev', 'f1connect'
    endpoint TEXT NOT NULL,           -- Target endpoint path
    season INTEGER,                   -- Extracted season year, NULL if unversioned
    response_json TEXT NOT NULL,      -- Raw JSON response payload
    created_at TIMESTAMP NOT NULL,    -- Unix epoch timestamp when cached
    expires_at TIMESTAMP             -- Unix epoch timestamp (NULL for permanent past season cache)
);

CREATE INDEX IF NOT EXISTS idx_cache_provider ON api_cache(provider);
CREATE INDEX IF NOT EXISTS idx_cache_season ON api_cache(season);
CREATE INDEX IF NOT EXISTS idx_cache_expires_at ON api_cache(expires_at);
```

### Implementation Checklist

- [ ] **Git Hygiene**: Add `.cache/` and `*.sqlite` to `.gitignore`.
- [ ] **Cache Module (`pitstat/api/cache.py`)**:
  - [ ] Implement `CacheManager` class with SQLite connection management and automatic table creation.
  - [ ] Implement `compute_key(provider, url, params)` hashing.
  - [ ] Implement `detect_season(endpoint, params)` regex parser.
  - [ ] Implement `get(...)`, `set(...)`, `purge_expired()`, and `clear(...)`.
- [ ] **Base API Integration (`pitstat/api/base.py`)**:
  - [ ] Add optional `cache: Optional[CacheManager]` parameter to `BaseAPI.__init__`.
  - [ ] Update `_fetch_json` to consult cache on lookup and store on response, supporting `refresh: bool`.
- [ ] **Concrete Clients (`openf1.py`, `f1api.py`, `jolpica.py`)**:
  - [ ] Add `refresh: bool = False` argument to `get_data(...)` in all concrete classes.
- [ ] **Manager Facade (`pitstat/api/manager.py`)**:
  - [ ] Initialize shared `CacheManager` instance across child clients.
  - [ ] Propagate `refresh: bool = False` through `F1APIManager.get_data(...)`.
  - [ ] Expose `clear_cache(season=None, provider=None)` on `F1APIManager`.
- [ ] **Testing & Verification**:
  - [ ] Verify cache hits return identical DataFrames to fresh network calls.
  - [ ] Verify `refresh=True` bypasses cache and updates stored entries.
  - [ ] Verify past seasons receive no expiration date and current season receives 24h TTL.
  - [ ] Verify `clear_cache` selectively removes matching entries.

## Check the validation of Wiki content
Check for every page of the Wiki content if the content is still valid and up to date. Update the content if needed.

## Look for the working system of `jolpica` APIs
Check the way the API is used in the class and confront it with the documentation.