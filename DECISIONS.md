# Design Decision Log (ADR-lite)

Every significant design decision in this project, with the reasoning and the
alternatives that were considered. Newest entries at the bottom of each section.
Format per entry: **Decision → Why → Alternatives rejected → Status.**

---

## D-001 · XAMPP → Docker (2025, rebuild)

- **Decision:** Run infrastructure (PostgreSQL) in Docker via docker-compose.
- **Why:** Reproducible environments — anyone (or any server) can bring up the
  exact same database with one command. XAMPP is a Windows-desktop dev tool,
  not something you deploy to production. Docker is the industry standard for
  packaging services.
- **Alternatives rejected:** XAMPP (not production-grade, Windows-only,
  manual setup), installing PostgreSQL natively (not reproducible, pollutes
  the host machine).
- **Status:** ✅ Done — db runs in compose, healthy.

## D-002 · PHP → FastAPI (Python)

- **Decision:** Rewrite the ingestion API in FastAPI.
- **Why:** Unifies the whole stack in one language (Python), so the API and
  the ML code can share models, utilities, and one team skillset. FastAPI
  also auto-generates OpenAPI docs (a self-documenting API contract) and has
  first-class validation via Pydantic.
- **Alternatives rejected:** Keep PHP (splits the stack into two languages),
  Flask (no built-in validation/docs, more manual wiring).
- **Status:** ✅ In use.

## D-003 · MySQL → PostgreSQL + PostGIS

- **Decision:** PostgreSQL with the PostGIS extension as the database.
- **Why:** Postgres is the most robust open-source RDBMS (strict typing,
  CHECK constraints, TIMESTAMPTZ). PostGIS adds real geospatial types so
  device locations can be stored as true geography points and queried
  spatially later (e.g. "sensors within 10 km").
- **Alternatives rejected:** MySQL (weaker constraint enforcement, weaker
  geospatial), SQLite (single-file, not a multi-service production DB).
- **Status:** ✅ Done — schema live in init.sql.

## D-004 · Validation at multiple layers (defense in depth)

- **Decision:** The same rules (e.g. temp between -80 and 80) are enforced in
  Pydantic schemas AND in DB CHECK constraints.
- **Why:** If one layer is bypassed (a bug, a manual SQL insert, a future
  second API), the other still protects data integrity. This is the
  "defense in depth" principle.
- **Alternatives rejected:** Validate only in the API (DB left unprotected),
  only in the DB (users get ugly 500 errors instead of clean 422s).
- **Status:** ✅ In place for readings.

## D-005 · SQLAlchemy models ≠ Pydantic schemas (separation of concerns)

- **Decision:** Keep database ORM models (models.py) separate from API
  request/response schemas (schemas.py).
- **Why:** The DB shape and the API contract evolve independently. The API
  must be able to hide columns (e.g. token_hash must NEVER leave the server)
  and accept fields that aren't columns (e.g. a raw token). One class doing
  both jobs leaks internals.
- **Alternatives rejected:** Single shared model class (leaks secrets,
  couples DB migrations to API versioning).
- **Status:** ✅ Pattern established.

## D-006 · Server stamps the timestamp if the device doesn't send one

- **Decision:** `ts` is optional in ReadingCreate; the server fills in "now"
  when missing.
- **Why:** ESP8266 clocks drift and may not know the real time (no RTC,
  NTP may fail). Server time is trustworthy and consistent.
- **Alternatives rejected:** Require device timestamps (unreliable hardware
  clock), always ignore device timestamps (loses info when the device DOES
  know, e.g. buffered offline readings).
- **Status:** ✅ Implemented in POST /readings.

## D-007 · Device auth token in `Authorization: Bearer` header, not body (2026-08-27)

- **Decision:** Devices authenticate via the standard HTTP Authorization
  header; the token was removed from the JSON request body.
- **Why:** (a) GET requests have no body, so body-tokens can't secure GET
  endpoints; (b) the Authorization header is the universal standard every
  tool/proxy/framework understands; (c) TLS encrypts headers, so it's safe
  in transit; (d) headers are less likely to end up in logged request bodies.
- **Alternatives rejected:** Token in JSON body (breaks on GET, non-standard),
  token in URL query string (ends up in server logs and browser history —
  a known security anti-pattern).
- **Status:** ✅ Implemented via FastAPI HTTPBearer, tested (401/404/201).

## D-008 · Store only the SHA-256 hash of tokens, never the raw token

- **Decision:** The DB column is `token_hash`; the raw token exists only in
  the response at creation time and on the device itself.
- **Why:** If the database ever leaks, attackers get hashes, not usable
  credentials. A hash is one-way — you cannot recover the token from it.
  Same principle as password storage.
- **Alternatives rejected:** Store raw tokens (a DB leak = every device
  compromised). Note: bcrypt/argon2 (slow hashes for human passwords) were
  not needed because device tokens are long random strings, not guessable
  human passwords — SHA-256 is appropriate and fast for per-request checks.
- **Status:** ✅ api/auth.py done (stdlib only), wired into POST /readings.

## D-009 · Error order in POST /readings: 404 (unknown device) before 401 (bad token)

- **Decision:** Look up the device first; unknown device → 404, then check
  token → 401, then insert.
- **Why:** You can't verify a token before knowing which device (and thus
  which hash) to check against. Guard clauses fail fast with the most
  specific error.
- **Status:** ✅ Implemented and tested.

## D-010 · ReadingResponse echoes the stored row (2026-08-27)

- **Decision:** ReadingResponse returns id, device_id, temp_c, humidity, ts,
  quality (the "echo" version), replacing the earlier minimal version
  (id, ts, quality).
- **Why:** Echoing what was stored lets the device/client confirm the server
  interpreted its data correctly (e.g. the server-stamped ts) without a
  second request.
- **Alternatives rejected:** Minimal response (less bandwidth but less
  confirmatory value; bandwidth is negligible at our scale).
- **Status:** ✅ In schemas.py.

## D-011 · Dashboard: Streamlit (2026-08-27)

- **Decision:** Build the visualization dashboard in Streamlit as its own
  service (dashboard/ directory).
- **Why:** Stays 100% in Python (one-language stack, same as D-002), is the
  fastest path from data to charts, and is ML-friendly (native support for
  dataframes/plots). Fits a learning project's pace.
- **Alternatives rejected:** React/JS frontend (new language + toolchain,
  much slower to learn), Grafana (great for ops metrics, clunky for custom
  ML prediction views).
- **Status:** ⏳ Planned — needs GET endpoints first.

## D-012 · ML: Ridge regression as the workhorse (2026-08-27)

- **Decision:** Keep Ridge regression for the 7-day min/max temperature
  prediction, trained on historical city weather data
  (data/Thessaloniki_Weather.csv). Add persistence + climatology baselines
  as honesty checks. Optionally race LightGBM later.
- **Why:** Small tabular dataset → linear models with good features beat
  complex models. The biggest accuracy wins are expected from FEATURES
  (lags, rolling windows, day-of-year seasonality), not model swaps.
  Baselines ("tomorrow = today", "tomorrow = seasonal average") keep us
  honest: if Ridge can't beat them, the model adds nothing.
- **Alternatives rejected:** Deep learning (needs far more data, opaque,
  slow to iterate), jumping straight to gradient boosting (premature —
  establish the baseline first).
- **Status:** ⏳ Planned — port temp_predictor.py logic into worker/.

## D-013 · Device registration via POST /devices, not manual SQL (2026-09-19)

- **Decision:** New devices are created through a registration endpoint.
  The API is the only door into the database.
- **Why:** Manual SQL inserts don't enforce validation, hashing, or
  defaults, and humans make typos. One endpoint = the rules run every time.
- **Alternatives rejected:** Continue manual psql inserts (fine for one test
  device, unsafe and unrepeatable beyond that), an admin CLI script (still
  a second door that can drift from the API's rules).
- **Status:** ⏳ In progress (Day 1 task).

## D-014 · Server generates device_id (UUID), caller cannot choose it (2026-09-19)

- **Decision:** DeviceCreate contains no device_id; the server generates a
  random UUID.
- **Why:** Caller-chosen IDs allow collisions and impersonation (guessing or
  overwriting another device's ID). Random UUIDs make collisions practically
  impossible and remove trust from the caller.
- **Alternatives rejected:** Caller-supplied IDs (trust problem),
  auto-increment integers (guessable/enumerable — an attacker can iterate
  device 1, 2, 3...).
- **Status:** ⏳ Being implemented.

## D-015 · Caller never supplies token or token_hash; raw token returned exactly once (2026-09-19)

- **Decision:** The server invents the token, stores only its hash, and
  returns the raw token a single time in the DeviceResponse. It can never be
  retrieved again (only re-issued/rotated).
- **Why:** (a) Server-generated tokens are guaranteed long and random —
  callers would pick weak ones; (b) show-once mirrors GitHub/AWS/Stripe API
  key UX and is possible because only the hash is stored (one-way); (c) if
  callers could supply a hash, they could replay a leaked hash to
  impersonate a device.
- **Alternatives rejected:** Caller-chosen tokens (weak secrets),
  retrievable tokens (requires storing raw tokens, violating D-008).
- **Status:** ⏳ Being implemented.

## D-016 · Skip location_point (geography) in the first version of device registration (2026-09-19)

- **Decision:** DeviceCreate v1 has no map coordinates; only the
  human-readable location text (optional).
- **Why:** Keep the first iteration small and shippable. Geospatial input
  raises real design questions (lat/lon fields vs WKT strings, validation
  ranges) that deserve their own session.
- **Alternatives rejected:** Full geo support now (slows down Day 1 for a
  feature nothing consumes yet).
- **Status:** ⏳ Deferred, revisit when the dashboard wants maps.

## D-017 · POST /devices is unauthenticated for now — KNOWN DEBT (2026-09-19)

- **Decision:** The registration endpoint requires no token (unlike every
  other write endpoint). Anyone who can reach the API can register a device.
- **Why:** Chicken-and-egg — a device comes to this endpoint to obtain its
  first token, so it cannot be asked for one. Acceptable while the API runs
  only on localhost. Explicitly logged as debt: before real deployment, add
  an admin credential (e.g. a single admin API key) to this endpoint.
- **Alternatives rejected:** Admin API key now (a second auth mechanism on
  Day 1 slows learning; nothing is deployed yet), pre-shared registration
  secret baked into firmware (worth revisiting at firmware time, Day 4).
- **Status:** ✅ Decided; debt open until pre-deployment hardening.

## D-018 · GET /readings v1: filterable via query parameters (2026-09-20)

- **Decision:** GET /readings accepts optional query parameters `device_id`
  (filter to one device) and `limit` (max rows, default 100, bounded),
  returning newest-first. User chose option B.
- **Why:** The Streamlit dashboard (its primary consumer) needs per-device
  views; returning every reading unconditionally does not scale and wastes
  bandwidth. Query params are the standard HTTP idiom for filtering reads.
  Newest-first because dashboards care about "now" most.
- **Alternatives rejected:** (A) No filters, fixed latest-100 (too rigid for
  the dashboard within days), (C) full offset/cursor pagination with counts
  (industrial-grade, premature at this data volume — revisit at hardening).
- **Status:** ✅ Implemented and tested 2026-09-20 (incl. empty-list for
  unknown device, 422 on limit=0).

## D-019 · Dashboard reads via the API, never the DB directly (2026-09-20)

- **Decision:** The Streamlit dashboard consumes GET /devices and
  GET /readings over HTTP, like any external client. User chose B.
- **Why:** Keeps the API as the single door (consistent with D-013): DB
  credentials stay in one service, response schemas guarantee secrets
  (token_hash) can never reach the dashboard, schema changes are absorbed
  in one place, and the dashboard exercises the API as its first real
  consumer. Same principle that scales to microservices
  (API-as-contract / no shared database).
- **Alternatives rejected:** Direct PostgreSQL access from Streamlit
  (second credential holder, bypasses schema filtering, couples two
  services to the DB layout, requires exposing the DB on the network once
  the dashboard moves off-machine).
- **Status:** ✅ Decided; dashboard v1 being built.

## D-020 · Aggregation runs in a separate worker service, not in the API (2026-09-22)

- **Decision:** Daily min/max/avg aggregation (readings → dht22_aggregate)
  lives in worker/, its own process, independent of the FastAPI service.
- **Why:** (in the user's own words: it's "asxeto" — unrelated — and "needs
  to work on its own either way.") (1) Separation of concerns: the API is
  request-driven (milliseconds, always available for sensors); aggregation
  is schedule-driven batch work. (2) Latency protection: batch jobs inside
  the API process would block or slow ingestion. (3) Fault isolation both
  ways: a crashing aggregator never stops ingestion; a down API never
  stops aggregation. Also enables independent scaling later.
- **Alternatives rejected:** Aggregation inside the API on a background
  thread (couples failure modes, competes for the same CPU, complicates
  deployment), aggregation at read-time on every dashboard request
  (recomputes the same numbers endlessly, slow queries at scale).
- **Status:** ✅ Decided; aggregator being built today (Day 2).

## D-021 · Aggregator computes in SQL (GROUP BY), not pandas (2026-09-22)

- **Decision:** The worker's daily min/max/avg aggregation is one SQL
  GROUP BY query executed inside PostgreSQL; only finished summary rows
  travel back (aggregation pushdown).
- **Why:** The raw readings never leave the database — at scale
  (~1,440 readings/device/day) pulling raw rows into Python to summarize
  them is the truck-load-for-one-box waste already rejected in D-018's
  limit design. Databases are purpose-built for aggregation. Also a
  deliberate learning goal: GROUP BY is the heart of SQL.
- **Alternatives rejected:** pandas groupby client-side (memory-bound,
  network-heavy; the same idiom is being learned anyway on the ML side
  with the CSV, so nothing is lost pedagogically).
- **Status:** ⏳ Being implemented in worker/aggregator.py.

## D-022 · Aggregation SQL lives in worker code, not a stored procedure (2026-09-22)

- **Decision:** The GROUP BY query is a fixed SQL string in
  worker/aggregator.py, executed via SQLAlchemy. (Raised by the user, who
  proposed a DB-side function.)
- **Why:** Logic in application code is version-controlled, diffable,
  reviewable and deployed like everything else; DB-side functions are
  state outside git that demands migration tooling to manage safely.
  Aggregation pushdown is preserved either way — GROUP BY executes inside
  PostgreSQL regardless of where the query text is stored. Only one
  writer of aggregates exists (the worker), so a stored procedure's
  centralization benefit has no consumer yet. Implemented 2026-09-22 as a
  single INSERT..SELECT..ON CONFLICT DO UPDATE (idempotent upsert; data
  never leaves the DB); worker/database.py holds engine setup only
  (no sessionmaker/get_db — that machinery is FastAPI-specific).
- **Alternatives rejected:** Stored procedure `aggregate_daily()` in
  PostgreSQL — legitimate pattern; revisit if a second service ever needs
  to trigger aggregation or if a dedicated migration workflow (Alembic)
  is adopted. Also noted: sending fixed SQL is safe; SQL injection only
  arises from gluing untrusted input into query text, which
  parameterized queries prevent (SQLAlchemy parameterizes always).
- **Status:** ✅ Decided.

## D-023 · Data storage policy: raw dataset committed, derived data ignored (2026-09-22)

- **Decision:** The raw NOAA file `data/thessaloniki_weather_raw.csv` is
  immutable ("raw is sacred": never edited or overwritten) and is committed
  to git. The cleaning step writes a derived snapshot
  `data/thessaloniki_weather_clean.csv` that stays gitignored, as do future
  model files (`*.joblib`). Before/after cleaning statistics (row counts,
  missing cells per column, duplicates removed, date gaps) are recorded in
  the cleaning decision entry as evidence. `.gitignore` changes from
  `data/` to `data/*` + `!data/thessaloniki_weather_raw.csv` (git cannot
  re-include a file inside an ignored directory, so the contents are
  ignored rather than the directory).
- **Why:** Four-question test for "belongs in git": small (2.3 MB), text
  (git diffs it efficiently), shareable (NOAA GHCN is public domain), and
  NOT regenerable from the repo (a re-download may differ because NOAA
  revises data). Committing the raw input makes the repo clone-and-run
  reproducible and pins the exact training input for the report. The clean
  file and models fail question four: the code rebuilds them, so committing
  them creates churn on every run and a "two truths" ambiguity. The story
  for the report is told by the cleaning code (in git) plus the before/after
  numbers, not by the clean file itself. Raised by the user, who asked
  whether to save intermediate data and whether to stop ignoring `data/`.
- **Alternatives rejected:** (A) keep all of `data/` ignored: reader must
  source the CSV themselves, weaker reproducibility. (C) commit raw AND
  clean: derived-artifact churn, two sources of truth. (D) Git LFS: right
  tool for files of hundreds of MB, overkill at 2.3 MB. DVC (data version
  control) deferred to hardening.
- **Status:** ✅ Decided. Implementation: user edits `.gitignore` and
  commits the raw CSV.

## D-024 · Explore in notebooks, productionize in scripts (2026-09-22)

- **Decision:** ML exploration (ML-1 inspect, ML-2 cleaning experiments,
  feature/baseline trials) happens in Jupyter notebooks under a top-level
  `notebooks/` directory (`tinkering_data.ipynb`; the two legacy notebooks
  moved there from `api/` as reference). Proven cells are ported, step by
  step, into `worker/ml_trainer.py`, which is the single source of truth
  for the raw → clean → features → train → save-model pipeline. Notebooks
  are disposable; the script must run top-to-bottom from a blank process.
  Habits adopted: "Restart Kernel → Run All" before trusting a notebook
  result; "Clear All Outputs" before committing a notebook. Proposed by
  the user.
- **Why:** Notebooks keep the dataset in memory between cells and show
  tables/plots inline, the ideal feedback loop for tinkering. But cells
  run in click order and the kernel retains every variable ever created
  (hidden state), so a notebook can "work" only thanks to a cell that was
  since edited or deleted; a script has no such trap. `.ipynb` files also
  embed outputs (the legacy notebooks are 3.1 MB and 0.8 MB, mostly
  outputs), which bloats git and makes diffs unreadable. Notebooks belong
  to no service, hence their own directory rather than `api/`.
- **Alternatives rejected:** Scratch script `worker/explore.py` (Claude's
  first suggestion): safe but slow feedback loop, re-reads the CSV on
  every run. REPL: nothing saved. Notebook as the production artifact
  (papermill/nbconvert): hidden-state risk in production; unnecessary.
  Automated output stripping (nbstripout) deferred to hardening.
- **Status:** ✅ Decided. Legacy `api/temp_predictor.py` moved to
  `worker/temp_predictor.py` as the porting reference.

## D-025 · Training data source: Open-Meteo ERA5-Land reanalysis replaces NOAA GHCN (2026-09-22)

- **Decision:** The ML model trains on daily reanalysis data from the
  Open-Meteo Historical Weather API (archive-api.open-meteo.com), model
  ERA5-Land (~9 km grid, one consistent model 1950→present), for
  Thessaloniki city centre (lat 40.64, lon 22.94), timezone auto
  (Europe/Athens), 1950-01-01 → ~one week before download. Variables:
  temperature_2m_{mean,max,min}, relative_humidity_2m_{mean,max,min}.
  Saved as `data/thessaloniki_openmeteo_raw.csv` (immutable, committed per
  D-023). The NOAA file `data/thessaloniki_weather_raw.csv` is kept for a
  later validation: mean absolute difference between reanalysis and the
  station thermometer on the ~14,000 days NOAA actually measured TMAX
  (optionally with a second small download at the airport coordinates
  40.52/22.971 so the comparison is same-cell).
- **Why:** ML-1 inspection of the NOAA GHCN file (21,211 rows, 1964→2025)
  showed the two TARGET columns are the holiest: TMAX 6,894 missing
  (32.5%), TMIN 8,787 missing (41.4%), TAVG 0 missing (flag `H` = derived
  from hourly reports, a different pipeline). Holes are NOT concentrated
  in the early era; they GROW over time: 2013 has 295/365 TMAX missing,
  2014 has 355/365, 2015–2025 run 50–60% missing. Plus two whole years
  absent (1972, 2005) and sparse rows 1964–1974. No duplicate dates, no
  9999 sentinels, plausible ranges (TMAX max 44.0, TMIN min −12.8). Every
  in-place cure fails: dropping NaN rows discards half the modern era;
  forward-fill (the v1 approach) turns 40% of targets into stale copies,
  which also inflated v1's measured accuracy (~1 °C day-1, ±3 °C day-7,
  partly on copied targets); interpolation is fiction across 2014.
  Better data beats cleverer cleaning. Reanalysis is gap-free by
  construction. City centre (not the airport) because the model should
  mimic the sensor's location (D-026). 1950 rather than 1964: download the
  maximum, slice in code; pre-1979 reanalysis is fuzzier (few
  observations assimilated) and the climate has warmed ~1–1.5 °C, so
  climatology features should use a recent window (e.g. WMO normal
  1991–2020) — a feature-step decision. ERA5-Land chosen over "Best match"
  (stitches models, discontinuity at 2017) and over ERA5 from 1940
  (coarser 25 km grid for ten fuzzy years).
- **Alternatives rejected:** (A) keep NOAA, interpolate + drop 2013–2014:
  too many invented values. (B) impute TMAX/TMIN from complete TAVG:
  training targets would themselves be model outputs (error stacking).
  (C) switch target to TAVG: changes the project's promise. NOAA GSOD
  (daily values derived from hourly airport reports, real measurements,
  likely complete): kept as the upgrade path if the report wants station
  data; costs °F conversion, 9999.9 sentinels, yearly files. Meteostat:
  silently fills gaps from model data. Greek sources (HNMS, meteo.gr):
  access by request, too slow. Trade-off accepted: reanalysis is modelled
  on a grid, not a thermometer; extremes slightly smoothed; coastal city
  centre maps to the nearest ERA5-Land land cell.
- **Status:** ✅ Decided. Download pending. Cleaning decision
  (drop/interpolate) is now expected to be trivial; verify with the same
  ML-1 checks on the new file.
- **Note (2026-09-22, after download):** ERA5-Land snapped the requested
  40.64/22.94 to grid-cell centre 40.70/22.90 (elevation 32 m, ~7 km NNW,
  inland). File: 28,017 daily rows 1950-01-01 → 2026-09-15, one per
  calendar day (gap-free confirmed). Three metadata lines precede the
  header (`skiprows=3`). Row 1 has NaN mean temp/humidity (no full first
  day). Column names carry units, e.g. `temperature_2m_max (°C)`.

## D-026 · Inference inputs are the sensor's daily aggregates; training features restricted to sensor-observable variables (2026-09-22)

- **Decision:** On prediction day the model is fed rows from
  `dht22_aggregate` (temp max/min/avg, humidity max/min/avg per day) plus
  calendar features derived from the date. Therefore the training data
  (D-025) carries only those same variables; precipitation, weather code
  and apparent temperature were deliberately NOT downloaded. Rule:
  training features ⊆ sensor columns (a subset is fine; the model must
  never need something the sensor cannot provide). Raised by the user
  ("we don't need precipitation, the DHT sensor only gets temp and
  humidity").
- **Why:** Feature availability at inference time / train–serve skew: a
  model trained on an input that is unavailable when predicting cannot be
  served. Path 2 keeps the system coherent (sensor → aggregate → model →
  prediction → dashboard) instead of making the sensor decorative. The
  historical reanalysis acts as a stand-in for the sensor's non-existent
  multi-decade history. Known caveat, logged not solved: domain shift
  between a balcony DHT22 and a 9 km reanalysis cell (sensor in sun reads
  hot); mitigation planned once months of sensor data exist: compare on
  overlapping days and correct the offset (or recalibrate).
- **Alternatives rejected:** Path 1: predictor fetches recent city weather
  from Open-Meteo at inference time (precipitation could stay; sensor
  becomes dashboard-only; hollow IoT story). Keeping precipitation as a
  feature: weak signal for temperature anyway, most information is in
  recent temperatures and day-of-year.
- **Status:** ✅ Decided.

## D-027 · Deadline re-plan: firmware first (timeboxed), scope cut for Sunday 2026-09-27 (2026-09-23)

- **Decision:** The project is presented finished on Sunday 2026-09-27,
  and the 2,500-word report is due the same day. New build order:
  Wed 09-23 firmware (FW-1..FW-7) → Thu 09-24 ML block (ML-1..ML-7 in one
  session) → Fri 09-25 predictions (`worker/predictor.py`,
  `GET /predictions`, dashboard v2) → Sat 09-26 buffer + demo rehearsal.
  The report is written in parallel (outline + related work Thu,
  architecture + design decisions Fri, finish Sat). Firmware is
  TIMEBOXED: if readings are not flowing by Thursday 12:00, switch to
  plan B, a Python simulator script that POSTs realistic readings to the
  API, and move on to ML. Cut from scope and moved to the report's
  "Future work": Docker for api/worker/dashboard, nginx + TLS,
  duplicate/idempotent ingestion, automatic scheduler (scripts run by
  hand for the demo), NOAA-vs-reanalysis validation, LightGBM comparison,
  dashboard polish. Pace: full teaching mode is kept everywhere (user's
  choice), protected by strict scope and the timebox. The pending
  cleaning decision (previously "D-027 pending") becomes D-028.
- **Why:** Risk-first scheduling. Hardware is the only component whose
  failures can lie outside the user's control (dead board, charge-only
  cable, USB driver, Windows firewall, WiFi), and a broken part needs a
  shop: surprises must surface on Wednesday, not Saturday. The sensor
  accumulates real data while everything else is being built, so every
  extra day of readings improves the demo; the v1 feature set uses a
  30-day rolling mean, so inference will need a cold-start plan anyway
  (a Friday decision), and more real days make it easier. Working
  firmware completes the first end-to-end slice (sensor → API → DB →
  aggregates → dashboard), a presentable safety net if ML runs late. ML
  is the lower-risk half: pure software, gap-free data already downloaded
  (D-025), model trained before in v1. ML still must not slip past
  Friday: it is the "Predictor" in the project's name. Full teaching is
  kept because the user values understanding over speed and must defend
  every part in the presentation Q&A. Raised by the user ("should we
  first create the firmware, test it, and have something presentable").
- **Alternatives rejected:** (B) ML first, firmware Friday: hardware
  surprises found late, only ~1–2 days of real sensor data by Sunday.
  (C) Simulator only, no hardware: safest, but hollows out the IoT half
  of the story (the sensor → model path of D-026). "Deadline mode"
  (Claude shows firmware/plumbing/dashboard code, user explains it back):
  faster, declined by the user in favour of full teaching. The original
  4-day plan (aggregator + ML, then predictions + dashboard v2, firmware
  LAST) put the riskiest component at the end.
- **Status:** ✅ Decided. Hardware in hand: ESP8266 (NodeMCU), DHT22 +
  jumper wires, USB data cable. Arduino IDE not yet installed on this
  laptop (FW-1).

## D-028 · Firmware v2: adapt the 2024 sketch, secrets in a gitignored header, new device, 60 s deep-sleep cycle (2026-09-23)

- **Decision:** The FastAPI-era firmware is the 2024 sketch
  `firmware/esp8266/esp8266.ino` adjusted in place, not rewritten, and
  the planned sensor-only test sketch is skipped (user's call: "lets just
  adjust old firmware"). Changes: every per-installation value (WiFi SSID
  and password, API URL, device_id, device token) moves to
  `firmware/esp8266/secrets.h`, pulled in with `#include "secrets.h"` and
  gitignored. The POST body becomes JSON
  `{"device_id", "temp_c", "humidity"}` (the ReadingCreate contract; `ts`
  is left to the server per D-006), built by String concatenation.
  Headers: `Content-Type: application/json` and
  `Authorization: Bearer <token>` (D-007). `http.end()` before sleeping.
  Cadence: one reading every 60 s via deep sleep (`ESP.deepSleep` counts
  microseconds) with the D0→RST wake wire, which is unplugged for every
  upload. The real sensor is registered as a NEW device via POST /devices.
- **Why:** The old sketch already holds WiFi-connect and DHT22-read code
  that worked in 2024, and it prints the sensor values to Serial before
  any network activity, so most of the test sketch's isolation benefit
  is kept. secrets.h: the repo is on GitHub and git never forgets (a
  deleted file stays in history, as the recovered 2024 wiring photo
  showed), so the WiFi password and device token must never be
  committed; this applies the "never hardcode secrets" principle. 60 s
  gives ~1,440 readings/day, the volume the aggregator was designed
  around (D-021), and a visible update every minute in the demo. Deep
  sleep (user's choice over the recommended always-awake `delay()`):
  battery-ready if the sensor ever runs off-grid outdoors, continuity
  with the 2024 design, and every cycle starts from a clean reboot so no
  state accumulates. Accepted costs: WiFi reconnects on every wake
  (effective interval ≈ 60 s + a few seconds), one line of boot noise per
  cycle in the Serial Monitor (the 74880-baud ROM message), and the
  D0→RST wire must be removed for uploads. New device: keeps real data
  separate from test rows (duplicate POSTs, the −80/100 boundary test)
  in charts, aggregates and ML inputs.
- **Alternatives rejected:** Separate sensor-only test sketch first (more
  isolation, slower). Always-awake loop with `delay(60000)` (simpler on
  USB power; recommended, not chosen). 10 s interval (six times the rows
  daily aggregates need) and 5 min (demo chart barely moves). Reusing
  test device test-3 (real and test data mixed). Secrets hardcoded in the
  .ino (would leak to GitHub). ArduinoJson library (overkill for three
  fields; revisit if the payload grows). WiFiManager captive portal or
  flash-stored config (overkill for one device).
- **Status:** ✅ Decided. Implementation in progress (FW-3..FW-5).
  Deep-sleep clause superseded by D-029 (stay awake on USB power).

## D-029 · v1 firmware stays awake on USB power; deep sleep deferred to a battery version (2026-09-23)

- **Decision:** Reverses the deep-sleep clause of D-028. This first
  firmware version targets a mains-powered (USB) sensor, e.g. on a
  balcony: the board stays awake and waits between readings with
  `delay()` (60 s, unchanged). `ESP.deepSleep` is removed and the D0→RST
  wake wire is no longer used. Deep sleep returns in a later
  wireless/battery version (report: Future work). Raised by the user.
- **Why:** Deep sleep only pays off on batteries. On USB power it brings
  costs and no benefit: the D0→RST wire (unplugged for every upload), a
  WiFi reconnect of a few seconds every cycle, boot noise in the Serial
  Monitor every minute, and an interval that drifts to ~63–65 s. Staying
  awake keeps WiFi connected, gives the loop's reconnect check a real
  job, and keeps an exact 60 s cadence. Principle: design for the
  deployment you actually have, and version the firmware when the
  deployment changes. Consequence: the chip now runs for days without
  rebooting, so resources must be released every cycle (`http.end()`);
  deep sleep's reboot used to hide that.
- **Alternatives rejected:** Keep deep sleep (D-028 as first decided).
- **Status:** ✅ Decided. Supersedes the deep-sleep clause of D-028.

## D-030 · ESP8266 uses a static IP instead of DHCP (2026-09-23)

- **Decision:** Before joining WiFi, the firmware sets a fixed address
  for itself with `WiFi.config(ip, gateway, subnet, dns)`: an unused
  address high in the home subnet, the router as gateway and DNS, and
  the subnet mask read from the PC's `ipconfig`. The concrete values live
  only in the firmware, never in documentation. The WiFi 6 compatibility
  lines `WiFi.mode(WIFI_STA)` + `WiFi.setPhyMode(WIFI_PHY_MODE_11G)` were
  suggested but turned out unnecessary: the static IP alone got the first
  request through (uvicorn logged the board's POST /readings → 422,
  expected with the placeholder device id). Kept in reserve if -1 errors
  reappear.
- **Why:** On the home WiFi 6 (802.11ax) router, the ESP8266 (2014,
  b/g/n only) sat on status 7 (connecting) for minutes, and when it
  finally reported "connected" it held a 169.254.x.x address, the
  link-local fallback a device gives itself when the router's DHCP never
  answers. With such an address the board is on the WiFi but cannot
  reach the PC (httpCode -1). A static IP skips DHCP entirely and also
  makes each connect faster. Ruled out before deciding: a password typo
  (secrets.h compared byte-for-byte with the phone's saved network), WPA3
  (the router reports WPA/WPA2-Personal), and hidden characters in
  secrets.h. The chosen address was verified free with `ping`
  (destination host unreachable).
- **Alternatives rejected:** DHCP reservation in the router (the proper
  fix, but useless while DHCP itself doesn't answer the board); debugging
  router settings or firmware (hours, not this week). Known risk: the
  router could lease the same address to another device someday;
  mitigated by picking a high address. Related fragility: the PC's own
  address (in API_URL) comes from DHCP and could change after a router
  reboot; a reservation for the PC is Future work.
- **Status:** ✅ Decided and verified 2026-09-23 ~23:55 (the board reached
  the API).

## D-031 · Going public: private notes excluded, author emails normalized, history rewritten once (2026-09-24)

- **Decision:** Before the repository is made public: (1) `CLAUDE.md`,
  the private mentoring / working-notes file, is untracked, gitignored
  (and also listed in the local-only `.git/info/exclude` as a safety
  net), and removed from every past commit with `git filter-repo`;
  (2) every commit's author and committer email is rewritten to the
  GitHub no-reply address (via a mailmap), and the repo-local git config
  uses that address from now on; (3) the rewritten history is
  force-pushed once, while the repo is still private and has a single
  user. A full backup (git bundle of all refs + an archive of the working
  folder) was taken first. The README credits the data sources
  (Open-Meteo CC BY 4.0, Copernicus ERA5-Land, NOAA GHCN-Daily), and
  `firmware/esp8266/secrets.example.h` documents which values the
  gitignored `secrets.h` must hold. Mentions of Claude (the AI mentor)
  in this log are kept on purpose: they record the working mode, in
  which the user writes and runs the code while Claude explains,
  reviews, and supplies short snippets for specific fixes (D-027 records
  that a faster mode, with Claude supplying ready-made code, was
  declined).
- **Why:** A public repo exposes its entire history, not only the latest
  files: deleting a file in a new commit leaves it readable in the old
  ones. CLAUDE.md holds personal learning notes that are not project
  documentation, and a personal email address in commit metadata gets
  harvested. The pre-publication audit found no credentials in code or
  history (secrets are read from env vars / a gitignored header; the one
  `.env` ever committed held placeholder values; old sketches and PHP
  files contain placeholders only). Rewriting history is only safe
  before anyone else has cloned; that window closes the moment the repo
  goes public. Open-Meteo data is licensed CC BY 4.0, so publishing the
  CSV requires attribution.
- **Alternatives rejected:** (B) publish CLAUDE.md as is (transparent
  about AI-assisted learning, but exposes personal notes). (C) strip the
  notes from the current version only (old versions remain in history).
  Restarting from a single fresh commit (would erase the 2023→2026
  project timeline the report can cite). Removing every mention of the
  AI mentor from this log (done briefly, then reverted at the user's
  request: the mentions document how the work was done).
- **Status:** ✅ Decided and executed 2026-09-24.

## D-032 · ML-2 cleaning: drop the one incomplete day; column names mirror the sensor table (2026-09-24)

- **Decision:** Cleaning of `data/thessaloniki_openmeteo_raw.csv` is three
  steps: (1) rename the columns to exactly the names of
  `dht22_aggregate` (`time → date`, `temperature_2m_{max,min,mean} →
  temp_c_{max,min,avg}`, `relative_humidity_2m_{max,min,mean} →
  humidity_{max,min,avg}`); (2) `dropna()` to remove rows with any
  missing value; (3) make `date` the index (a time series). No
  interpolation, no filling.
- **Evidence (before → after):** 28,017 rows → 28,016 rows. Missing
  cells: 2 → 0, both on 1950-01-01 (the mean temperature and mean
  humidity of the first day, which the source cannot compute because the
  record starts that day). Duplicate dates: 0. Every year has 365/366
  days (2026: 258 days, 1 Jan → 15 Sep, the download cut-off). Ranges
  are physically plausible: temperature −16.1 to 43.7 °C, daily mean
  humidity 28–98 %.
- **Why:** With one incomplete day at the very start of a 76-year series,
  dropping is lossless in practice and invents nothing; the cleaning
  problem that forced D-025 (32–41 % missing targets in the NOAA file)
  does not exist in reanalysis data. `dropna()` rather than deleting
  "row 0" by position stays correct if a re-download also ends with an
  incomplete last day. Identical names in training data and in the
  sensor's aggregate table let the predictor feed sensor rows to the
  model without a renaming step, removing a whole class of train–serve
  mismatch bugs (D-026).
- **Alternatives rejected:** Interpolating the two cells (no value in
  inventing data for one day in 28,000). Keeping the long source names
  (units and a `°` inside names, error-prone to type). Short custom names
  (`temp_max`, …; the user's first version): would require a
  translation step at inference.
- **Status:** ✅ Decided 2026-09-24 (user chose to match the sensor
  names). Implemented in `notebooks/tinkering_data.ipynb`; to be ported
  to `worker/ml_trainer.py` (D-024).

## D-033 · Training window: the satellite era, 1979 onward (2026-09-24)

- **Decision:** The model learns from days dated 1979-01-01 onward
  (about 17,400 rows up to the 2026-09-15 download cut-off). The full
  1950–2026 table stays intact during feature engineering (ML-3). The
  window is applied only at the train/test split (ML-4), e.g.
  `weather.loc["1979":]`, so lag and rolling features for early January
  1979 can still look back into December 1978.
- **Why:** A reanalysis is only as good as the observations fed into it.
  From 1979 onward, satellite observations enter ERA5, so the earlier
  decades rest more on the model and less on measurement. The region has
  also warmed by roughly 1–1.5 °C since 1950; the oldest decades would
  pull the model's idea of "normal" toward a colder past. About 17,400
  daily rows is far more than a Ridge model with around 20 inputs needs,
  so dropping 1950–1978 costs little.
- **Alternatives rejected:** (B) 1991 onward, matching the WMO 1991–2020
  climate normal: closest to today's climate, about 13,000 rows; a
  defensible choice, kept as a comparison. (C) Every year from 1950
  (28,016 rows): the most data, but it mixes the less-constrained
  pre-satellite era and a colder climate into training.
- **Status:** ✅ Decided 2026-09-24 (user took the recommendation, A).
  Treated as a hypothesis: in ML-6 the model can be re-fitted on B and C
  and scored on the same test period; if another window wins clearly, a
  new entry supersedes this one.

## D-034 · Targets: temperature max and min for days 1–7; humidity is an input only (2026-09-24)

- **Decision:** The model predicts 14 numbers per evening: `temp_c_max`
  and `temp_c_min` for each of the next 7 days (columns
  `target1_max … target7_max` and `target1_min … target7_min`, built with
  `shift(-n)`). Humidity (max/min/avg) is used only as an input feature.
- **Why:** This matches the project goal and v1, so the report can compare
  against v1's benchmark. It keeps the serving work small (14 numbers in
  the API response, two forecast lines on the dashboard). Relative
  humidity is harder to forecast from these inputs: it largely mirrors
  temperature and depends on rain and wind, which are deliberately not in
  the dataset (D-026). The DHT22 is also less accurate and less stable on
  humidity than on temperature, and the gap between a balcony and a 9 km
  grid cell is larger for humidity.
- **Alternatives rejected:** (B) Also predict humidity max/min (28
  targets): a fuller demo, but it doubles the evaluation, API and
  dashboard work for a weaker forecast. Kept as a stretch goal / Future
  work; adding it is two lines in the target step.
- **Status:** ✅ Decided 2026-09-24 (the user wrote temperature-only
  targets in the notebook, i.e. option A).

## D-035 · Model selection by time-series cross-validation; the test set stays sealed (2026-09-24)

- **Decision:** The **test** set is 2022 → end of data and is used once,
  at the end, to report the final score (same test period as v1, so the
  report comparison stays fair). The **development** data, 1979–2021, is
  used to compare feature sets and settings with time-series
  cross-validation: scikit-learn `TimeSeriesSplit`, 5 folds, expanding
  window (each fold trains on all earlier years and validates on the next
  block), with `gap=7` rows between each training block and its
  validation block. A feature set's score is its MAE per horizon
  (day 1–7), averaged over the 5 folds; the spread across folds is noted
  too. Never shuffled.
- **Why:** A single validation period gives one score that can be the
  luck of those particular years (one hot summer, one mild winter).
  Averaging over five successive periods gives a steadier comparison and
  shows how much the score varies. The expanding window respects time:
  the model is never judged on days earlier than the days it learned
  from. `gap=7` because the targets reach 7 days ahead: without it, the
  targets of the last training rows would fall inside the validation
  block. Keeping the test set sealed avoids "overfitting to the test
  set", which would make the final number optimistic. Ridge trains in
  milliseconds, so five fits per experiment cost nothing.
- **Alternatives rejected:** (A) One validation slice, 2016–2021:
  simpler, but a comparison based on a single period is noisier. (B)
  Keep the two-way v1 split and compare feature sets on the test set:
  optimistic final number.
- **Open (decided in ML-6):** whether the chosen model is refitted on all
  development data before the single test run, and whether the deployed
  model is refitted on all data.
- **Status:** ✅ Decided 2026-09-24 (user chose C over the recommended A).

## D-036 · Predictions are stored in the database, not computed on demand (2026-09-24)

- **Decision:** `worker/predictor.py` runs once a day after the
  aggregator. It computes each device's 7-day forecast from that device's
  daily aggregates and upserts it into a new `prediction` table
  (`ON CONFLICT DO UPDATE`, the same pattern as the aggregator, D-021/
  D-022). `GET /predictions` only reads that table. The table's exact
  shape is decided when it is built.
- **Why:** The model's inputs change once per day, so the forecast is the
  same all day; computing it on every request repeats identical work.
  Stored forecasts keep a history, which allows comparing what was
  predicted with what the sensor later measured: a real-world evaluation
  for the report and the demo. Roles stay clean: the worker does ML and
  writes to the database; the API only serves data (in the spirit of
  D-019) and needs no scikit-learn, no model file and no feature code
  from `worker/`.
- **Known caveat:** a stored forecast goes stale if the predictor is not
  run, and there is no automatic scheduler for the demo (D-027). The
  dashboard shows the date the forecast was issued.
- **Alternatives rejected:** (B) On demand inside the API: always fresh
  and no new table, but no forecast history, and the API would depend on
  ML libraries, the model file and the worker's feature code. (C) Hybrid,
  computing on demand and caching: the complexity of both, with no
  benefit at this scale.
- **Status:** ✅ Decided 2026-09-24 (user accepted the recommendation,
  A). Closes the "store vs on-demand" question open since Day 1. Built on
  Day 3 (Friday).

## D-037 · Feature selection: automated forward selection, scored by the time-series CV (2026-09-24)

- **Decision:** The goal is the most accurate model. The user writes a
  list of candidate features, and scikit-learn's
  `SequentialFeatureSelector` picks the subset: `direction="forward"`,
  `cv` = the D-035 `TimeSeriesSplit` (5 folds, `gap=7`),
  `scoring="neg_mean_absolute_error"` (MAE averaged over the 7 horizons
  of the multi-output Ridge), `n_features_to_select="auto"` with
  `tol=0.01` (stop when the next feature improves the average MAE by less
  than 0.01 °C). It runs separately for the max targets and the min
  targets, on the development data (1979–2021) only.
- **Rules for candidates (correctness, not preference):** built only from
  the sensor's columns (temperature and humidity max/min/avg) and the
  date (D-026); backward-looking only (`shift(+n)`, `rolling`), never
  future information.
- **Why:** Automatic and reproducible, and it removes personal bias from
  the choice. Forward selection is a standard, explainable method. The
  `tol` stop rule keeps the model small and avoids adding features that
  help only by chance.
- **Alternatives rejected:** (B) Manual, one feature at a time: best for
  learning, but slower and open to bias. (C) Every combination: over a
  million subsets for 20 candidates; slow, and the winner would be mostly
  luck.
- **Known caveats:** The selector tries many subsets, so its best CV
  score is optimistic; the reported score comes only from the sealed test
  set (D-035). The selector returns the final set, not the order in which
  features were added.
- **Status:** ✅ Decided 2026-09-24 (user chose A).

## D-038 · Ship the v1-recipe model now; serving first, improve later (2026-09-24)

- **Decision:** The model we have is the one we serve: 14 Ridge models
  (`alpha=0.1`), 7 for the max targets and 7 for the min targets. All 14
  use the same 4 v1 predictors: `temp_c_max`, `temp_c_min`,
  `avg_max_month`, `daily_avg_offset_max`. The user's notebook marks this
  set "#Best results" for min as well. They are trained on Open-Meteo
  from 1979 onward and saved with `joblib` to `models/ridge_v1.joblib`,
  one dictionary holding the models (day order 1–7) and their predictor
  lists. The file (6.6 KB) is committed (644014c), so a fresh clone can serve forecasts without retraining. Work moves
  straight to serving: the `prediction` table, `worker/predictor.py`,
  `GET /predictions` and dashboard v2.
  Model improvements come after the full pipeline works end to end.
- **Why:** The deadline is Sunday 2026-09-27. A working end-to-end system
  (sensor → API → aggregate → prediction → dashboard) is worth more for
  the demo than a better model with no way to serve it. The v1 recipe
  already gives MAE ~1.6 °C (day 1) to ~2.9 °C (day 7) for max
  temperature.
- **Split used:** max models: train 1979-01-01 → 2024-12-31, test
  2025-01-01 onward (the user moved the split in the notebook, replacing
  D-035's 2022+ test period). The saved min models still use the older
  split: train up to 2021-12-31 (from 1950), test 2022 onward, day-1 MAE
  1.16 °C. Aligning the two is on the "improve later" list.
  → Aligned 2026-09-27 (see D-044): the min models also train on
  1979–2024 and test on 2025 onward.
- **Supersedes / defers:** D-037 (forward feature selection) and the
  cross-validation model selection in D-035 are deferred to "if time
  allows" or the report's Future work. D-033 (1979 window) and D-034
  (targets) still hold.
- **Alternatives rejected:** Finishing the 5-step road to the best model
  first (feature search, alpha tuning), which would push serving into
  Saturday's buffer.
- **Status:** ✅ Decided 2026-09-24 (user).

## D-039 · The `prediction` table: one row per device, issue day and target day (2026-09-24)

- **Decision:** A new table `prediction` in "long" format. Each predictor
  run writes 7 rows per device, one per forecast day. Columns:
  `device_id` (UUID, FK to `device`, `ON UPDATE CASCADE` / `ON DELETE
  RESTRICT` like the other tables), `based_on_date` (DATE, the day of the
  data the forecast was made from), `target_date` (DATE, the day being
  forecast), `temp_c_max` and `temp_c_min` (NUMERIC(5,2), the predicted
  values, named like the `dht22_aggregate` columns), `model`
  (e.g. `ridge_v1`) and `created_at` (TIMESTAMPTZ, default `NOW()`).
  Primary key = (`device_id`, `based_on_date`, `target_date`). CHECKs:
  `target_date > based_on_date`, and both temperatures above −100 and below 80
  (the sensor table uses −80..80). No extra index: the primary key's index already serves
  "latest forecast for this device".
- **Why:** One row per forecast day is the standard layout for forecast
  data. The dashboard plots `target_date` directly. Joining `target_date`
  to `dht22_aggregate.date` compares each forecast with what the sensor
  later measured, which is the real-world evaluation promised in D-036.
  The primary key is the upsert key: re-running the predictor on the same
  day overwrites its 7 rows instead of duplicating them (the pattern from
  D-021/D-022). `model` shows which model made which forecast
  once v2 exists. The CHECKs are defense in depth: an off-by-one date
  bug or an absurd prediction fails loudly instead of being stored.
- **Renamed 2026-09-25:** `issued_date` → `based_on_date`. The user
  found `issued_date` next to `created_at` confusing: both sounded like
  "when the forecast was made". The new name says what the column means:
  the forecast is based on sensor data up to this day. `target_date` and
  `created_at` keep their names. The table was empty, so the live column
  was renamed with `ALTER TABLE … RENAME COLUMN`; the primary key and
  CHECK followed automatically.
- **Alternatives rejected:** (B) One row per run with 14 columns
  (`max_d1` … `min_d7`): one INSERT per run, but charting and comparing
  with actual values means unpacking 14 columns, and changing the number
  of forecast days means changing the table.
- **Status:** ✅ Decided 2026-09-24. The user accepted the recommendation
  (A): "prediction sounds good".

## D-040 · GET /predictions: latest forecast by default, older ones by date (2026-09-25)

- **Decision:** `GET /prediction` (singular path, as written in the
  code) takes a **required** `device_id` and an
  optional `based_on_date`. Without a date, it returns the 7 rows of that
  device's newest forecast, found with `MAX(based_on_date)`. With a date, it
  returns the 7 rows of the forecast made on that day. Rows are sorted by
  `target_date` (day 1 → day 7). A device or date with no forecast returns
  an empty list, not 404 (same rule as GET /readings). The response schema
  `PredictionResponse` returns `device_id`, `based_on_date`, `target_date`,
  `temp_c_max`, `temp_c_min`, `model` and `created_at`.
- **Why:** The dashboard's normal question is "what is the forecast right
  now?", so the API answers it directly and the dashboard stays simple
  (D-019). Old forecasts matter because storing them is what makes a
  real-world check possible, comparing a past forecast with what the sensor
  later measured (D-036). Adding the optional date costs one `if`, the same
  "conditionally filter" pattern as GET /readings. `device_id` is required
  because a forecast only makes sense for one sensor.
- **Alternatives rejected:** (A) Latest only: simplest, but old forecasts
  would be unreachable. (B) A plain list like GET /readings (optional
  device, `limit`, newest first): the dashboard would receive many
  forecast runs mixed together and have to find the newest one itself.
- **Scope:** The API supports old forecasts now. The dashboard's "pick an
  old date" control comes after the main pipeline works (Saturday buffer
  or Future work).
- **Status:** ✅ Decided 2026-09-25. The user asked whether the UI should
  show old forecasts, which led to option C, and chose C.

## D-041 · Model v2: drop the 30-day features so a forecast needs only one day of sensor data (2026-09-25)

- **Decision:** Remove `avg_max_month` (30-day rolling mean of max) and
  `daily_avg_offset_max` (today's max minus that mean) from the model's
  inputs. Model v2 uses only **one day** of data: the six daily sensor
  columns `temp_c_max`, `temp_c_min`, `temp_c_avg`, `humidity_max`,
  `humidity_min`, `humidity_avg`, the user's choice when retraining. The
  same six feed all 14 Ridge models (7 max, 7 min), and they have exactly
  the same names as the `dht22_aggregate` columns, so the predictor can
  pass an aggregate row straight to the model. The user saved it over
  `models/ridge_v1.joblib`: the file keeps the v1 name but holds v2 (the
  original v1 is in git history, commit 644014c). The predictor reads
  one day of `dht22_aggregate` per device.
- **Result (test period, MAE °C):** max days 1–7: 1.62, 2.19, 2.44, 2.54,
  2.66, 2.73, 2.74 (v1: 1.62 … 2.91). Min day 1: 1.10 (v1: 1.16). v2
  matches v1 on day 1 and is **better** from day 3 onward. Adding humidity
  and the daily average made up for the lost 30-day mean.
- **Why:** Cold start. When `worker/predictor.py` was designed, the
  balcony sensor had 23 readings and no complete day, and v1 needs 30
  days of daily max/min for its rolling-mean features: no forecast before
  late October. Changing the model so it needs only what the sensor
  already provides is the simplest fix, with no second data source and no
  extra code in the predictor. It extends D-026 (features only from
  sensor columns) to "features only from history the sensor has".
- **Cost / later:** v2 has no feature for the time of year. Day-of-year
  features (sine/cosine of the date) could add that without needing any
  history. Listed as a later improvement.
- **Alternatives rejected:** (A) Fill missing days from Open-Meteo's API
  at prediction time: sensible forecasts at once, but it mixes two data
  sources and adds download and merge code. (B) Average over whatever
  sensor days exist: meaningless inputs until about 30 days of data.
  (C) Wait for 30 sensor days: nothing to demo before late October.
- **Supersedes:** the predictor list in D-038.
- **Status:** ✅ Decided 2026-09-25 (the user's call: "we just change the
  ML, remove that predictor").

## D-042 · The predictor's input query lives in `predictor.py`, not in the database (2026-09-25)

- **Decision:** The query that picks each device's newest **finished** day
  (`SELECT DISTINCT ON (device_id) * FROM dht22_aggregate WHERE date <
  CURRENT_DATE ORDER BY device_id, date DESC`) is a SQL string inside
  `worker/predictor.py`, the same pattern as `aggregator.py`. Today is
  excluded because its max/min are not final until the day ends.
- **Why:** The user asked whether this belongs in the database as a stored
  procedure. The ML part cannot run there: the models are scikit-learn
  Python objects, and running Python inside Postgres needs an extension
  (PL/Python) that the container lacks and that widens the attack
  surface. For the query alone, keeping it next to the code that uses it
  means one place to read and one file to change, versioned together in
  git, with no `init.sql` + live-database step. The database keeps its job
  of storing and guarding data (keys, CHECKs); application logic stays in
  the application.
- **Alternatives rejected:** (B) A database VIEW: reusable by other
  programs, but only one program needs it, and it would be one more object
  to keep in sync in `init.sql` and the live database. (C) A stored
  procedure for the whole job: impossible for the ML step, and the hardest
  option to test and debug.
- **Status:** ✅ Decided 2026-09-25. The user went on to write the query in
  `predictor.py` (option A).

## D-043 · Automatic daily jobs with APScheduler in `worker/scheduler.py` (2026-09-25)

- **Decision:** Aggregation and prediction run automatically once a day.
  `aggregator.py` and `predictor.py` wrap their work in functions
  (`run_aggregation()`, `run_prediction()`), each with an
  `if __name__ == "__main__":` guard so manual runs still work.
  `worker/scheduler.py` imports both and uses APScheduler's
  `BlockingScheduler` (timezone `Europe/Athens`) with a daily `cron` job
  that runs aggregation, **then** prediction, inside `try/except` with a
  logged line per run, so one failed night does not stop the scheduler.
  The exact run time depends on the day-boundary choice (UTC vs Athens
  days), decided separately.
- **Why:** Without it, the dashboard only changes when someone runs two
  scripts by hand, and a stored forecast goes stale (D-036). APScheduler
  is a standard Python library: timing, time zones and cron-style rules
  are handled for us, and it runs on Windows, Linux and later in a Docker
  container. Both jobs are upserts, so a retry or a double run never
  duplicates rows.
- **Alternatives rejected:** (A) Manual runs (the D-027 plan): no work,
  but nothing updates by itself. (B) Windows Task Scheduler + `.bat`
  file: quick, but Windows-only and invisible to the code base. A
  hand-written `while True` + `sleep` loop: it works, but re-implements
  timing, time zones and missed runs.
- **Known limits:** The scheduler lives in a terminal on the laptop. If
  the window closes or the laptop sleeps, it stops. Running it in its own
  container with `restart: unless-stopped` stays Future work.
- **Supersedes:** the "automatic scheduler" cut in D-027.
- **Status:** ✅ Decided 2026-09-25 (user chose C: "lets do it").

## D-044 · Table III evaluation: one test period, persistence and climatology baselines (2026-09-26)

- **Decision:** Every number in the report's Table III is measured on the
  same 616 test days (2025-01-01 → 2026-09-08), for the maximum and the
  minimum. Two reference forecasts: **persistence** (day n equals today's
  value) and **climatology** (the 1979–2024 mean for the calendar date,
  smoothed over 31 days). The minimum models are retrained on 1979–2024,
  like the maximum models: the notebook's minimum function still had
  the old split (up to 2021, from 1950; see D-038). Retraining changes
  no test MAE by more than 0.004 °C (Table III: day 4 2.18 → 2.19).
- **Why:** One test period makes the maximum and minimum columns
  comparable. Persistence is the bar set by requirement TR7; climatology
  is the other standard reference forecast, and the report already
  defines it. The 1979+ training window (D-033) applies to every model.
- **Result:** Ridge v2 beats persistence at every horizon (max 1.62 vs
  1.66 on day 1, 2.74 vs 3.06 on day 7; min 1.10 vs 1.38, 2.41 vs 2.82).
  Climatology (about 2.38 °C max and 2.16 °C min at every horizon) beats
  the model from day 3 (max) and day 4 (min), because the model sees
  today's weather but not the date. Day-of-year features, already in
  Future work, are the fix to try first.
- **Alternatives rejected:** (A) Minimum on the notebook's old split
  (2022+, 1,712 days): the two halves of the table would not be
  comparable. (B) Keep the saved minimum models trained on 1950–2021
  (the 2026-09-26 version of this entry): almost the same numbers, but
  it breaks the 1979+ rule. The user rejected it on 2026-09-27 ("We want
  only 1979 and onwards for training").
- **Status:** ✅ Done 2026-09-26 by Claude at the user's request ("run the
  tests needed for table 3"), with a script outside the repo that
  reproduces the notebook's numbers first. Minimum split corrected
  2026-09-27 at the user's instruction: report updated; the user
  changes the notebook's minimum split and re-runs it to re-save
  `models/ridge_v1.joblib`.
