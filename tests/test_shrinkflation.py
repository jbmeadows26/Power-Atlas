"""Verify published shrinkflation page content, links, and category data."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_shrinkflation_release():
  data=json.loads((ROOT/"data/consumer-practices/shrinkflation-v1.json").read_text())
  assert data["categoryDownsizingCpiEffectPp"]["householdPaper"]==3.0
  assert data["categoryDownsizingCpiEffectPp"]["coffee"]==1.4
  assert not data["methods"]["brandPriceChangesVerified"]
  for x in data["illustrations"]:
    assert abs(x["unitPriceChangePct"]-100*((x["newPriceUsd"]/x["newSizeOz"])/(x["oldPriceUsd"]/x["oldSizeOz"])-1))<1e-8
  for directory in ("site","platform/unified"):
    p=ROOT/directory
    h=(p/"consumer-practices.html").read_text()
    assert 'id="shrinkflation"' in h and 'data-sf-price="rises"' in h
    assert 'data-sf-category="coffee"' in h and "Actual price change: unverified." in h
    assert 'shrinkflation.js' in h and 'shrinkflation.css' in h
    assert (p/"shrinkflation.js").exists() and (p/"shrinkflation.css").exists()
  assert 'consumer-practices.html#shrinkflation' in (ROOT/"platform/unified/my-life.html").read_text()
