## Goal of trend

Turn `ambient trend` into the main local-analysis command for short-term and medium-term weather interpretation.

It should become the CLI tool that answers:

- what changed?
- how fast?
- what’s the range?
- what relationships matter meteorologically?

---

## Trend Layer 1 — Multi-field summary

### Objective

Support multiple requested fields in a single command.

### Command shape

ambient trend --hours 24 --show temp dewpoint pressure

### Initial supported fields

- `temp`
- `dewpoint`
- `humidity`
- `pressure`

### Output per field

- latest
- min
- max
- avg
- sample count

### Why first

This gives immediate value without changing the database.

---

## Trend Layer 2 — Derived fields

### Objective

Add fields computed from stored values.

### High-priority derived fields

- `spread` = temp - dewpoint
- `pressure_change` over selected window or last N samples
- later maybe rolling averages

### Why important

This is where the CLI starts becoming meteorologically useful, not just a stats wrapper.

### Example

ambient trend --hours 6 --show temp dewpoint spread pressure

---

## Trend Layer 3 — Rain support

### Objective

Add rain-related trend views.

### First version

Support stored Ambient fields directly:

- `hourlyrain`
- `dailyrain`
- `weeklyrain`
- `monthlyrain`
- `yearlyrain`

### Later version

Add computed rainfall over arbitrary windows:

- rain over last 3 hours
- rain over last 24 hours
- rain over selected event period

### Why staged

Cumulative counters are easy; computed interval rain requires careful logic around resets.

---

## Trend Layer 4 — Display modes

### Objective

Let you choose how much detail to show.

### Proposed options

- default summary mode
- `--table` for timestamped row output
- `--last N` for most recent N data points
- maybe later `--compact`

### Example

ambient trend --hours 6 --show temp dewpoint --table
ambient trend --hours 24 --show pressure --last 20

---

## Trend Layer 5 — Tendency / directional summaries

### Objective

Add weather-interpretation style outputs.

### Useful features

- pressure rising/falling/steady over 1h/3h/6h
- temp rising/falling over period
- dew point rising/falling over period
- spread tightening/widening

### Example

ambient trend --hours 3 --show pressure spread --stats

Possible summary text:

- pressure fell 0.08 inHg over 3 hours
- temp/dew point spread tightened from 7.1°F to 3.4°F

This is especially useful for severe-weather situational awareness.

---

## Trend Layer 6 — Multi-timescale summaries

### Objective

Support longer and grouped views.

### Future directions

- hourly summaries over a day
- daily summaries over a month
- monthly summaries over a year

### Why useful

This bridges short-term trend use with long-term station-history analysis.

---

## Trend Layer 7 — Chart-ready trend outputs

### Objective

Prepare for graphs without committing to dashboard work yet.

### Planned chart types

- temp + dew point line chart
- temp/dew point spread chart
- pressure line chart
- rainfall accumulation chart
- multi-day temp ranges
- monthly rainfall bars
- yearly rainfall accumulation

---

## Trend-specific meteorological ideas to keep in mind

These are not all immediate features, but they should guide design.

### Short-term severe-weather useful

- temp/dew point spread
- pressure fall over 1/3/6 hours
- dew point rise over 1/3/6 hours
- rainfall bursts in short windows
- wind/gust changes if you later add stronger wind support

### Medium-term useful

- humidity and dew point behavior over 24–72 hours
- front passage signatures using temp + pressure
- rain accumulation over event windows

### Long-term useful

- monthly rainfall totals
- hottest/coldest months by station record
- average dew point by month
- seasonal behavior of pressure and humidity
- rainiest months/years in your local record

---

## Recommended implementation order for trend

1. multi-field `--show`
2. richer summary stats per field
3. add `dewpoint`
4. add `spread`
5. add `pressure`
6. add `--table`
7. add rain fields
8. add tendency summaries
9. add grouped/time-bucketed summaries
10. add chart support
