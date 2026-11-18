# Eastern Axis — open-source intelligence analyst

The new **AI analyst** section is a country-filtered GitHub Pages interface backed by a daily GitHub Actions source-processing pipeline. It preserves the existing Neon API, Power Atlas root and Vercel fallback. It requires no Raspberry Pi or AppDeploy.

## Five optional adapters
- **GPT Researcher** runs only on manually dispatched research, with `EA_OPENAI_API_KEY` and `EA_TAVILY_API_KEY` secrets. AI/search providers may charge for inference; no paid key is enabled by default.
- **Local Deep Research** runs only on manual research, using an existing reachable authenticated LDR server configured by `EA_LDR_URL` (variable), `EA_LDR_USERNAME` and `EA_LDR_PASSWORD` (secrets). Its model/service must exist separately.
- **OpenOSINT** uses the official passive MCP `search_dns` tool against a scoped public domain configured via `EA_OPENOSINT_DOMAIN` (variable). No active scanning or personal-identity investigation is enabled.
- **OpenAleph** probes the read-only `/api/2/entities` endpoint at `EA_OPENALEPH_URL` (variable) with optional `EA_OPENALEPH_TOKEN` secret. No name matching is automatically published.
- **OpenCTI** probes its read-only GraphQL API at `EA_OPENCTI_URL` (variable) with `EA_OPENCTI_TOKEN` secret. This verifies authentication only; it does not imply cyber claims were imported.

## Free automated analysis (no API credentials)
The daily pipeline now combines the existing official publication-change monitor with public **DOJ, FARA, and CISA intelligence intake**, using title, date, publisher, original source URL, explicit country mentions, and collection status. DOJ/FARA/CISA imports remain **baseline metadata**, not confirmed misconduct or new alerts. Missing secondary intake is shown as unavailable rather than silently omitted.

An optional **Apache-2.0 MiniLM** sentence embedding model runs through [FastEmbed](https://github.com/qdrant/fastembed) on the temporary GitHub Actions CPU runner. It identifies possibly related **headlines across different publishers** and then requires compatible country and topic tags; similarity is **not** proof of independent corroboration. Topic labels and country counts also work without any model. The dashboard exposes the model's actual status: `available`, `unavailable`, `disabled`, or `insufficient-data`. Fallbacks never masquerade as AI analysis. None of this is a generative intelligence judgment or a forward-looking military threat score.

**Operational minimum:** original-source library, current change count, country coverage, subject breakdown, title search, baseline controls, publisher diversity, collection health and honest model status work without paid accounts. Full GPT Researcher/Local Deep Research report generation and OpenAleph/OpenCTI graph search still require their own authenticated servers/models. These are explicitly **not configured** until their live probes succeed.

## Publication and review
Only original-source titles, HTTPS source links, publishers, publication/detection dates, literal country mentions, auditable source-derived topic labels, and clearly limited semantic overlap are published. Invalid upstream schemas cause the workflow to fail closed rather than overwrite verified output. A new official report is not a new military deployment; mentioning a jurisdiction is not an accusation. LLM-generated documents are **unreviewed** and uploaded as seven-day GitHub Actions artifacts only for explicitly requested manual research. **Because this GitHub repository is public, treat artifact contents and workflow inputs as potentially public. Never include secrets, private intelligence, unpublished leads, or personal information.** Human verification of citations, original records, entity resolution, competing hypotheses and legal status is required before publishing any analytic assertions.

## Operation
Run the **Eastern Axis intelligence analyst** workflow with `research=false` for the first feed check; it then schedules at 06:17 UTC daily. Successful analyst workflow completion on `main` triggers the combined Pages release through `workflow_run` (including scheduled bot commits, which do not emit a follow-on push workflow). The Pages release rechecks Neon, mobile QA, and the root Power Atlas site before publishing `eastern-axis/public/analysis/manifest.json`. Keep provider secrets in GitHub Actions **Secrets**, never in repository variables or frontend bundles. The Pages interface shows each tool as disconnected until its live probe succeeds.
