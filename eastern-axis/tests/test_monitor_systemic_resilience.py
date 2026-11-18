"""Offline regression tests: never report an outage without corroboration."""
import importlib.util
import os
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

PATH=Path(__file__).resolve().parents[1]/"scripts"/"monitor_systemic_resilience.py"
sys.path.insert(0,str(PATH.parent))
spec=importlib.util.spec_from_file_location("resilience_monitor",PATH)
monitor=importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)

def make_probe(provider,failures):
    return {"id":"globalping-"+provider,"title":provider,"category":"regional_http",
            "provider":provider,"status":"warning" if failures>=2 else "observed",
            "failedRegions":failures}

class ResilienceIntegrityTest(unittest.TestCase):
    def test_single_provider_is_not_cascade(self):
        self.assertEqual([],monitor.correlate([make_probe("microsoft",3)]))
    def test_single_region_is_not_cascade(self):
        self.assertEqual([],monitor.correlate([make_probe("microsoft",1),make_probe("google",1)]))
    def test_two_independent_providers_watch_without_attribution(self):
        incidents=monitor.correlate([make_probe("microsoft",2),make_probe("google",3)])
        self.assertEqual(1,len(incidents))
        self.assertEqual("screening-only",incidents[0]["confidence"])
        self.assertIn("unknown",incidents[0]["explanation"])
    def test_credential_block_is_not_failure(self):
        item={"id":"globalping-ms","category":"regional_http","provider":"microsoft",
              "regions":[{"state":"unknown","httpStatus":403}],"status":"observed","failedRegions":0}
        self.assertEqual([],monitor.correlate([item,make_probe("google",3)]))
    def test_no_data_is_unavailable_not_green(self):
        snapshot=monitor.build_snapshot([],when="2026-11-18T20:00:00Z")
        self.assertEqual("unavailable",snapshot["status"])
        self.assertEqual(0,snapshot["sampledCount"])
        self.assertTrue(all(c["status"]!="sampled" for c in snapshot["capabilities"]))
    def test_unsupported_private_metrics_are_ignored(self):
        data='[{"metric":"leaked_secret","value":12,"observedAt":"2026-11-18T20:00:00Z"}]'
        with patch.dict(os.environ,{"RESILIENCE_METRICS_JSON":data}):
            self.assertEqual([],monitor.private_operator_metrics())
    def test_historical_watch_does_not_survive_new_clean_sample(self):
        prev={"history":[{"checkedAt":"2026-11-17T20:00:00Z","alerts":1,"observed":3,"errors":0}]}
        snapshot=monitor.build_snapshot([make_probe("microsoft",0)],prev,when="2026-11-18T20:00:00Z")
        self.assertEqual("sampled-no-correlated-alert",snapshot["status"])
        self.assertEqual(2,len(snapshot["history"]))
    def test_capability_only_marks_measured_when_sampled(self):
        obs=[{"id":"operator-foo","metric":"das_acoustic_alerts","status":"observed"}]
        snapshot=monitor.build_snapshot(obs,when="2026-11-18T20:00:00Z")
        selected={c["id"]:c["status"] for c in snapshot["capabilities"]}
        self.assertEqual("sampled",selected["cables"])
        self.assertEqual("requires operator access",selected["aiops"])
    def test_rolling_spike_requires_six_real_baselines(self):
        obs=[{"id":"ripe-cloudflare","category":"bgp_rpki","status":"observed","bgpUpdateCount":1000}]
        history=[{"samples":{"ripe-cloudflare.bgpUpdateCount":2}} for _ in range(5)]
        self.assertEqual([],monitor.screen_trends(obs,{"history":history}))
        history.append({"samples":{"ripe-cloudflare.bgpUpdateCount":2}})
        screens=monitor.screen_trends(obs,{"history":history})
        self.assertEqual(1,len(screens))
        self.assertEqual("deviation-from-rolling-baseline",screens[0]["kind"])
        self.assertIn("screening",screens[0]["detail"])
    def test_rolling_spike_is_not_automatic_global_attack(self):
        obs=[{"id":"ripe-cloudflare","category":"bgp_rpki","status":"observed","bgpUpdateCount":1000}]
        previous={"history":[{"samples":{"ripe-cloudflare.bgpUpdateCount":2}} for _ in range(6)]}
        snap=monitor.build_snapshot(obs,previous,when="2026-11-18T21:00:00Z")
        self.assertEqual("screening",snap["status"])
        self.assertEqual([],snap["incidents"])
        self.assertEqual(1,len(snap["screeningSignals"]))
    def test_pki_crl_403_not_correlated_outage(self):
        obs=[{"id":"gts-crl-transport","category":"pki_transport","status":"unavailable"}]
        snap=monitor.build_snapshot(obs,when="2026-11-18T21:00:00Z")
        self.assertEqual("unavailable",snap["status"])
        self.assertEqual([],snap["screeningSignals"])
    def test_history_bounded(self):
        hist=[{"checkedAt":str(i)} for i in range(500)]
        snapshot=monitor.build_snapshot([],{"history":hist},when="2026-11-18T20:00:00Z")
        self.assertEqual(48,len(snapshot["history"]))

if __name__=="__main__":
    unittest.main()
