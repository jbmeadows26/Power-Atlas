# Eastern Axis acceptance governance

Canonical machine-readable registry: [`../../site/development-control/acceptance.json`](../../site/development-control/acceptance.json). This is the single source for the EA-001–EA-020 backlog, dependencies, acceptance criteria, release gates and evidence references. Readiness is derived from that registry plus independently established current-release identity; it is never stored as a manually edited percentage. The [control center](../../site/development-control/index.html) reads the registry and content-addressed release manifest directly. See [DS-001 Acceptance Registry Engineering](DS-001-ACCEPTANCE-REGISTRY-ENGINEERING.md) for the DeepSeek-to-Codex handoff and current-release policy.

Run `python scripts/validate_eastern_axis_acceptance.py` to validate history with current release context explicitly unavailable. Supply mechanically verified output with `--release-context <identity-result.json>` to compute current-production readiness. Run `python -m unittest discover -s tests -p test_eastern_axis_acceptance.py -v` for integrity and Python/JavaScript parity tests. Only Verified records with executed, stage-compatible passing evidence count. Not applicable requires rationale, is separately disclosed and is excluded from the denominator. The schema requires the canonical nonwaivable G01 and G09 declaration. Dependency failures prevent release readiness. EA-020 is continuous and can never be permanently completed.

The initial registry deliberately records Pending, including for existing working software. These states mean acceptance evidence has not yet been assessed and recorded under this directive, not that functionality is absent. No completion percentage is maintained. Each gate must be assessed for applicability before release; pending applicability is not a pass.

## Evidence contract

Add public, non-sensitive attestations to `evidence`: stable `id`, actual timezone-qualified `executedAt`, full `commit`, retrievable `artifact`, `method`, `scope`, explicit `stage`, actual `result`, and `disposition`. Deployment, production and commercial evidence also supplies `deployedCommit` matching the tested commit. Assessment evidence must be referenced; integrated release and historical evidence need an explicit reason instead. Record unsuccessful executions and preserve them in assessment history after resolution. Schema validation cannot establish that an attestation is true: review the underlying artifact. Do not include private business records, credentials or sensitive logs.

## Dependency-aware roadmap

1. Foundation: EA-001, EA-002, EA-020.
2. Private ingestion and recovery: EA-004, EA-005; extend existing shared private workspace and Adaptive Intelligence.
3. Relational approved facts: EA-006, EA-007, EA-008.
4. Core convergence: EA-003.
5. Intelligence expansion: EA-009, EA-010, EA-011, EA-012, EA-015.
6. Decisions and customer experience: EA-013, EA-014, EA-016.
7. Commercial preparation: EA-017, EA-018, EA-019.

Exact dependencies are maintained only in the registry. Existing procurement, sanctions screening, vault and local AI must be reused and regression-tested. Pricing is hypothetical; real participation, licensing and hosting eligibility remain external commercial gates. No paid infrastructure or external recruitment is authorized by this registry.

## Specification mapping

This mapping follows the user's 18-section execution directive. It does not pretend to reproduce a separately adopted product specification whose original text has not been supplied. That original remains an explicit documentation dependency.

| Directive section | Acceptance requirements |
|---|---|
| 1 Assignment | EA-001, EA-020 |
| 2 Governing product vision | EA-003, EA-012, EA-013 |
| 3 Platform architecture | EA-003, EA-006, EA-015 |
| 4 Development principles | EA-001, EA-002, EA-008, EA-018 |
| 5 Initial repository audit | EA-001, EA-020 |
| 6 Permanent development governance | EA-001, EA-020 |
| 7 Mandatory backlog | EA-001 through EA-020 |
| 8 Adaptive Intelligence Engine | EA-004, EA-015, EA-018 |
| 9 Public intelligence infrastructure | EA-002, EA-008, EA-009 |
| 10 Privacy and security | EA-004, EA-005, EA-006, EA-017, EA-018, EA-020 |
| 11 Development Control Center | EA-001, EA-020 |
| 12 Release gates | All requirements, G01 through G11 |
| 13 Implementation sequence | Registry dependencies and roadmap above |
| 14 GitHub and deployment | EA-020, G09 |
| 15 Prohibited shortcuts | EA-001, EA-008, EA-010, EA-012, EA-018 |
| 16 Pilot MVP acceptance | EA-003 through EA-008, EA-010 through EA-014, EA-017 |
| 17 Final reporting | EA-001, EA-020 |
| 18 Execution instruction | All requirements |

## Acceptance-count audit and execution stages
The original 240 records consist of 20 customer acceptance outcomes and 220 capability-specific release assessments. They are not 240 independent product features. The control center now reports these denominators separately, and every release assessment names its capability-specific check. The eleven gate definitions remain canonical; shared execution evidence can be referenced across relevant capabilities without inventing independent test runs. Gates are retained because the directive requires applicable gates per capability; applicability changes require explicit reasons.

Evidence stages distinguish source implementation, local verification, CI verification, deployed identity, production functionality and commercial validation. They are separate contracts rather than an automatic promotion hierarchy. Every stage is commit-bound. A CI-Verified gate is not production verification and becomes stale on another release unless an explicit tested asset scope is mechanically unchanged. Commercial evidence cannot substitute for technical production evidence or carry forward from code identity alone. No complete requirement is inferred from a subset of passing gates. Recorded historical CI for commit 59830a7e covers bounded Business and vault tests; full document formats and overall Pilot acceptance remain incomplete.
