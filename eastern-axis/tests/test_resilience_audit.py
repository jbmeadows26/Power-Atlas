"""Independent weekly freshness gate regression fixtures."""
import datetime as dt
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location("resilience_audit",
    Path(__file__).resolve().parents[1]/"scripts"/"audit_resilience_snapshot.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
now=dt.datetime(2026,11,18,22,0,tzinfo=dt.timezone.utc)
def snapshot(at="2026-11-18T21:00:00Z"):
    return {"schemaVersion":1,"checkedAt":at,"capabilities":[],
        "observations":[
            *[{"id":"dns-"+str(i),"category":"dns_tls","status":"observed"} for i in range(4)],
            {"id":"regional","category":"regional_http","status":"observed"},
            {"id":"rpki","category":"bgp_rpki","status":"observed"}]}

class AuditIntegrity(unittest.TestCase):
    def test_valid_fresh_snapshot(self):
        self.assertEqual([],mod.verify(snapshot(),now))
    def test_stale_snapshot_failure(self):
        self.assertTrue(any("4h" in e for e in mod.verify(snapshot("2026-11-18T15:00:00Z"),now)))
    def test_missing_route_collector(self):
        p=snapshot()
        p["observations"]=[x for x in p["observations"] if x["category"]!="bgp_rpki"]
        self.assertTrue(any("bgp_rpki" in x for x in mod.verify(p,now)))
    def test_duplicate_probe_source_id(self):
        p=snapshot()
        p["observations"].append(p["observations"][0].copy())
        self.assertTrue(any("Duplicate" in x for x in mod.verify(p,now)))
    def test_unknown_is_not_available(self):
        p=snapshot()
        for x in p["observations"]:x["status"]="unavailable"
        self.assertTrue(any("No usable" in x for x in mod.verify(p,now)))
    def test_unparseable_clock_is_failure(self):
        p=snapshot()
        p["checkedAt"]="unknown"
        self.assertTrue(any("unparseable" in x for x in mod.verify(p,now)))
if __name__=="__main__": unittest.main()
