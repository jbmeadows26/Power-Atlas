# GitHub Actions schedule migration (2026-11-17)

## Goal

Move no-cost, deterministic research integrity checks out of ChatGPT scheduled tasks so ChatGPT slots remain available for jobs that require reasoning, source evaluation, connector access, or notification. No paid LLM/API is configured; no private data or credential export.

## New consolidated scheduled workflow

[`scheduled-research-integrity.yml`](../.github/workflows/scheduled-research-integrity.yml) runs once daily (10:19 UTC) and on manual dispatch. Four independent jobs:

- Campaign promises: validate the existing source-linked pledge pilot and expanded research feed, falsification tests, and missing-denominator protections.
- Political authenticity: validate the existing official-biography audit and age comparison, preserving observed scope and missingness.
- Institutional decay: run the existing evidence provenance/denominator/leakage test suite.
- Power Atlas source gaps: check the reference gap ledger and run the static cross-site audit. Upload short-lived audit artifacts. No bot commits or Vercel deployment.

Existing scheduled collectors and production checks remain separate. In particular, `collect-political-authenticity.yml` and `reconcile-evidence.yml` have had failing scheduled runs as of November 17; these failures must not be labeled verified ingestion. The new workflow does not depend on them for success.

## What is *not* migrated

GitHub Actions without a research-agent credential cannot reproduce ChatGPT's source discovery, qualitative adjudication, development work, or push notification. Passing tests means **existing records satisfy their tested contracts**, not that new evidence was collected, a causal claim was proven, or the research is complete. Any ChatGPT automation paused after verification loses its open-ended research role; resume it for autonomous discovery.

The Nvidia financing four-hour watch relies on timely news interpretation and conditional ChatGPT notifications and should stay in ChatGPT. Likewise, deterministic GitHub workflows cannot replace authorized Vercel/PostHog investigative follow-up.

## Safety and operations

- Read-only `contents: read` token for each new job; no deployment credentials; no GitHub write operations.
- Failed jobs are visible through GitHub Actions and GitHub's configured notification preferences; GitHub failures do not generate ChatGPT push alerts.
- Scheduled Actions can be delayed and will not automatically fix failures.
- The new workflow uses only free public GitHub-hosted runners and checked-in validation scripts. Avoid frequent unnecessary schedule overlaps.
- To verify: inspect the workflow run (including each job), its checks, and the short-lived sitewide artifact. Only then disable overlapping ChatGPT monitoring slots.
