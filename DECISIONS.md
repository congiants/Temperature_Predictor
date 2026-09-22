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
