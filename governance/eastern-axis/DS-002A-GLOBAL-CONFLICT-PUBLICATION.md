# DS-002A — Global Conflict Analyst Publication Engineering

This records the DeepSeek-to-Codex handoff for the failed Global Conflict Analyst run `46071339454`. DeepSeek supplied findings F1–F9 and unexecuted proposals D1–D5. Codex used the final independent review as the governing engineering requirements and did not apply the proposals verbatim.

## Historical failure classification

The run's analysis, source collection, evidence gates, output assertions, and frontend build succeeded. The combined commit/push step failed. Available evidence does not establish the dirty paths, a genuine JSON content conflict, or the exact push failure subtype. The retained classification is therefore `combined-checkout-publication-failure-unresolved`: analysis `success`, validation `success`, publication `failed`, production `unavailable`. The unsuccessful run remains in the receipt history and does not make the analyst operational.

## Publication policy

The `global-conflict` job remains the read-only analysis job and preserves the existing check name. A separate `publish-snapshot` job alone receives `contents: write`, only on non-PR `main` executions after analysis succeeds. Its downloaded artifact is the sole analytical input.

Publication uses `scripts/guarded_snapshot_publish.py`. On every bounded attempt it:

1. Parses the candidate timestamp as UTC and validates schema, evidence provenance, and snapshot invariants.
2. Fetches the latest authorized `main` head and distinguishes a missing snapshot from unreadable or malformed retained data.
3. Treats identical bytes at an equal timestamp as a no-op, rejects changed bytes at an equal timestamp, and rejects older candidates.
4. Creates a new detached worktree at the exact fetched head, verifies full tracked/staged/untracked cleanliness, installs only the allowlisted snapshot, and commits exactly that path.
5. Performs a normal fast-forward push. A concurrent update causes a new fetch, new clean worktree, and complete revalidation. No rebase, force push, stash, reset, or unrelated commit is used.
6. Classifies ordering, malformed data, provenance, contamination, authorization/protection, transport, non-fast-forward, deadline, and retry-exhaustion failures separately.

Workflow artifacts retain stage-specific analysis, validation, publication, snapshot identity, and explicit production-unavailable evidence. Publication is not production verification. Current production status additionally requires DS-001 mechanical release context.

## Analyst registry policy

Run-level success or failure does not infer a stage. Legacy receipts without step evidence are `unavailable` for analysis, validation, publication, and production. Receipts are validated for type, workflow/run identity, full SHA, UTC timestamp, duplicates, stage evidence, failure classification, and optional snapshot identity, then sorted by parsed time with a deterministic run-number tie break. Historical failures remain after later success.

The public registry and UI display analysis, publication, and current-production status independently. `outputGeneratedAt` is explicitly the retained artifact's generation time, not the last analytical attempt or observation freshness. The legacy `operationalStatus` field remains for compatibility but is not used to infer stage success.

## Scope and protections

F9 remains a disclosed limitation: the shared `outputSchema` description is compatibility metadata and does not prove that planned analysts emit that schema. Resolving per-analyst output contracts is separate analytical engineering.

Repository rules were not changed or bypassed. The GitHub API returned HTTP 403 for branch-protection inspection. Before merge, an administrator or read-authorized export must confirm whether `global-conflict` is the required check and whether adding the non-PR-only `publish-snapshot` job affects ruleset evaluation. Source engineering, PR checks, and offline publisher tests do not require production write authority.
