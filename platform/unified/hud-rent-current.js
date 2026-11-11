/* Power Atlas · current FY2027 HUD ZIP-level bedroom rent benchmarks.
   Compiled from original HUD SAFMR tables by Multifamily Today (CC BY 4.0).
   The file request contains the state code only, never the visitor's ZIP.
   These are voucher-program reference amounts (incl. utilities), NOT leases,
   market asking rent, observed neighborhood transactions or an owner effect.
*/
(()=>{"use strict";
const REPO="https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/main/data/housing/bedroom-rents/";
const PROVIDER="https://multifamily.today/data/zips/";
const HUD="https://www.huduser.gov/portal/datasets/fmr/smallarea/index.html";
const ATTRIBUTION="https://multifamily.today/data/";
const cache=new Map();
let serial=0;
const names=["Studio","1 bedroom","2 bedrooms","3 bedrooms","4 bedrooms"];
function e(tag,cls,content){const n=document.createElement(tag);if(cls)n.className=cls;if(content!==undefined)n.textContent=content;return n;}
function cash(n){return "$"+Math.round(n).toLocaleString("en-US");}
function valid(v){return Array.isArray(v)&&v.length===5&&v.every(x=>typeof x==="number"&&Number.isFinite(x)&&x>0&&x<=50000);}
function verifiedDoc(doc,state){return doc&&doc.state===state&&doc.fy===2027&&doc.zips&&typeof doc.zips==="object"&&doc.areas&&typeof doc.areas==="object";}
function box(){
 let root=document.getElementById("pa-hud-safmr");
 if(root)return root;
 const spot=document.querySelector("main > .vs6-topic")||document.getElementById("where");
 if(!spot)return null;
 root=e("section","pa-hud-safmr");root.id="pa-hud-safmr";root.hidden=true;
 root.setAttribute("aria-label","2027 HUD bedroom-specific rent benchmarks and their limitations");
 const status=e("p","pa-hud-status","");
 status.setAttribute("role","status");
 const rows=e("div","pa-hud-results");
 const source=e("a","pa-hud-source","Original HUD data and methodology ↗");
 source.href=HUD;source.rel="noopener noreferrer";source.target="_blank";
 const credit=e("a","pa-hud-source","Compiled source · CC BY 4.0 ↗");
 credit.href=ATTRIBUTION;credit.rel="noopener noreferrer";credit.target="_blank";
 root.append(e("span","pa-hud-kicker","CURRENT HUD PROGRAM BENCHMARK · FY2027"),
   e("h2",null,"Rent, by bedrooms."),
   e("p",null,"HUD Small Area Fair Market Rents are monthly housing-voucher program benchmarks, including utilities—not current apartment listings or an estimate of the rent paid for a home like yours."),
   status,rows,
   e("small","pa-hud-limits","ZIP statistical boundaries and HUD metro areas are not property boundaries. These estimates do not determine current asking rents, signed leases, or whether an individual landlord is charging too much."),
   source,credit);
 spot.append(root);return root;
}
function renderArea(r){
 const card=e("article","pa-hud-area");
 card.append(e("small","pa-hud-label",r.hudArea));
 const container=e("div","pa-hud-bars");
 const amounts=names.map((name,index)=>({name,value:r.usdByBedroom[String(index)]})).filter(x=>typeof x.value==="number"&&Number.isFinite(x.value));
 const peak=Math.max(1,...amounts.map(x=>x.value));
 for(const {name,value} of amounts){
   const line=e("div","pa-hud-row");const track=e("span","pa-hud-track");
   const fill=e("span","pa-hud-fill");fill.style.width=(100*value/peak).toFixed(1)+"%";
   track.append(fill);
   line.append(e("span","pa-hud-name",name),track,e("strong","pa-hud-price",cash(value)));
   container.append(line);
 }
 card.append(container);
 if(r.fiscalYear===2026){
   card.append(e("p","pa-hud-held","HUD lists an FY2026 figure as retained during FY2027 reevaluation. Check HUD’s applicable decision before relying on it."));
 }
 return card;
}
function send(zip,records,status){
 window.dispatchEvent(new CustomEvent("poweratlas:hud-benchmarks-ready",{
   detail:{zip,status,records,fiscalYear:2027}
 }));
}
function unpack(doc,zip){
 const entries=doc.zips?.[zip];
 if(!Array.isArray(entries))return [];
 const records=[];
 for(const entry of entries){
   if(!Array.isArray(entry)||typeof entry[0]!=="string"||!valid(entry[1]))continue;
   const area=doc.areas[entry[0]];
   if(!area||typeof area.name!=="string"||!area.name.trim())continue;
   const held=valid(entry[2]);
   const values=held?entry[2]:entry[1];
   const rent={};
   for(let i=0;i<5;i++)rent[String(i)]=values[i];
   records.push({zip,hudCode:entry[0],hudArea:area.name,
     fiscalYear:held?2026:2027,usdByBedroom:rent});
 }
 return records;
}
async function get(state){
 if(cache.has(state))return cache.get(state);
 const job=(async()=>{
   for(const base of [REPO,PROVIDER]){
     try{
       const res=await fetch(base+state+".json",{cache:"force-cache"});
       if(!res.ok)continue;
       const payload=await res.json();
       if(verifiedDoc(payload,state))return payload;
     }catch(_){/* Check one fallback without inventing figures. */}
   }
   throw Error("No verified current fiscal-year state file");
 })();
 cache.set(state,job);
 return job.catch(err=>{cache.delete(state);throw err;});
}
async function show(zip,state){
 if(!/^\d{5}$/.test(zip)||!/^[A-Z]{2}$/.test(state||""))return;
 const panel=box();if(!panel)return;
 panel.hidden=false;
 const status=panel.querySelector(".pa-hud-status"),results=panel.querySelector(".pa-hud-results");
 results.replaceChildren();status.textContent="Loading FY2027 HUD benchmarks for this ZIP…";
 const seq=++serial;
 try{
   const doc=await get(state);
   if(seq!==serial)return;
   const records=unpack(doc,zip);
   if(!records.length){
     status.textContent="No validated current HUD bedroom figures are available for this ZIP; no other ZIP or county value was substituted.";
     send(zip,[],"unavailable");return;
   }
   status.textContent=records.length>1?
      "This ZIP spans multiple HUD areas; the figures are shown separately. Choose the applicable area with the housing authority.":
      "FY2027 HUD Small Area Fair Market Rent for this ZIP and HUD rent area, effective October 1, 2026 except reevaluation holds.";
   records.forEach(r=>results.append(renderArea(r)));
   send(zip,records,"ready");
 }catch(_){
   if(seq!==serial)return;
   status.textContent="The current HUD rent source could not be retrieved. No historical median or prior-year figure has been substituted.";
   send(zip,[],"unavailable");
 }
}
window.addEventListener("poweratlas:zip-visual-context",event=>{
 const d=event?.detail;
 if(d?.status==="loading"&&/^\d{5}$/.test(d.zip||"")){
   show(d.zip,d.stateCode);
 }
});
})();
