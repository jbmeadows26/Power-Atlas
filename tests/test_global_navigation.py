"""Navigation remains available on every Power Atlas research destination."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/"platform"/"unified"
PAGES={"compare.html":"compare","index.html":"overview","dark-money.html":"money","reform-lab.html":"reforms","election-money.html":"money","money-sources.html":"money","donor-intelligence.html":"money","investigations.html":"money","navatek.html":"money","election-2026.html":"overview"}
class GlobalNavTests(unittest.TestCase):
 def test_all_pages_share_nav(self):
  for filename,section in PAGES.items():
   with self.subTest(filename=filename):
    html=(ROOT/filename).read_text(encoding="utf-8")
    self.assertEqual(html.count('id="pa-global-header"'),1)
    self.assertIn('href="global-navigation.css"',html)
    self.assertIn('aria-label="Main sections"',html)
    self.assertIn('data-pa-nav="'+section+'" aria-current="page"',html)
    for target in ("index.html","compare.html","dark-money.html","reform-lab.html"):
     self.assertIn('href="'+target+'"',html)
 def test_sticky_header_and_anchor_offsets(self):
  css=(ROOT/"global-navigation.css").read_text(encoding="utf-8")
  self.assertIn("#pa-global-header{position:sticky",css)
  self.assertIn("top:0;z-index:9999",css)
  self.assertIn("scroll-margin-top:",css)
  self.assertIn('body[data-pa-page="compare"] > header{display:none',css)
