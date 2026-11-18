# Eastern Axis — early-warning data implementation and remaining access gaps

## Working free-first architecture

- **GitHub Pages frontend** displays a versioned, source-dated static JSON snapshot. It does not request upstream datasets from users' browsers or expose credentials.
- **GitHub Actions** validates parser fixtures and the Vite build, then refreshes the official-source snapshot daily; a successful refresh triggers the existing Pages workflow. Full-source probes during pull-request QA do not publish.
- **Verified observations** have a source name, original link, actual observation period, previous comparable period, unit, geographic scope, and source check status.
- **All signal screens are investigative leads.** They are not calibrated crisis probabilities, threat attribution, or declarations of imminent physical failure.
- **Freshness** is assessed per publication/observation: daily and monthly prices are not interchangeable. No missing value becomes zero, and insufficient history cannot generate a percentage change.

## Source matrix

| Layer | Public collector | Coverage | Boundaries |
|---|---|---|---|
| U.S. funding | Federal Reserve Bank of New York SOFR JSON | Daily rate and secured repo volume | U.S.-scoped transactions; not a bank run, global funding index or proof of collateral distrust |
| Industrial & food inputs | World Bank Pink Sheet monthly workbook | Matched commodity columns, month-on-month comparisons | Price benchmarks; individual markets may lack readings; not delivery lead time |
| Food basket & product groups | UN FAO nominal monthly food-price CSV | Six index categories when schema/date checks pass | International commodity indices, not retail inflation, yield forecasts or hunger prediction; acknowledge FAO as original source |
| GNSS signal-quality proxy | GPSInterference.com regional daily series | Global, three country and four regional views | Aircraft-reported degraded accuracy, not verified jamming/spoofing, intent, PTP drift or ground-system impact; source: GPSInterference.com (https://gpsinterference.com/), derived from adsb.lol ODbL data |
| Open-source project hygiene | OpenSSF Scorecard public JSON | Sample of critical repositories | Does not identify hostile maintainers or compromise; project sample not entire ecosystem |
| Maritime vessel flow | Existing IMF PortWatch module | Chokepoint volumes | Throughput is not advance insurance pricing or slot auction price |
| Manufacturing pressure / bilateral trade | Existing NY Fed GSCPI and bounded Comtrade module | Source-dated series | Not an exhaustive global commercial transportation/OTIF matrix |

## Unconnected or restricted indicators

- Panama Canal accepted slot bids, war-risk insurance quotes, global port actual waiting times and flight cargo price feeds need appropriate public APIs or authorized licensed feeds.
- Tier-2/Tier-3 supplier OTIF, defect rates, WIP and delivery backlogs require participating suppliers' permission. Public records cannot recreate those facts.
- PTP oscillator drift, utility transformer supplier production backlogs and independent cooling-water thresholds need operator measurements and jurisdiction-specific permits; aviation GNSS observations cannot substitute for clock telemetry.
- Global port/rail labor expiry index is incomplete. Verified agreements remain reference-only rather than projected labor stoppage probabilities.
- A full dependency graph requires independently corroborated ownership, supplier and infrastructure edges. Betweenness and propagation probability are not measured on a hypothetical graph.
- Correlated screens should include at least two independent sources and dated asset/exposure links before escalation. A commodity price spike alone is never a red alert.

## Source quality / operations

Collection errors are explicitly recorded and displayed via the Early Warning source audit. Failures in one source do not silently replace values with historical or invented figures. The last collection timestamp is **not** the timestamp of every underlying observation, and users should use the period on each card.

The public app and its source snapshot are available at:

- https://jbmeadows26.github.io/Power-Atlas/eastern-axis/
- https://jbmeadows26.github.io/Power-Atlas/eastern-axis/analysis/physical-early-warning.json

The production deployment must only be marked complete after both GitHub Actions and public browser QA pass.
