export const codeValue=s=>{const v=String(s??"").trim();return /^(?:\d{8}|\d{10}|\d{4}\.\d{2}\.\d{2}(?:\.\d{2})?)$/.test(v)?v.replaceAll(".",""):null;};
export function lookup(index,code){
 const key=codeValue(code);if(!key)return {status:"invalid"};
 if(!index||!index.records||!Array.isArray(index.ambiguous))return {status:"unavailable"};
 if(index.ambiguous.includes(key))return {status:"ambiguous"};
 if(!Object.hasOwn(index.records,key))return {status:"not found"};
 const row=index.records[key];if(!row||["general","special","column2"].some(k=>row[k]!==null&&typeof row[k]!=="string"))return {status:"unavailable"};
 return {status:"exact reference",row,code:key};
}
export function landed(value,rate,freight,fees){
 if(![value,rate,freight,fees].every(x=>typeof x==="number"&&Number.isFinite(x)&&x>=0)||value>1e10||rate>1000||freight>1e10||fees>1e10)return null;
 const cents=n=>Math.round(n*100);
 const duty=cents(value*rate/100),total=cents(value)+duty+cents(freight)+cents(fees);
 return {duty:duty/100,total:total/100};
}
const $=id=>document.getElementById(id),fmt=n=>new Intl.NumberFormat("en-US",{style:"currency",currency:"USD"}).format(n);
export function setupProcurement(){
 let index=null,manifest=null,loading=false;
 const output=$("hts-result");
 function sourceLink(){const a=document.createElement("a");a.href="https://www.usitc.gov/2026_hts_revision_23";a.textContent="Official dated USITC revision";a.target="_blank";a.rel="noopener noreferrer";return a;}
 function render(){
  output.replaceChildren();const status=$("hts-status");status.textContent=loading?"Loading public tariff reference…":manifest?.status==="available"&&index?manifest.release+" · published "+manifest.releaseDate+" · "+manifest.recordCount.toLocaleString()+" exact codes · "+(manifest.currentCheck==="matches-listed-revision"?"Official listing matched at retrieval":"Current revision not independently confirmed"):"Reference unavailable. Consult USITC directly.";
  const code=$("hts-code").value.trim();if(code){
   const x=lookup(index,code),p=document.createElement("p");
   if(x.status==="exact reference"){
    p.textContent="Exact archived reference: "+x.code;output.append(p);
    for(const [label,k] of [["General","general"],["Special","special"],["Column 2","column2"]]){const line=document.createElement("p"),b=document.createElement("strong");b.textContent=label+": ";line.append(b,document.createTextNode(x.row[k]??"Not stated on this exact line — consult parent and notes"));output.append(line);}
    if(x.row.footnotesPresent||x.row.additionalDutiesPresent){const note=document.createElement("p");note.textContent="Footnotes or additional-duty fields are present in the source. Check the full schedule and applicable rules.";output.append(note);}
   }else{p.textContent=x.status==="invalid"?"Enter a valid 8- or 10-digit US HTS code.":x.status==="ambiguous"?"Conflicting exact-code entries. Review the official schedule.":x.status==="not found"?"Code not found in this dated reference. No duty inferred.":"Reference unavailable. No duty inferred.";output.append(p);}
  }
  output.append(sourceLink());
 }
 async function load(){if(loading)return;loading=true;index=null;manifest=null;render();try{
   const opts={cache:"no-store",credentials:"omit",referrerPolicy:"no-referrer",signal:AbortSignal.timeout(15000)};
   const a=await fetch("./data/hts-manifest.json",opts);if(!a.ok)throw Error("Missing manifest");const m=await a.json();manifest=m;
   if(m.status!=="available"||m.schemaVersion!==1||!Number.isInteger(m.recordCount)||m.recordCount<15000)return;
   const b=await fetch("./data/hts-index.json",opts);if(!b.ok)throw Error("Missing index");const data=await b.json();if(!data.records||Object.keys(data.records).length!==m.recordCount||!Array.isArray(data.ambiguous))throw Error("Index mismatch");index=data;
  }catch{index=null;}finally{loading=false;render();}}
 function calc(){const inputs=["hts-value","hts-rate","hts-freight","hts-fees"].map(id=>{const x=$(id);return x.value!==""&&x.validity.valid?Number(x.value):null;});const s=landed(...inputs);$("hts-duty").textContent=s?fmt(s.duty):"—";$("hts-landed").textContent=s?fmt(s.total):"—";}
 $("hts-code").oninput=render;for(const id of ["hts-value","hts-rate","hts-freight","hts-fees"])$(id).oninput=calc;$("hts-reload").onclick=load;
 render();calc();return {load,reset(){for(const id of ["hts-code","hts-value","hts-rate","hts-freight","hts-fees"])$(id).value="";render();calc();}};
}
