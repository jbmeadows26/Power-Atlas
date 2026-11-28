# DS-001 — Acceptance Registry Engineering

This change records the DeepSeek-to-Codex engineering handoff requested on 2026-11-28. DeepSeek supplied static-analysis findings F1–F10 and proposed patches D1–D3. Codex independently reproduced the stage-mismatch, unsupported Failed assessment, and historical-release completion defects before implementation. The proposed patch bodies were not present in the repository and were not executed verbatim.

## Final engineering disposition

- Accepted: assessment evidence needs explicit stage compatibility; Failed requires failed execution evidence; history and current assessments both require validation; duplicate and unknown references must fail; G01 and G09 are nonwaivable; current completion needs external deployment identity.
- Modified: evidence reverse references are enforced only for evidence classified for an assessment. Integrated release executions and historical receipts use an explicit `release` or `historical` disposition and remain valid without an artificial capability association.
- Modified: stages are contracts, not a promotion hierarchy. `source`, `local`, `ci`, `deployed`, `production`, and `commercial` are distinct. Commercial evidence cannot satisfy a production-functionality contract.
- Rejected: a default mandatory-gate list when the declaration is missing. Schema v2 requires the exact canonical `mandatoryGatePolicy`; the validator also pins G01 and G09 to reject unauthorized policy edits.
- Rejected: treating any older production receipt as current. Release-bound assessments become `Stale`, or `Unavailable` when no trusted context is supplied.

## Current-release policy

The registry never proves its own deployment. `pages_release_identity.py verify` compares the public content-addressed manifest and asset bytes with repository source, then returns `eastern-axis.release-context.v1`. The validator accepts that context separately through `--release-context`. Without it, historical states remain visible but current-production completion is withheld.

G09 is evaluated from the external current release identity, avoiding an endless registry-update/deployment loop. Every verification stage remains commit-bound. Evidence can carry forward across an evidence-only release only when it declares a bounded `releaseScope`, the registry itself is outside that scope, and the release-identity builder mechanically proves every scoped Git path unchanged. Commercial evidence cannot carry forward merely because software assets are unchanged. The verified manifest lists the evidence IDs that passed the comparison.

## Evidence and assessment history

Evidence has an explicit disposition:

- `assessment`: must be referenced by a current or historical assessment.
- `release`: retained integrated release execution which need not map to one capability.
- `historical`: retained evidence superseded for current assessment purposes.

The orphaned `production-browser-df1e1a5b` receipt is an integrated failed release execution. It is classified `release`; it is not deleted and is not attached to unrelated gates. The narrower `production-decision-failure-df1e1a5b` receipt remains assessment evidence for EA-013 G02 and EA-017 G02.

Current Verified, Partial, and Failed assessments require a timestamp, stage, evidence, and preserved prior assessment history. Historical failures remain in `assessmentHistory` after a legitimate resolution. `Blocked` requires a typed direct blocker. Dependency-derived blockers are calculated separately.

EA-020 may be release-ready for a particular current release but remains continuous and is never permanently complete.

## Control Center

The browser reads the same registry plus the same-origin content-addressed release manifest and applies `acceptance-rules.mjs`. Cross-language tests compare Python and JavaScript state counts, stage counts, assessment currency, blockers, requirement readiness, and continuous semantics. The Python CI validator remains authoritative for schema integrity.
