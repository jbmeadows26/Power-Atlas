# Power Atlas — evidence-linked redistricting research

Public, low-storage data repository for Power Atlas. This repository indexes **candidate research records**, not verified allegations or final case dispositions.

## Architecture
- `data/batches/`: source-indexed incremental batches.
- `scripts/build.py`: deterministic deduplication, schema checks, compact export.
- `data/research.json`: versioned read-only frontend feed.
- `.github/workflows/validate.yml`: free-tier GitHub Actions validation on push and weekly.

Run `python scripts/build.py`. The workflow checks the export is committed and matches its inputs. No AI credits, scraping, or paid API keys required.

**Data policy:** No mirrored PDFs, HTML pages, transcripts, personal contact details, or embeddings. Retain stable IDs, dates, short titles, source URLs, and verification labels. Unreviewed records must not be presented as proven influence. Do not redistribute third-party datasets without checking their licenses.

**Frontend:** https://gerrymandering-power-atlas-0ythxx.v2.appdeploy.ai/ — connecting it to this feed requires a future AppDeploy release. JSON feed: https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/main/data/research.json

**Scope:** The first eight litigation index entries are not a nationally complete dataset and require independent primary-docket verification. The scheduled workflow currently validates existing files; it does not autonomously collect new cases.
