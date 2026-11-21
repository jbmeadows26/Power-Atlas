# Evidence-gated Early Warning → AI Analyst → Command

## Operation

The public GitHub Pages dashboard reads the **same** source-linked decision artifact on both pages:
`eastern-axis/public/analysis/early-warning-triage.json`.
The physical source collector writes `physical-early-warning.json` and runs four times daily
(every six hours). A completed, successful collector workflow triggers the separate
`Eastern Axis signal analyst` GitHub Actions workflow. It commits a new triage snapshot;
that workflow's successful completion triggers the shared Pages build and mobile QA.
The website refreshes its displayed triage snapshot every five minutes. These are
**periodic snapshots**, not a continuously running model or streaming telemetry.

Every metric receives deterministic validation, country/region scope checks, movement
screening, source freshness and (where sufficient) a robust median/MAD historical test.
A two-observation percentage change is **not** treated as an established norm.
The parser retains up to 36 monthly observations for World Bank and FAO, up to 40
date-stamped GNSS samples, and up to ten SOFR readings, without inventing history.
More historical coverage is a prerequisite for calling a measurement statistically
abnormal; incomplete history stays marked as such.

Review-screen candidates are sent **individually** to a free, ephemeral
GitHub Actions Ollama `qwen2.5:1.5b` model. Small independent requests prevent
one malformed or truncated model response from invalidating every other review.
Each request contains dated source evidence, original URL, geographic scope,
baseline diagnostics and independently published supporting readings, if any.
The model returns monitor/elevate and a concise auditable rationale; deterministic
evidence gates still decide whether any promotion is permitted.
Failed items remain monitored and explicitly **unreviewed**. Review coverage is
`available`, `partial`, or `unavailable`; never silently claim 100% model
coverage.

### Publication gate

A candidate may be elevated into Command only after the model returns
`elevate` with medium/high confidence **and** a separately enforced gate passes:

1. An official NWS severe or extreme alert is still valid and fresh, with
   a direct official link, actual alert status, area and observed timestamp.
   It is a regional U.S. advisory, never an allegation of sabotage.
2. Or at least two independently published, source-dated series in a
   comparable sector (currently grain prices or oilseed prices) show
   fresh, same-direction, same-geography anomalies. Each source must have
   sufficient dated historical changes and absolute movement threshold
   plus |robust z| ≥ 3. A set of World Bank series alone never counts as
   independent corroboration. This is labeled an **observed systemic
   market anomaly**, not a confirmed incident or forecast.

No other model-only conclusion becomes a Command finding. Geo-proxies
do not imply hostile actors; software vulnerabilities do not prove a breach.

### Added free source feeds

| Collector | Source | Evidence and boundary |
| --- | --- | --- |
| CISA KEV | [CISA KEV](https://www.cisa.gov/known-exploited-vulnerabilities-catalog) | Catalog-listed exploited vulnerabilities, not victim incidents. If the CISA host denies the request, use the [official CISA GitHub mirror](https://github.com/cisagov/kev-data); retain which origin was used. |
| USGS | [Significant earthquakes](https://earthquake.usgs.gov/earthquakes/feed/v1.0/) | Source-reported significant events, not evidence of malicious activity. |
| NOAA SWPC | [Planetary Kp index](https://www.swpc.noaa.gov/products/planetary-k-index) | Observed geomagnetic index, not a grid outage report. |
| NOAA/NWS | [Active advisories](https://www.weather.gov/documentation/services-web-alerts) | Bounded severe and extreme active advisories. Local, time-sensitive U.S. official warnings only. |

Existing SOFR, World Bank commodity, FAO food, GNSS regional proxy and
OpenSSF hygiene feeds remain intact. Collector failures are visible in
source-health records. No failed feed is replaced with zero values.

### Interface behavior

**Early Warning:** measurement overview; analyst triage status;
threshold screens; all monitored observations, including source leads;
clickable per-record baseline, source and rationale; existing detailed
evidence and collector audit remain below. Unavailable AI is explicitly
reported as unavailable rather than as a neutral verdict.

**Command:** only genuine `elevated` records from the same published
triage JSON appear above Decision Radar. Old triage snapshots are clearly
marked stale and prior findings are not presented as current alerts.
The normal monitoring backlog never floods Command. Global readings
remain labeled worldwide context under national filters.

## Known coverage gaps and extensions

- Four checks a day can miss short-lived advisories. A dedicated faster
  alert-only collector is the next step if resources and source quotas allow.
- The analyst does **not** have a durable inference server. The model only
  runs on an ephemeral GitHub Actions runner when candidate screens exist.
- Calibrated causal risk, military intent, regional attribution and
  financial default probabilities cannot be inferred from this snapshot.
- Market/aviation/energy feeds outside these direct sources still need
  independent publication checks and domain-specific baseline calibrations.
- Neither direct on-platform user reports nor private source monitoring
  are inferred from this public workflow.

## Quality gates

`python -m unittest discover -s eastern-axis/tests -p test_signal_analyst.py -v`
covers dated source rejection, CISA/USGS observational limits, live NOAA
row schema, NWS advisories, model vetoes, and independent-publisher cases.
The source workflow also runs its existing price/FAO/GNSS tests, builds
the React dashboard, and the Pages release exercises touch QA.
