"""Test rhetoric metrics without pretending synthetic examples are a real corpus."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from rq2_corpus_metrics import hedging,fleiss_binary,analyze,BINARY

class RhetoricQC(unittest.TestCase):
    def test_lexical_measure_is_only_token_frequency(self):
        self.assertEqual(hedging("We might possibly act today"),.4)
        self.assertEqual(hedging("We will act today"),0)
        self.assertIsNone(hedging(""))
    def test_agreement_and_degenerate_case(self):
        self.assertEqual(fleiss_binary([[0,0,0],[1,1,1]]),1)
        self.assertIsNone(fleiss_binary([[1,1,1],[1,1,1]]))
        self.assertLess(fleiss_binary([[1,0,1],[0,1,0]]),.8)
    def test_no_manufactured_corpus(self):
        x={"id":"SYNTH-ONE","sourceUrl":"https://example.org/original","eventUTC":"2026-01-02",
          "unitType":"official_press_release","text":"We may act."}
        report=analyze([x])
        self.assertEqual(report["researchStatus"],"not_empirically_qualified")
        self.assertEqual(report["tripleCoded"],0)
        self.assertIsNone(report["kappaByCode"]["DIRECT_ANSWER"]["fleissKappa"])
    def test_qa_must_contain_question(self):
        with self.assertRaises(ValueError):analyze([{"id":"TEST","sourceUrl":"https://example.org","eventUTC":"2026-01-02","unitType":"interview_question_answer","answerText":"Yes"}])
    def test_triple_coding_unique_and_complete(self):
        x={"id":"TEST","sourceUrl":"https://example.org","eventUTC":"2026-01-02",
           "unitType":"standalone_speech","text":"Hello","secondPrimarySourceUrl":"https://example.org/second-original","annotations":[{"coderId":f"c{i}","codes":{k:1 for k in BINARY}} for i in range(3)]}
        self.assertEqual(analyze([x])["tripleCoded"],1)
        x["annotations"][1]["coderId"]="c0"
        with self.assertRaises(ValueError):analyze([x])
if __name__=="__main__": unittest.main()
