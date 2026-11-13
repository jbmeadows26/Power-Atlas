"use strict";
const assert = require("node:assert/strict");
const Module = require("node:module");
const originalLoad = Module._load;
const handler = require("../platform/unified/api/housing-evidence.js");
const approved = { assertion_id: "approved-1", assertion_text: "Reviewed municipal rate", display_evidence_state: "verified_in_reviewed_scope" };
let simulatedGuard = { raw_access:false, approved_access:true, legacy_access:false };
let rows = [approved];
let failed = false;
const observed=[];
class Client {
  constructor(config) { assert.equal(config.application_name, "power-atlas-housing-read"); }
  async connect() { if (failed) throw new Error("PASSWORD=secret; draft detail"); }
  async query(sql, params=[]) {
    observed.push(sql);
    if (sql.includes("has_table_privilege")) return { rows:[simulatedGuard] };
    assert(sql.includes("FROM atlas_housing.public_evidence"));
    assert(!sql.includes("source_assertion a"));
    if (params.length) return { rows: rows.filter(r=>r.assertion_id===params[0]) };
    return { rows };
  }
  async end() {}
}
Module._load = function(id, parent, isMain) {
  if(id === "pg") return { Client };
  return originalLoad.apply(this, arguments);
};
function response() {
  return { headers:{}, setHeader(k,v){this.headers[k]=v;return this;},
    status(code){this.code=code;return this;},json(value){this.body=value;return this;} };
}
async function check(req) { const res=response(); await handler(req,res); return res; }
(async () => {
  delete process.env.HOUSING_DATABASE_URL;
  let res=await check({method:"GET",query:{}});
  assert.equal(res.code,503);
  assert(!JSON.stringify(res.body).includes("secret"));
  process.env.HOUSING_DATABASE_URL="postgresql://example:example@localhost/neondb";
  res=await check({method:"POST",query:{}});
  assert.equal(res.code,405);
  res=await check({method:"GET",query:{table:"source_assertion"}});
  assert.equal(res.code,400);
  res=await check({method:"GET",query:{}});
  assert.equal(res.code,200);
  assert.deepEqual(res.body.evidence,[approved]);
  assert.equal(res.headers["Cache-Control"],"no-store");
  res=await check({method:"GET",query:{assertion_id:"does-not-exist"}});
  assert.deepEqual(res.body.evidence,[]);
  simulatedGuard={raw_access:true,approved_access:true,legacy_access:false};
  res=await check({method:"GET",query:{}});
  assert.equal(res.code,503);
  simulatedGuard={raw_access:false,approved_access:true,legacy_access:true};
  res=await check({method:"GET",query:{}});
  assert.equal(res.code,503);
  simulatedGuard={raw_access:false,approved_access:true,legacy_access:false};
  failed=true;
  res=await check({method:"GET",query:{}});
  assert.equal(res.code,503);
  assert(!JSON.stringify(res.body).includes("draft"));
  assert(observed.every(q => q.includes("has_table_privilege") || q.includes("FROM atlas_housing.public_evidence")));
  console.log("Housing API contract PASS (fail closed, approved only, privilege guard, no error leaks)");
})().catch(e=>{console.error(e);process.exitCode=1}).finally(()=>{Module._load=originalLoad});
