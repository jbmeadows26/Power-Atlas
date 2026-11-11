/* Power Atlas · advertised rent snapshot, not HUD / ACS.
   Per-municipality provenance is mandatory. Never substitute a HUD figure,
   an adjacent ZIP, or a historical all-home median for current market listings.
   No visitor input is transmitted: we fetch a constant named market snapshot.
*/
(()=>{"use strict";
const URL="https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/main/data/housing/market-asking-rent-cliffside-park-2026-11.json";
const SUPPORTED="07010";
let serial=0;
let cache=null;
function emit(zip,status,market=null){
 window.dispatchEvent(new CustomEvent("poweratlas:market-rent-ready",{detail:{zip,status,market}}));
}
function validate(m){
 if(!m||m.schema!=="power-atlas.market-asking-rent-snapshot.v1"||
    !/^20\d\d-(0[1-9]|1[0-2])$/.test(m.snapshotMonth||"")||
    m.geography?.kind!=="municipality"||m.geography.relatedZipCode!==SUPPORTED||
    m.geography.zipSpecific!==false||
    !/^https:\/\/www\.trulia\.com\//.test(m.source?.url||""))throw Error("Unverified market snapshot");
 const snapshotDate=new Date(m.snapshotMonth+"-01T00:00:00Z");
 const cutoff=new Date(Date.now());cutoff.setUTCMonth(cutoff.getUTCMonth()-4);
 if(snapshotDate<cutoff)throw Error("Market snapshot is stale; a refreshed observation is required");
 for(const key of ["all","apartment_condo","house","townhouse"]){
   const type=m.propertyTypes?.[key];
   if(!type||typeof type.label!=="string")throw Error("Missing property-type evidence");
   for(const bed of ["1","2","3","4"]){
     const value=type.bedrooms?.[bed];
     if(value!==null&&!(typeof value==="number"&&Number.isFinite(value)&&value>=400&&value<=50000))
       throw Error("Invalid or absent rent figure");
   }
 }
 return m;
}
function get(){
 if(cache)return cache;
 const p=fetch(URL,{cache:"force-cache"}).then(r=>{
   if(!r.ok)throw Error("Market data not published");
   return r.json();
 }).then(validate);
 cache=p;
 return p.catch(err=>{cache=null;throw err;});
}
async function show(zip){
 const run=++serial;
 if(zip!==SUPPORTED){emit(zip,"unavailable");return;}
 emit(zip,"loading");
 try{
   const market=await get();
   if(run!==serial)return;
   emit(zip,"ready",market);
 }catch(_){if(run===serial)emit(zip,"unavailable");}
}
let previous="";
window.addEventListener("poweratlas:zip-visual-context",event=>{
 const d=event?.detail;
 if(!/^\d{5}$/.test(d?.zip||""))return;
 if(d.zip===previous)return;
 previous=d.zip;
 show(d.zip);
});
})();