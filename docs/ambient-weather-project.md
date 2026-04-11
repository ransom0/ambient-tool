## 1. Project purpose

Build a Raspberry Pi–hosted Ambient Weather data system that:

- pulls live data from the Ambient Weather API
- stores observations locally in SQLite
- runs automatic collection on a schedule
- supports historical backfill from Ambient’s archived API data
- provides CLI-based analysis and trend reporting
- grows into charts, exports, and possibly a lightweight dashboard
- becomes useful both for short-term situational awareness and long-term weather/climate-style analysis at the station location

This should remain understandable, modular, and safe to evolve without breaking the database early.

### Working now

- Git/GitHub setup works over SSH
- project uses `src/` layout
- `ambient` CLI works
- current commands exist for summary/current/devices/raw
- `snapshot` saves data into SQLite
- SQLite database is being populated automatically by a systemd user timer
- timer files are now tracked in the repo under `deploy/systemd/`
- historical backfill framework has been started
- trend command exists in an early/basic form
- database already has a few hundred rows, so analysis is now meaningful

### Important architecture already in place

- local SQLite history store
- user-level systemd automation on the Pi
- Git-based development and versioning
- editable install with `.venv`
- UTC storage in database, local time conversion at display time

## 3. Guiding design principles

### 3.1 Keep raw data safe

Store enough raw source data so future analysis is possible even if current parsing is incomplete.

### 3.2 Keep database evolution cautious

Do not make large destructive schema changes casually. Prefer additive changes and clear migration steps.

### 3.3 Store in UTC, display in local time

Internal timestamps should remain UTC. Convert only at display/report time.

### 3.4 Separate layers

Try to keep these distinct:

- API client
- storage/database
- query/analysis
- CLI presentation
- automation/deployment

### 3.5 Build for meteorological usefulness, not just software neatness

The project should eventually help answer questions like:

- How has pressure been trending over the last 3 hours?
- How close are temp and dew point today?
- What are the rainfall patterns this month, season, or year?
- How unusual has this month been compared to prior local data?

## 4. Planned project layers

## Layer A — Core ingestion and storage

Purpose: reliably collect and store observations.

### Completed / partly completed

- live fetch from `/devices`
- snapshot command
- SQLite storage
- systemd timer
- partial backfill support
- dedupe direction established

### Remaining work

- finish and harden dedupe behavior
- harden backfill against 429/rate limits
- validate backfill range growth
- add small health/status checks for collector

---

## Layer B — Query and trend analysis

Purpose: read local data back out and summarize it intelligently.

### Current state

- basic trend command works for limited fields

### Planned direction

- support multiple requested fields
- add richer summary stats
- add derived metrics
- add optional tabular output
- add more meteorologically meaningful analyses

This is the next primary focus area.

---

## Layer C — Data quality and operational controls

Purpose: ensure data is trustworthy and system behavior is understandable.

### Planned features

- collector health/status command
- show last successful snapshot time
- show row counts and date range
- detect duplicate or missing intervals
- surface backfill progress and coverage range
- document how timer and backfill interact

---

## Layer D — Export and charting

Purpose: make the data visually useful.

### Planned outputs

- CSV export
- matplotlib charts
- maybe terminal-friendly ASCII mini-graphs
- possibly image output saved to files
- later maybe a simple web dashboard

---

## Layer E — Long-term station climatology / “pre-climatological” analysis

Purpose: use the station history as a local long-term record.

This is not formal climatology in the NOAA sense, but it can become a meaningful local station-based historical record.

### Useful long-term analyses

- monthly rainfall totals by month/year
- yearly rainfall accumulation since station start
- hottest/coldest days and months in your station record
- daily/weekly/monthly mean temperatures over time
- dew point behavior by season
- pressure trends around notable weather events
- count of days with temp/dew point spread below chosen thresholds
- count of humid nights or high-dew-point days
- rolling averages of temp, dew point, pressure
- seasonal charts across years once enough data exists

### Important caution

These only become more useful as the local database grows and remains clean.

## Roadmap

## Phase 1 — Stabilize ingestion

Goal: make collection/backfill trustworthy.

1. version systemd files in repo
2. finish dedupe and migration behavior
3. stabilize historical backfill
4. add retry/backoff for 429s
5. verify safe staged backfills
6. add simple collector status checks

## Phase 2 — Expand trend command

Goal: make CLI analysis genuinely useful.

1. support multiple fields with `--show`
2. improve stats output
3. add derived metrics like temp-dewpoint spread
4. add optional table/last-N output
5. support rain-oriented views
6. support pressure tendency summaries

## Phase 3 — Build query/export foundation

Goal: make data reusable.

1. query module cleanup
2. export CSV command
3. save chart-ready outputs
4. improve time filtering and grouping

## Phase 4 — Add charts

Goal: visualize data over time.

1. temperature/dew point/pressure line charts
2. rainfall accumulation charts
3. daily/monthly summary charts
4. long-term trend charts

## Phase 5 — Long-term historical analytics

Goal: develop station-history insights.

1. monthly/yearly rainfall summaries
2. hottest/coldest periods
3. rolling temp/dew point summaries
4. simple local normals-from-record over time
5. event analysis around storms or fronts

---

## 6. Near-term priorities

In practical order:

1. stabilize backfill and rate-limit handling
2. improve trend command into a multi-field tool
3. add derived field support, especially temp/dew point spread
4. do staged backfill beyond 1 day
5. then add richer outputs and later charts

---

## 7. Commit / push discipline

Use these checkpoints consistently:

### Commit when:

- a feature works end-to-end
- a bug is fixed
- before a risky refactor
- after a database/storage change that you’ve tested

### Push when:

- ending a work session
- after a meaningful working milestone
- before large experiments

Good mental model:

- commit = local save point
- push = remote backup / GitHub sync

---

## 8. Risks to watch

- rate limiting during backfill
- accidental duplicate ingestion without good dedupe
- making schema changes too early or too aggressively
- mixing display logic and query logic too much
- over-designing the CLI before deciding what weather insights are actually valuable
