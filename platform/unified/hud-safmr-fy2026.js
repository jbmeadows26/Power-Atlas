/* HUD FY2026 source-linked rent benchmarks. No current asking-rent estimates.
   The only network request uses ONE ZIP DIGIT (public read-only shard), never
   submits a visitor's complete postal ZIP to the data host or analytics. */
(()=>{"use strict";
const DATA="https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/main/data/housing/hud-safmr-fy2026-";
const HUD="https://www.huduser.gov/portal/datasets/fmr/smallarea/index.html";
const cache=new Map();let serial=0;
function el(tag,cls,content){const n=document.createElement(tag);if(cls)n.className=cls;if(content!==undefined)n.textContent=content;return n;}
function money(n){return "$"+Math.round(n).toLocaleString("en-US");}
function record(record){
  const card=el("article","pa-hud-area");
  card.append(el("small","pa-hud-label",record.hudArea));
  const chart=el("div","pa-hud-bars");
  const pairs=[["Studio",record.usdByBedroom["0"]],
               ["1 bedroom",record.usdByBedroom["1"]],
               ["2 bedrooms",record.usdByBedroom["2"]],
               ["3 bedrooms",record.usdByBedroom["3"]]];
  const max=Math.max(...pairs.map(x=>Number(x[1])||0),1);
  for(const [label,value] of pairs){
    if(!Number.isFinite(value))continue;
    const line=el("div","pa-hud-row"),name=el("span","pa-hud-name",label);
    const track=el("span","pa-hud-track"),fill=el("span","pa-hud-fill");
    fill.style.width=(value/max*100).toFixed(1)+"%";
    track.append(fill);
    line.append(name,track,el("strong","pa-hud-price",money(value)));
    chart.append(line);
  }
  card.append(chart);return card;
}
function panel(){
  const existing=document.getElementById("pa-hud-safmr");
  if(existing)return existing;
  const spot=document.querySelector("main > .vs6-topic")||document.getElementById("where");
  if(!spot)return null;
  const box=el("section","pa-hud-safmr");
  box.id="pa-hud-safmr";box.hidden=true;
  box.setAttribute("aria-label","HUD 2026 archived rental benchmark by bedroom");
  const title=el("h2",null,"Rent, by bedrooms.");
  const intro=el("p",null,"Official HUD FY2026 voucher benchmarks—not current listings, landlord charges or average rent.");
  const status=el("p","pa-hud-status","");status.setAttribute("role","status");
  const rows=el("div","pa-hud-results");
  const foot=el("small","pa-hud-limits","HUD ZIP-area benchmarks may cover more than one FMR area. ZCTAs are not precise postal, school, voting or municipality boundaries.");
  const source=el("a","pa-hud-source","Original HUD rent source ↗");
  source.href=HUD;source.target="_blank";source.rel="noopener noreferrer";
  box.append(el("span","pa-hud-kicker","SOURCE-BACKED HOUSING · FY2026"),title,intro,status,rows,foot,source);
  spot.append(box);return box;
}
async function getShard(digit){
  if(cache.has(digit))return cache.get(digit);
  const work=(async()=>{
    const response=await fetch(DATA+digit+".json",{cache:"force-cache"});
    if(!response.ok)throw new Error("Archived HUD snapshot is not published");
    const data=await response.json();
    if(data.schema!=="power-atlas.hud-fy2026-safmr-shard-v1"||
       data.fiscalYear!==2026||data.prefix!==digit||!Array.isArray(data.rows))
      throw new Error("Unverified HUD data version");
    return data;
  })();
  cache.set(digit,work);
  return work.catch(e=>{cache.delete(digit);throw e;});
}
async function show(zip){
  if(!/^\d{5}$/.test(zip))return;
  const box=panel();if(!box)return;
  box.hidden=false;
  const status=box.querySelector(".pa-hud-status"),results=box.querySelector(".pa-hud-results");
  status.textContent="Checking the original HUD FY2026 snapshot…";
  results.replaceChildren();
  const seq=++serial;
  try{
    const data=await getShard(zip[0]);if(seq!==serial)return;
    const rows=data.rows.filter(r=>r.zip===zip);
    if(!rows.length){
      status.textContent="No FY2026 small-area HUD record in the indexed source for this ZIP. No county rent has been substituted.";
      return;
    }
    status.textContent=rows.length>1?"This ZCTA overlaps "+rows.length+" distinct HUD rent areas. Each is shown separately.":
     "HUD FY2026 monthly gross-rent voucher benchmark for this ZCTA and FMR area.";
    rows.forEach(r=>results.append(record(r)));
    const source=box.querySelector(".pa-hud-source");
    source.title="HUD FY2026 SAFMR; source table collected "+data.retrievedUTC;
  }catch(_){
    if(seq===serial)status.textContent="This FY2026 archive is not available. The existing FY2027 and original HUD links remain accessible; no values are inferred.";
  }
}
window.addEventListener("poweratlas:zip-visual-context",e=>{
  if(/^\d{5}$/.test(e.detail?.zip||""))show(e.detail.zip);
});
})();
