import {prepareItems,standardRank,validateRank,capabilities,eligible,MAX_QUERY} from "./adaptive-core.mjs";
export function setupAdaptive(){
 const mount=document.getElementById("adaptive-intelligence");if(!mount)return {setItems(){},reset(){}};
 const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
 const note=el("p","Rank existing intelligence against your private priorities. No model can add evidence, change an alert or make a decision for you.","ai-note");
 const device=el("p","Checking browser capabilities…","ai-note"),status=el("p","Standard keyword search is available without a model download.","ai-note");status.setAttribute("role","status");
 const consent=el("button","Enable local AI");consent.type="button";consent.disabled=true;
 const stop=el("button","Use standard mode","secondary");stop.type="button";stop.disabled=true;
 const controls=el("div",undefined,"ai-actions");controls.append(consent,stop);
 const label=el("label","Your priority or question"),query=el("textarea");query.id="adaptive-query";query.rows=3;query.maxLength=MAX_QUERY;query.autocomplete="off";label.htmlFor=query.id;
 const run=el("button","Find relevant intelligence");run.type="button";
 const clear=el("button","Clear search","secondary");clear.type="button";
 const actions=el("div",undefined,"ai-actions");actions.append(run,clear);
 const count=el("p","No findings loaded.","ai-note"),output=el("div");output.setAttribute("aria-live","polite");
 mount.append(el("h2","Private Intelligence Engine"),note,device,controls,status,label,query,actions,count,output);
 let items=[],sig="",worker=null,ready=false,busy=false,serial=0,timer=null,manifest=null,caps=null;
 function terminate(){serial++;clearTimeout(timer);worker?.terminate();worker=null;ready=false;busy=false;stop.disabled=true;consent.disabled=!manifest||!caps||!eligible(caps);run.disabled=false;}
 function reset(){terminate();query.value="";output.replaceChildren();status.textContent="Standard mode. Local model stopped; no private query retained by the engine.";}
 function draw(rows,mode){
  output.replaceChildren();output.append(el("p",mode+" · Relevance order, not risk probability or verified importance.","ai-note"));
  if(!rows.length){output.append(el("p","No relevant existing finding returned."));return;}
  for(const r of rows.slice(0,8)){const x=items.find(z=>z.id===r.id);if(!x)continue;const card=el("div",undefined,"ai-result");card.append(el("small",x.status),el("strong",x.title),el("p",x.text.slice(0,440)));output.append(card);}
 }
 function fallback(message){terminate();status.textContent=message+" Standard keyword mode remains available.";if(query.value.trim())draw(standardRank(query.value,items),"Standard keyword search");}
 function start(){
  if(!manifest||!caps||!eligible(caps)||worker)return;
  const mb=(manifest.bytes/1e6).toFixed(1);
  if(!confirm("Download approximately "+mb+" MB of local AI assets from this platform? This may use mobile data, memory and battery. No private information is sent to an AI provider."))return;
  const current=++serial;busy=true;consent.disabled=true;stop.disabled=false;run.disabled=true;status.textContent="Downloading and initializing local model…";
  try{
   worker=new Worker(new URL("./adaptive-worker.mjs",import.meta.url),{type:"module"});
   worker.onerror=()=>{if(current===serial)fallback("Local AI unavailable on this device.");};
   worker.onmessage=({data:m})=>{
    if(current!==serial||!m)return;
    if(m.type==="ready"){clearTimeout(timer);ready=true;busy=false;run.disabled=false;status.textContent="Local AI ready · MiniLM q8 · CPU/WebAssembly. Private relevance searches stay in this worker.";return;}
    if(m.type==="result"&&ready&&busy&&m.id===pending){clearTimeout(timer);busy=false;run.disabled=false;try{draw(validateRank(m.rows,items),"On-device semantic relevance");status.textContent="Local AI completed. No evidence was added or promoted.";}catch{fallback("Local result rejected.");}return;}
    if(m.type==="error")fallback(m.message||"Local AI unavailable.");
   };
   timer=setTimeout(()=>{if(current===serial)fallback("Local model initialization timed out.");},180000);
   worker.postMessage({type:"init"});
  }catch{fallback("Local AI could not start.");}
 }
 let pending=0;
 run.onclick=()=>{
  const q=query.value.trim();if(!q){status.textContent="Enter a priority first.";return;}if(!items.length){status.textContent="No existing findings to rank. Load or evaluate your evidence first.";return;}
  if(!ready||!worker){draw(standardRank(q,items),"Standard keyword search");return;}
  if(busy)return;busy=true;run.disabled=true;const id=++pending;status.textContent="Ranking existing findings on your device…";output.replaceChildren();
  timer=setTimeout(()=>fallback("Local search timed out."),90000);
  worker.postMessage({type:"rank",id,query:q,items});
 };
 consent.onclick=start;stop.onclick=()=>{terminate();output.replaceChildren();status.textContent="Standard mode. Local model stopped.";};
 clear.onclick=()=>{query.value="";output.replaceChildren();if(busy){terminate();status.textContent="Search cancelled. Standard mode.";}};
 query.oninput=()=>{output.replaceChildren();if(busy&&ready){terminate();status.textContent="Search changed. Standard mode.";}}; 
 // Small public metadata request only. Model files are not requested before consent.
 Promise.all([capabilities(),fetch(new URL("./adaptive-assets/manifest.json",import.meta.url),{cache:"no-store",credentials:"omit",referrerPolicy:"no-referrer",signal:AbortSignal.timeout(10000)}).then(r=>r.ok?r.json():null).catch(()=>null)]).then(([c,m])=>{
  caps=c;manifest=m?.schemaVersion===1&&m.model==="Xenova/all-MiniLM-L6-v2"&&Number.isFinite(m.bytes)&&m.bytes>0&&m.bytes<100000000?m:null;
  device.textContent=(c.wasm?"WebAssembly available":"WebAssembly unavailable")+" · "+(c.gpu?"WebGPU detected (advanced models not enabled)":"WebGPU not detected")+" · "+(c.memory===null?"Memory not reported":c.memory+" GB reported memory")+(c.saveData?" · Data saver on":"");
  consent.disabled=!manifest||!eligible(c);
  if(manifest)consent.textContent="Enable local AI (~"+(manifest.bytes/1e6).toFixed(1)+" MB)";
  if(!manifest||!eligible(c))status.textContent="Local AI unavailable for this browser or release. Standard mode remains available.";
 }).catch(()=>{device.textContent="Device check unavailable. Standard mode remains available.";});
 return {setItems(rows){const next=prepareItems(rows),key=JSON.stringify(next);if(key===sig)return;sig=key;items=next;output.replaceChildren();count.textContent=items.length+" existing findings available"+(rows.length>items.length?" (first "+items.length+" only)":"")+".";
  if(busy&&ready){terminate();status.textContent="Evidence changed. Previous search cancelled.";}
 },reset};
}
