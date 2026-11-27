"""Free-first text inference for trusted CI; no third-party Python dependencies."""
import argparse, json, os, re, subprocess, sys, time, urllib.request, urllib.error
from decimal import Decimal
from pathlib import Path

OR="https://openrouter.ai/api/v1"
GROQ="https://api.groq.com/openai/v1/chat/completions"
GEMINI="https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
LOCAL="http://127.0.0.1:11434"
PROFILES={
 "general": ["qwen3.5:4b","gemma3:4b","llama3.2:3b","qwen2.5:1.5b"],
 "reasoning": ["qwen3:4b","qwen3.5:4b","granite3.3:2b"],
 "coding": ["qwen2.5-coder:3b","qwen3.5:4b","granite3.3:2b"],
 "extraction": ["qwen2.5:1.5b","llama3.2:1b","gemma3:1b","granite3.3:2b"],
}
GROQ_MODELS=["openai/gpt-oss-120b","qwen/qwen3.8-27b","openai/gpt-oss-20b"]
GEMINI_MODELS=["gemini-3.5-flash-lite"]
CF_MODELS=["@cf/openai/gpt-oss-120b","@cf/openai/gpt-oss-20b"]
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None

def request(url, body=None, key=None, timeout=45):
    headers={"Content-Type":"application/json"}
    if key: headers["Authorization"]="Bearer "+key
    req=urllib.request.Request(url,data=None if body is None else json.dumps(body).encode(),headers=headers)
    handlers=[NoRedirect()]
    if url.startswith(LOCAL+"/"): handlers.append(urllib.request.ProxyHandler({}))
    with urllib.request.build_opener(*handlers).open(req,timeout=timeout) as response:
        return json.loads(response.read(5_000_000))

def zero_price(row):
    try:
        p=row["pricing"]
        if any(k not in p for k in ("prompt","completion")): return False
        return all(Decimal(str(v)) == 0 for v in p.values() if v is not None)
    except (ValueError, ArithmeticError, KeyError, TypeError):
        return False

def discover():
    rows=request(OR+"/models")["data"]
    return [r for r in rows if isinstance(r.get("id"),str)
            and r["id"].endswith(":free") and zero_price(r)
            and "text" in r.get("architecture",{}).get("input_modalities",[])
            and "text" in r.get("architecture",{}).get("output_modalities",[])]

def ranked(rows, profile):
    hints={"coding":("coder","devstral","qwen","gpt-oss"),
           "reasoning":("reason","deepseek","gpt-oss","qwen","nemotron"),
           "extraction":("lite","flash","small","gemma","qwen"),
           "general":("qwen","gemma","llama","nemotron","mistral")}[profile]
    def rank(r):
        name=r["id"].lower()
        return (next((i for i,h in enumerate(hints) if h in name),len(hints)),
                -int(r.get("context_length") or 0),name)
    return [r["id"] for r in sorted(rows,key=rank)]

def chat(url, model, key, prompt, tokens, free_router=False):
    body={"model":model,"messages":[{"role":"user","content":prompt}],
          "max_tokens":tokens,"stream":False}
    if free_router:
        body["provider"]={"max_price":{"prompt":0,"completion":0,"request":0,"image":0}}
    raw=request(url,body,key)
    usage=raw.get("usage") or {}
    if free_router and usage.get("cost") is not None and Decimal(str(usage["cost"])) != 0:
        raise ValueError("unexpected reported cost")
    text=raw["choices"][0]["message"]["content"]
    if not isinstance(text,str) or not text.strip(): raise ValueError("empty completion")
    return {"text":text,"model":raw.get("model") or model,"usage":
            {k:usage[k] for k in ("prompt_tokens","completion_tokens","total_tokens") if k in usage}}

def local(prompt,tokens,profile,start):
    models=PROFILES[profile]
    name="free-model-gateway-"+str(os.getpid())
    def docker(*args,timeout=180):
        subprocess.run(["docker",*args],check=True,timeout=timeout,
                       stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    owned=False
    try:
        try: installed=request(LOCAL+"/api/tags",timeout=3)
        except Exception:
            if not start: raise
            docker("run","-d","--name",name,"-e","OLLAMA_HOST=0.0.0.0:11434",
                   "-e","OLLAMA_NUM_PARALLEL=1","-p","127.0.0.1:11434:11434","ollama/ollama:latest",timeout=180)
            owned=True
            for _ in range(25):
                try:
                    installed=request(LOCAL+"/api/tags",timeout=3); break
                except Exception: time.sleep(2)
            else: raise RuntimeError("local service unavailable")
        present={r.get("name") for r in installed.get("models",[])}
        choices=[m for m in models if m in present]
        if owned: choices+= [m for m in models if m not in present][:2]
        for model in choices:
            try:
                if model not in present: docker("exec",name,"ollama","pull",model,timeout=240)
                raw=request(LOCAL+"/api/generate",{"model":model,"prompt":prompt,
                    "stream":False,"options":{"num_ctx":8192,"num_predict":tokens}},timeout=180)
                if not isinstance(raw.get("response"),str) or not raw["response"].strip(): continue
                return {"text":raw["response"],"model":raw.get("model") or model,
                        "usage":{"prompt_tokens":raw.get("prompt_eval_count"),"completion_tokens":raw.get("eval_count")}}
            except Exception: continue
        raise RuntimeError("no local completion")
    finally:
        if owned:
            try: docker("rm","-f",name,timeout=15)
            except Exception: pass

def confirmed(provider):
    return os.getenv(provider+"_FREE_PLAN_CONFIRMED","").lower()=="true"

def routes(profile,hosted):
    if not hosted: return
    key=os.getenv("OPENROUTER_API_KEY")
    if key:
        try: models=ranked(discover(),profile)[:2]
        except Exception: models=[]
        for model in models+["openrouter/free"]:
            yield "openrouter",model,OR+"/chat/completions",key,True
    key=os.getenv("GROQ_API_KEY")
    if key and confirmed("GROQ"):
        for model in GROQ_MODELS[:2] if profile in ("reasoning","coding") else GROQ_MODELS[1:]:
            yield "groq",model,GROQ,key,False
    key=os.getenv("GEMINI_API_KEY")
    if key and confirmed("GEMINI"):
        for model in GEMINI_MODELS: yield "gemini",model,GEMINI,key,False
    key=os.getenv("CLOUDFLARE_API_TOKEN")
    account=os.getenv("CLOUDFLARE_ACCOUNT_ID","")
    if key and confirmed("CLOUDFLARE") and re.fullmatch(r"[a-fA-F0-9]{32}",account):
        for model in CF_MODELS:
            yield "cloudflare",model,"https://api.cloudflare.com/client/v4/accounts/"+account+"/ai/v1/chat/completions",key,False

def generate(prompt,profile="general",tokens=512,hosted=False,start=False):
    if profile not in PROFILES or not isinstance(prompt,str) or not prompt.strip() or len(prompt)>16000 or not 1<=tokens<=1024:
        raise ValueError("invalid profile, prompt or token bound")
    attempts=[]
    for provider,model,url,key,guard in routes(profile,hosted):
        try:
            result=chat(url,model,key,prompt,tokens,guard)
            return {"status":"ok","provider":provider,**result,"attempts":attempts}
        except Exception as e:
            attempts.append({"provider":provider,"model":model,"status":
                "http_"+str(e.code) if isinstance(e,urllib.error.HTTPError) else type(e).__name__})
    try:
        result=local(prompt,tokens,profile,start)
        return {"status":"ok","provider":"ollama",**result,"attempts":attempts}
    except Exception as e:
        attempts.append({"provider":"ollama","status":type(e).__name__})
    return {"status":"deferred","provider":None,"model":None,"text":None,"attempts":attempts}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--catalog",action="store_true")
    p.add_argument("--prompt-file"); p.add_argument("--output",required=True)
    p.add_argument("--profile",choices=PROFILES,default="general")
    p.add_argument("--max-tokens",type=int,default=512)
    p.add_argument("--allow-hosted",action="store_true"); p.add_argument("--start-local",action="store_true")
    a=p.parse_args()
    if a.catalog:
        try:
            rows=discover()
            result={"status":"ok","openrouter":[r["id"] for r in rows]}
        except Exception:
            result={"status":"catalog_unavailable","openrouter":[]}
        result.update({"groq":GROQ_MODELS,"gemini":GEMINI_MODELS,"cloudflare":CF_MODELS,"ollama":PROFILES,
                       "note":"Catalog entries are not live inference tests; non-OpenRouter hosted routes require confirmed free-only accounts."})
    else:
        if not a.prompt_file: p.error("--prompt-file required")
        source=Path(a.prompt_file)
        if source.resolve()==Path(a.output).resolve() or source.stat().st_size>64000: p.error("invalid prompt file")
        result=generate(source.read_text(encoding="utf-8"),a.profile,a.max_tokens,a.allow_hosted,a.start_local)
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Gateway:",result["status"],result.get("provider") or "",file=sys.stderr)
    return 0 if result["status"]=="ok" else 75
if __name__=="__main__": sys.exit(main())
