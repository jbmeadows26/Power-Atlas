"""Offline no-text-republication source metadata tests. Synthetic text only."""
import unittest
from scripts.collect_2020_primary_sentence_inventory import index_source,select_content

SAMPLE={"id":"US20-TEST","side":"DEM","type":"platform_resolution","url":"https://www.presidency.ucsb.edu/documents/test","date":"2020-08-24"}

def html():
    paragraphs="".join("<p>We will implement public policy in the country. We may take various steps later.</p>" for _ in range(15))
    return ("<html><nav>Navigation here</nav><div class='field-docs-content'>"+paragraphs+
            "</div><footer>Copyright</footer></html>").encode("utf-8")

class SentenceIndexTests(unittest.TestCase):
    def test_full_source_sentence_indices_and_future_cues(self):
        obj=index_source(SAMPLE,html())
        self.assertEqual(obj["indexedSentenceCount"],30)
        self.assertEqual(obj["heuristicFutureTenseCues"],15)
        self.assertEqual(obj["reviewedPledgeSentences"],0)
        self.assertIsNone(obj["verifiedAtomicPledges"])
        self.assertTrue(all(s["verifiedAtomicPledge"] is None for s in obj["sentences"]))
        self.assertTrue(all(s["humanAdjudicationRequired"] for s in obj["sentences"]))

    def test_unique_sha_and_position_ids(self):
        doc=index_source(SAMPLE,html())
        self.assertEqual(len({x["id"] for x in doc["sentences"]}),30)
        self.assertTrue(all(len(x["sentenceSHA256"])==64 for x in doc["sentences"]))
        self.assertTrue(all("sentenceText" not in x for x in doc["sentences"]))

    def test_snapshot_digest_stable_and_differs_if_document_changed(self):
        original=index_source(SAMPLE,html())
        self.assertEqual(original["originalHtmlSHA256"],index_source(SAMPLE,html())["originalHtmlSHA256"])
        modified=html().replace(b"public policy",b"health policy")
        self.assertNotEqual(original["originalHtmlSHA256"],index_source(SAMPLE,modified)["originalHtmlSHA256"])

    def test_incomplete_content_is_not_silently_counted(self):
        with self.assertRaisesRegex(ValueError,"no reviewed source-content selector"):
            select_content("<article><p>Hi.</p></article>","TEST","platform_resolution")

if __name__=="__main__":
    unittest.main()
