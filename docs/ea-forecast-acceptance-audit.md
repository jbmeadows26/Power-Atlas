# EA-010 / EA-011 forecast acceptance audit

The existing `eastern-axis/scripts/forecast_product_shortages.py` produces conditional shortage pressure screens from input prices, corridor transit counts and limited inventory observations. It explicitly describes its score as uncalibrated triage and its horizon as a planning scenario. These outputs do not satisfy validated forecasting acceptance: no measured product-level prediction target, out-of-sample evaluation or uncertainty validation is established by this module.

This implementation adds explicit machine-readable `forecastStatus: withheld`, the required withholding message, scenario classification, methodology version, and null predicted outcome/uncertainty to every screen. Missing or invalid monthly changes now remain null instead of being reported as zero. Existing risk-screen rules and evidence remain intact.

Validation: `python -m unittest discover -s eastern-axis/tests -p test_shortage_forecasts.py -v` passed 10 tests on 2026-11-27, including missing/invalid versus genuine zero changes and withholding on every output. Fixtures are isolated test data.

Remaining acceptance: a narrow real prediction target with adequate historical vintages, walk-forward baseline comparison, uncertainty evaluation, an append-only issuance/outcome ledger retaining unsuccessful predictions, and production UI/deployment verification. No forecast capability is classified complete by this change. Existing historical data may support a future input-price target; that is distinct from a product shortage prediction and requires its own evaluation. No public output was regenerated from incomplete or stale inputs during this audit.
