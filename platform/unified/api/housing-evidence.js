"use strict";
// Public evidence is served solely through the security-barrier view. No draft fallback.
// This endpoint does not disclose DB configuration, assertion research rows or errors.
module.exports = async function housingEvidence(req, res) {
  res.setHeader("Cache-Control", "no-store");
  res.setHeader("X-Content-Type-Options", "nosniff");
  if (req.method !== "GET") return res.status(405).json({ error: "Method not allowed" });
  const url = String(process.env.HOUSING_DATABASE_URL || "");
  if (!/^postgres(?:ql)?:\/\//.test(url)) {
    return res.status(503).json({ error: "Evidence service unavailable" });
  }
  const q = req.query || {};
  const assertionId = typeof q.assertion_id === "string" ? q.assertion_id : "";
  if (assertionId && !/^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$/.test(assertionId)) {
    return res.status(400).json({ error: "Invalid assertion identifier" });
  }
  if (Object.keys(q).some((key) => key !== "assertion_id")) {
    return res.status(400).json({ error: "Unsupported query" });
  }
  let client;
  try {
    const { Client } = require("pg");
    client = new Client({ connectionString: url, connectionTimeoutMillis: 4500,
      query_timeout: 5000, statement_timeout: 5000, application_name: "power-atlas-housing-read" });
    await client.connect();
    // If the login was misconfigured with elevated privileges, refuse to serve
    // even if the SQL query itself would have returned approved rows.
    const guard = await client.query(
      "SELECT has_table_privilege(current_user, 'atlas_housing.source_assertion', 'SELECT') AS raw_access, " +
      "has_table_privilege(current_user, 'atlas_housing.public_evidence', 'SELECT') AS approved_access, " +
      "has_table_privilege(current_user, 'atlas_housing.public_verified_relations', 'SELECT') AS legacy_access"
    );
    if (guard.rows.length !== 1 || guard.rows[0].raw_access !== false ||
        guard.rows[0].approved_access !== true || guard.rows[0].legacy_access !== false) {
      return res.status(503).json({ error: "Evidence service unavailable" });
    }
    const sql = "SELECT assertion_id, target_table, assertion_text, exact_locator, " +
      "verification_status, authority, source_url, reviewed_at, approved_at, display_evidence_state " +
      "FROM atlas_housing.public_evidence " +
      (assertionId ? "WHERE assertion_id = $1 " : "") +
      "ORDER BY assertion_id LIMIT 50";
    const result = await client.query(sql, assertionId ? [assertionId] : []);
    return res.status(200).json({ status: "approved_only", evidence: result.rows });
  } catch (_) {
    return res.status(503).json({ error: "Evidence service unavailable" });
  } finally {
    if (client) await client.end().catch(() => {});
  }
};
