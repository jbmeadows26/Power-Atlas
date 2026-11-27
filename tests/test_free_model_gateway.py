import importlib.util, os, unittest, urllib.error
from pathlib import Path
from unittest.mock import patch
s=importlib.util.spec_from_file_location("gateway",Path(__file__).resolve().parents[1]/".github/actions/free-model/gateway.py")
g=importlib.util.module_from_spec(s); s.loader.exec_module(g)

class Gateway(unittest.TestCase):
    def test_price(self):
        self.assertTrue(g.zero_price({"pricing":{"prompt":"0","completion":"0","request":"0"}}))
        for p in [{"prompt":"0","completion":".01"},{"prompt":"0"},{"prompt":"0","completion":"0","request":"1"}]:
            self.assertFalse(g.zero_price({"pricing":p}))
    def test_discovery(self):
        a={"id":"test:free","pricing":{"prompt":"0","completion":"0"},
           "architecture":{"input_modalities":["text"],"output_modalities":["text"]}}
        with patch.object(g,"request",return_value={"data":[a,{**a,"id":"test"},{**a,"pricing":{"prompt":"1","completion":"0"}}]}):
            self.assertEqual(g.discover(),[a])
    def test_private_default(self):
        with patch.dict(os.environ,{"OPENROUTER_API_KEY":"x"},clear=True),patch.object(g,"chat") as c,patch.object(g,"local",return_value={"text":"ok","model":"x"}):
            self.assertEqual(g.generate("test")["provider"],"ollama")
            c.assert_not_called()
    def test_paid_accounts_blocked(self):
        with patch.dict(os.environ,{"GROQ_API_KEY":"x","GEMINI_API_KEY":"x","CLOUDFLARE_API_TOKEN":"x"},clear=True):
            self.assertEqual(list(g.routes("general",True)),[])
    def test_fallback(self):
        with patch.dict(os.environ,{"OPENROUTER_API_KEY":"x"},clear=True),patch.object(g,"discover",return_value=[]),patch.object(g,"chat",side_effect=urllib.error.HTTPError("x",429,"",{},None)),patch.object(g,"local",return_value={"text":"ok","model":"x"}):
            r=g.generate("test",hosted=True)
            self.assertEqual(r["provider"],"ollama")
            self.assertEqual(r["attempts"][0]["status"],"http_429")
    def test_defer(self):
        with patch.dict(os.environ,{},clear=True),patch.object(g,"local",side_effect=TimeoutError):
            self.assertEqual(g.generate("test")["status"],"deferred")
    def test_guard(self):
        with patch.object(g,"request",return_value={"choices":[{"message":{"content":"ok"}}],"usage":{"cost":0}}) as r:
            g.chat(g.OR+"/chat/completions","openrouter/free","x","test",20,True)
            self.assertEqual(r.call_args.args[1]["provider"]["max_price"]["completion"],0)
    def test_profiles(self):
        self.assertEqual(len(set(sum(g.PROFILES.values(),[]))),9)
        self.assertIn("qwen2.5-coder:3b",g.PROFILES["coding"])
