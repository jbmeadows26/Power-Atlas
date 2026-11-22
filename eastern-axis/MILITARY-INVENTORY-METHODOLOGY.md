# Eastern Axis military equipment data: provenance and QA

Reviewed: 2026-11-22

## Sources and scope

- **DefenseMatrixLab 2026-Q4, revision 2026-11-21:** independently compiled CC BY 4.0 country-level public estimates for personnel, tanks, armored vehicles, artillery, combat aircraft, helicopters, drones, submarines, major surface vessels, missile estimates and military satellites. Pinned source: https://www.defensematrixlab.com/data/2026-q4-r20261121/countries_latest_long.csv (SHA-256 `fb12f0ba6209b84c2ff4207d7567480051be5bba8eff1791530da801a449ef82`). License: https://creativecommons.org/licenses/by/4.0/. Original source and download page: https://www.defensematrixlab.com/en/data-download.
- **FAS 2026:** independent nuclear warhead estimates, explicitly separating deployed strategic warheads, military stockpiles and retired weapons.
- **CRS/Japan MOD/ODNI:** unclassified country-specific government estimates and capability assessments from the original backend.
- **World Bank WDI:** historical IISS-derived active armed-forces personnel and SIPRI-derived spending, not 2026 verified equipment inventories.
- **IISS, Janes, FlightGlobal, UNROCA, Global Firepower, SIPRI, WDMMW:** publicly linked research starting points, **not** incorrectly labeled automated ingestions.

The equipment-source ingestion is a **source-attributed editorial estimate**, not government-verified active readiness. The revised 2026 dataset contains 9,641 source rows before filtering. Only 27 unit-count indicators from defense equipment and personnel categories are eligible. Source-provided inferred zeros are omitted, so unknown or unindexed capabilities are displayed as a dash rather than a factual zero. Scores, boolean capabilities and spending are not converted into asset counts. The pipeline does not pretend tactical drones or one-way attack UAVs are comprehensively measured. The source does not distinguish active vs storage/maintenance for all categories.

## Versioning and audit

The publishing build validates the exact **byte-level SHA-256** of the pinned source and rejects truncated, changed, or schema-incompatible downloads. It requires coverage of at least 145 countries and 1,600 nonzero counts, with per-domain minima for land, air, navy, personnel and missiles. A failed source update **fails closed** and does not replace the last verified GitHub Pages deployment with incomplete data.

Every displayed record stores: country ISO2 code, named equipment type, numerical quantity and unit, observation year, publisher, original source URL, dataset URL, version, source confidence, readiness limitation and CC BY 4.0 attribution. Country and global filters both use the same data; older sources remain in place. Duplicate DML records are idempotently replaced each build. FAS and other estimates are **not added together** with DML category totals.

A new DML release must be separately reviewed, its source fingerprint updated, and the same pipeline/tests re-run. Pinned reproducibility is intentional: no silently changing inventory estimates and no automatic promotion to operational-change alerts. A difference in editorial catalog versions is **not proof of real military mobilization**.

## QA

```bash
python3 -m unittest discover -s eastern-axis/tests -p 'test_military_equipment.py' -v
python3 eastern-axis/scripts/collect_military_inventory.py
python3 eastern-axis/scripts/collect_military_equipment.py
python3 -m unittest discover -s eastern-axis/tests -p 'test_military_equipment.py' -v
```

GitHub Pages publishing also runs the established Neon API checks and browser tests for mobile navigation and country context; the new smoke assertion checks China's sourced 2026 tank estimate and land-category filtering.

**Limits:** Equipment data are not a live unit tracker. Country/source estimates may differ because of equipment classification, coverage dates, serviceability, storage and wartime attrition. Independent estimates require corroboration before entering any elevated military-asset anomaly queue.
