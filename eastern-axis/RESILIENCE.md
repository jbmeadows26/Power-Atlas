# Eastern Axis — Systemic Resilience Watch

## Scope
**Public sampled monitoring; not complete global or out-of-band visibility.**
This layer surfaces possible cascading internet failures and incomplete telemetry.
It is not an incident attribution engine or an autonomous remediation controller.

- **Public active probes**: TLS handshake, local DNS, certificate days-to-expiry; Globalping independent network probes of Microsoft and Google public login entry points; RIPEstat RPKI + 1-hour BGP updates for two sampled prefixes.
- **Additional no-key feeds:** Elexon BMRS near-real-time Great Britain transmission frequency (actual source timestamp and 15-minute freshness gate), PeeringDB AMS-IX registry metadata (not congestion), Google Trust Services root CRL endpoint HEAD transport (not OCSP validity or operator traffic volume).
- **Cross-region augmentation:** global probes now sample Microsoft, Google, Cloudflare, and GitHub public endpoints from the US, Germany, Singapore, Brazil, South Africa and Australia; the user-facing caution that public reachability is not authenticated transaction success remains.
- **Rolling screening rules:** after **six** prior observations, flag sufficiently large sampled DNS/TLS/BGP deviations as *screening only*; independently show official GB frequency bound crossings and operator thresholds without calling them correlated incidents.
- **Optional free token**: Cloudflare Radar traffic anomalies (GitHub Actions repository secret `CLOUDFLARE_API_TOKEN`; minimum permitted Radar Read token).
- **Authorized internal metrics**: optional `RESILIENCE_METRICS_JSON` Actions secret; publish **only aggregate metrics**, never raw EDR events, traces, credentials, hostnames or user identities.
- **Unconnected**: authenticated login/mail/calendar transactions, SaaS nth-party graph, AIOps policy changes, UPS/frequency controls, submarine acoustic sensing, IXP interface congestion, distributed tracing, deployment logs, cloud metadata delays, provider quota/ruleset limits, OCSP/CRL query volume, cyber-underground verification.

GitHub Actions monitors independently of the **target** Microsoft / Google control planes but is **not** a fully independent control plane itself; GitHub, hosting and DNS may also fail. A truly redundant system needs at least one non-GitHub, independently operated collector with separated power, networking, DNS and alert delivery. A local Raspberry Pi cannot be assumed available or online.

## Public sources and limitations

| Signal | Source | What it does **not** prove |
| --- | --- | --- |
| Regional HTTP HEAD | https://globalping.io/ | Authenticated M365 mail/MAPI/EAS or Google sign-in |
| DNS/TLS and expiry | Public host probes on independent Actions runner | TLS success at other locations, PKI revocation |
| RPKI/route activity | https://stat.ripe.net/ | All prefixes, live IXP congestion, global origin-invalid rate |
| Traffic anomalies (optional token) | https://radar.cloudflare.com/ | Cause, state actor or attribution |
| GB frequency sample | https://bmrs.elexon.co.uk/api-documentation/endpoint/system/frequency | Grid status elsewhere, UPS / ATS / transfer operations; UK-only |
| Exchange registry | https://www.peeringdb.com/apidocs/ | Internet exchange congestion or end-to-end reachability |
| CRL distribution transport | https://pki.goog/ | Certificate revocation validity, OCSP query time, CA-side volumes |
| Physical power reference | https://www.eia.gov/electricity/gridmonitor/ and https://transparency.entsoe.eu/ | Globally normalized live grid frequency |
| Subsea cables reference | https://www.iscpc.org/ | Cable-operator DAS access or globally complete fault feed |
| IXP reference | https://www.euro-ix.net/ | Permission to read private interface utilization |
| PKI reference | https://cabforum.org/working-groups/server/baseline-requirements/requirements/ | Real-time OCSP/CRL traffic volume; CA operator access required |

Do not use outage rumor chatter as incident attribution or evidence of a malicious act without independent corroboration.

## Operator aggregate schema

When an authorized owner connects internal systems, supply an Actions secret containing a JSON **array**. Example (illustrative only, never published as collected data):

```json
[
  {
    "metric": "automation_remediations_per_hour",
    "value": 45,
    "baseline": 10,
    "scope": "operator-approved region or service",
    "observedAt": "2026-11-18T19:00:00Z"
  }
]
```

Permitted metric names in `METRICS` of `scripts/monitor_systemic_resilience.py`. Samples older than an hour are dropped. Code strips all unrecognized fields and limits values/scopes before publication. Flags rate/latency metrics above 3x a supplied positive baseline and selected % utilization metrics at or above 90% as **screening warnings**. No irreversible API, rollback or switch is invoked; operators implement any circuit-breaker policy themselves.

## Source trust and alerting

- A successful unauthenticated HTTP HEAD means **reachability only**. HTTP 401/403/405 does not indicate successful authentication. A single failed region or unavailable probe is **not** a global outage.
- A correlated public watch requires at least two **distinct provider endpoints**, each with HTTP 5xx in at least two regions (US, DE, SG) in one measurement round. Independent source corroboration and human investigation are still required.
- RPKI `invalid_asn` and `invalid_length` are warning states on **sampled prefixes**; the cause remains unverified.
- BGP updates are from RIPE route collectors in a sampled hour, not all internet announcements.
- Sampling frequencies are **not** an official uptime SLO. A stale grid reading (over 15 minutes or more than one minute in the future) is a missing observation; crossing the GB statutory 49.5–50.5 Hz band is a preliminary review signal.
- Private deployment, AIOps policy, MELT, metadata propagation and quota metrics are collected only with an authorized aggregate Actions secret; those remain unconnected by default.
- CA CRL endpoint HEAD may respond 4xx even when an OCSP/CRL POST/GET would work; 4xx stays unknown. CRL validity and revocation storm volumes require separate operator data.
- The ICPC states 70–80% of subsea telecommunications faults are accidental and operator route/fault records are confidential. No raw DAS coverage is claimed. See https://iscpc.org/news/media-enquiries/

- Operator metrics are not included in public-global incident correlation, because internal baselines and authorization vary.
- No news report, status page, unresolved certificate, or cyber-underground claim alone can verify an attack.
- Missing, expired or unavailable feeds show **unknown**, not green; after 120 minutes the UI marks the public snapshot **stale**.
- GitHub scheduled jobs are best effort (30-minute cron, may be delayed). They do not meet a real-time detection SLO.

## Branch and deployment
- Code: `main` through a reviewed PR; frontend embedded inside existing **Risk watch**, keeping the persistent country selector and navigation.
- Telemetry: `telemetry/eastern-axis-live` branch, file `eastern-axis/public/telemetry/resilience.json`; raw GitHub URL read by the frontend. Scheduled commits do not push to `main`, avoiding a Vercel production build per observation.
- History: rolling 48 snapshots, read from the telemetry branch before each run; no background task in ChatGPT.
- Pages/Vercel builds keep their existing frontend workflow. No AppDeploy or paid service is necessary for the public collector subset.
- Tests: `python3 -m unittest discover -s eastern-axis/tests -p test_monitor_systemic_resilience.py -v`.

## Priority follow-on
Connect independent power feeds and cable advisories with clear latency/licensing and source dates; validate metadata and endpoint adapters with test tenants; obtain consent for private tracing, endpoint and quota telemetry. Publish a signed manifest and host an independent copy of alerts off GitHub before labeling the system truly out-of-band.
