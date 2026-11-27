const norm=s=>String(s??"").normalize("NFKC").trim().replace(/\s+/g," ").toUpperCase();
export function screen(data,name,now=Date.now()){
 const q=norm(name);if(!q||q.length>500)return {status:"invalid",matches:[],coverage:[]};
 const t=Date.parse(data?.checkedAt);if(data?.schemaVersion!==1||!Number.isFinite(t)||t>now+60000||now-t>48*3600000)return {status:"unavailable or stale",matches:[],coverage:[]};
 const matches=[],coverage=[];
 for(const key of ["SDN","Consolidated"]){
  const s=data.sources?.[key];
  const available=s?.status==="available"&&Array.isArray(s.entries)&&s.entries.length===s.organizationEntries&&s.organizationEntries>0;
  coverage.push({key,available,date:available?s.published:null,count:available?s.organizationEntries:null});
  if(!available)continue;
  for(const r of s.entries){const primary=norm(r.name)===q,alias=Array.isArray(r.aliases)&&r.aliases.some(a=>norm(a)===q);if(primary||alias)matches.push({list:key,uid:r.uid,name:r.name,match:primary?"Primary name":"Strong alias",programs:r.programs,countries:r.countries,date:s.published});}
 }
 return {status:coverage.some(x=>x.available)?matches.length?"Potential name matches":"No exact name candidate in available scope":"unavailable",matches,coverage};
}
const $=id=>document.getElementById(id),node=(tag,text)=>{const x=document.createElement(tag);x.textContent=text;return x;};
export function setupSuppliers(){
 let data=null,busy=false;
 function render(){
  const target=$("supplier-results");target.replaceChildren();
  const name=$("supplier-name").value.trim(),r=screen(data,name||"__coverage_only__");
  $("supplier-status").textContent=busy?"Retrieving public reference…":r.coverage.length?r.coverage.map(x=>x.key+": "+(x.available?x.count.toLocaleString()+" organizations · published "+x.date:"Unavailable")).join(" | "):"Reference unavailable or stale. No screening conclusion.";
  if(!name)return;
  target.append(node("h3",r.status));
  for(const m of r.matches.slice(0,30)){
   const card=node("div","");card.className="source";card.append(node("strong",m.name),node("p",m.list+" · OFAC record "+m.uid+" · "+m.match+" · "+m.date),node("p","Source-listed programs: "+(m.programs||[]).join(", ")),node("p","Source-listed address countries: "+((m.countries||[]).join(", ")||"Not stated")));target.append(card);
  }
  if(r.matches.length>30)target.append(node("p","Showing 30 of "+r.matches.length+" candidates. Review full official list."));
  target.append(node("p","An exact name or alias is not proof of identity. Independently compare registration identifiers, addresses, ownership and applicable legal restrictions. No-match is not clearance."));
 }
 async function load(){
  if(busy)return;busy=true;data=null;render();
  try{const r=await fetch("./data/ofac-organizations.json",{cache:"no-store",credentials:"omit",referrerPolicy:"no-referrer",signal:AbortSignal.timeout(15000)});if(!r.ok)throw Error("Unavailable");data=await r.json();}catch{data=null;}finally{busy=false;render();}
 }
 $("supplier-name").oninput=render;$("supplier-reload").onclick=load;
 render();return {load,reset(){$("supplier-name").value="";render();}};
}
