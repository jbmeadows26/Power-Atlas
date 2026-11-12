/* Power Atlas v6 — visual-first editorial stories. Review-only extension.
   Presentation only. All original research, dates, links, and interaction tools are retained. */
(()=>{
"use strict";
const root=document.documentElement;
const documentPath=(location.pathname.split("/").pop()||"index.html").toLowerCase();
const review=location.hostname.includes("visual-review");
const sourceLinks={
  transportation:"https://fred.stlouisfed.org/data/CPITRNSL",
  rent:"https://fred.stlouisfed.org/data/CUSR0000SEHA",
  groceries:"https://fred.stlouisfed.org/data/CUSR0000SAF11",
  "medical care":"https://fred.stlouisfed.org/data/CPIMEDSL"
};
function E(tag,cls,txt){const x=document.createElement(tag);if(cls)x.className=cls;if(txt!==undefined)x.textContent=txt;return x;}
function S(markup){const n=E("div");n.innerHTML=markup.trim();return n.firstElementChild;}
function desc(s){return (s||"").replace(/\s+/g," ").trim();}
function source(a,label){const e=E("a","vs6-source",label||"Source ↗");e.href=a;e.target="_blank";e.rel="noopener noreferrer";return e;}
function accent(c){return {"teal":"#37d5b0","coral":"#ff9c78","violet":"#ae99ff","blue":"#8ab5ff","gold":"#ffcd68"}[c]||"#37d5b0";}
function typeFor(label,index){
 const t=label.toLowerCase();
 if(t.includes("everyday")||t.includes("cost"))return"costs";
 if(t.includes("corporate")||t.includes("own"))return"ownership";
 if(t.includes("consumer")||t.includes("fine print"))return"consumer";
 if(t.includes("political")||t.includes("money")||t.includes("donor"))return"money";
 if(t.includes("market")||t.includes("competition"))return"market";
 if(t.includes("class action")||t.includes("lawsuit"))return"claims";
 if(t.includes("economic")||t.includes("fragil"))return"economy";
 if(t.includes("financial scale")||t.includes("trillion"))return"scale";
 if(t.includes("civic")||t.includes("reform"))return"action";
 return index===4?"evidence":"action";
}
function visual(type){
 const box=E("div","vs6-art vs6-art--"+type);box.setAttribute("aria-label","Graphic: "+type);box.setAttribute("role","img");
 if(type==="ownership"){
  box.append(S('<div class="vs6-owned"><span class="vs6-owned-entity vs6-owned-entity--parent"><i>INVESTOR</i><strong>Thoma Bravo</strong></span><span class="vs6-owned-connector"><b>→</b><small>2021</small></span><span class="vs6-owned-entity vs6-owned-entity--company"><i>COMPANY</i><strong>RealPage</strong></span></div>'));
  box.append(E("span","vs6-art-foot","Documented acquisition · Not proof of local rent effects"));
 }else if(type==="consumer"){
  box.append(S('<div class="vs6-phone-viz"><div class="vs6-phone-outline"><div class="vs6-phone-notch"></div><span class="vs6-phone-tag">THE DEAL</span><strong>“FREE”</strong><span class="vs6-phone-ribbon">Conditions apply</span></div><div class="vs6-phone-stack"><span>Plan requirement</span><span>Monthly credits</span><span>Early-exit costs</span></div></div>'));
  box.append(E("span","vs6-art-foot","Illustration · Always compare total cost"));
 }else if(type==="money"){
  box.append(S('<div class="vs6-money-viz"><div><b>DONOR</b><span class="vs6-money-circle">●</span></div><span class="vs6-money-arrow">→</span><div><b>COMMITTEE</b><span class="vs6-money-circle vs6-money-circle--mid">●</span></div><span class="vs6-money-arrow">→</span><div><b>SPENDING</b><span class="vs6-money-circle vs6-money-circle--end">●</span></div></div>'));
  box.append(E("span","vs6-art-foot","Records show transactions—not proof of bought decisions"));
 }else if(type==="market"){
  box.append(S('<div class="vs6-market-proof"><div class="vs6-market-proofline"><span><strong>85%</strong><small>Top 4 U.S. beef packers<br>Share of steer/heifer purchases</small></span><i style="--p:85%" aria-hidden="true"></i></div><div class="vs6-market-proofline"><span><strong>~80%</strong><small>Top 3 prescription middlemen<br>Share of U.S. claims</small></span><i style="--p:80%" aria-hidden="true"></i></div></div>'));
  box.append(E("span","vs6-art-foot","USDA 2024 · FTC 2023 claims · Separate markets, not price markups"));
 }else if(type==="claims"){
  box.append(S('<div class="vs6-case-viz"><span class="vs6-case-step"><b>1</b>Filed</span><span class="vs6-case-wire"></span><span class="vs6-case-step"><b>2</b>Reviewed</span><span class="vs6-case-wire"></span><span class="vs6-case-step"><b>3</b>Claim?</span></div>'));
  box.append(E("span","vs6-art-foot","Allegation ≠ ruling ≠ payout"));
 }else if(type==="economy"){
  box.append(S('<svg viewBox="0 0 460 170" class="vs6-wave" aria-hidden="true"><defs><linearGradient id="vs6Wave" x1="0" x2="1"><stop offset="0%" stop-color="#8bb9ff"/><stop offset="100%" stop-color="#ffab84"/></linearGradient></defs><path d="M6 102 L52 62 L93 79 L135 31 L178 57 L222 51 L263 132 L309 92 L354 129 L397 66 L454 81" fill="none" stroke="url(#vs6Wave)" stroke-width="9" stroke-linejoin="round" stroke-linecap="round"/><path d="M6 150 H454" stroke="#ffffff50" stroke-width="2"/><circle cx="263" cy="132" r="11" fill="#ffab84"/></svg>'));
  box.append(E("span","vs6-art-foot","Illustrative pathways · Not a crash forecast"));
 }else if(type==="scale"){
  box.append(S('<div class="vs6-scale-viz"><span class="vs6-scale-sm"><i></i><b>$1M</b></span><span class="vs6-scale-md"><i></i><b>$1B</b></span><span class="vs6-scale-lg"><i></i><b>$1T</b></span></div>'));
  box.append(E("span","vs6-art-foot","A trillion is 1,000 × a billion"));
 }else if(type==="costs"){
  box.append(S('<div class="vs6-cost-viz"><span style="--h:44%;--v:#ff9c78">TRANSPORT</span><span style="--h:27%;--v:#37d5b0">RENT</span><span style="--h:23%;--v:#ae99ff">FOOD</span><span style="--h:19%;--v:#ffcd68">HEALTH</span></div>'));
  box.append(E("span","vs6-art-foot","See sourced year-on-year indexes above"));
 }else if(type==="evidence"){
  box.append(S('<div class="vs6-proof-viz"><span><b>✓</b>Measured</span><span><b>↗</b>Documented</span><span><b>?</b>Unknown</span></div>'));
  box.append(E("span","vs6-art-foot","Facts and allegations remain separate"));
 }else{
  box.append(S('<div class="vs6-action-viz"><span class="vs6-action-start">Problem</span><span class="vs6-action-arc">⟶</span><span class="vs6-action-end">Choice</span></div>'));
  box.append(E("span","vs6-art-foot","Compare options and trade-offs"));
 }
 return box;
}
function readMetrics(old){
 const buttons=[...old.querySelectorAll(".pa4-graphic .pa4-bar")];
 return buttons.map((button,i)=>{
  const name=desc(button.querySelector("span")?.textContent);
  const val=Number(desc(button.querySelector("b")?.textContent).replace(/[^0-9.]/g,""));
  const key=name.toLowerCase();
  return{name,value:val,key,url:sourceLinks[key]||"#",element:button,tint:["#ff9c78","#57d7b5","#b09bfb","#ffcd68"][i]};
 }).filter(m=>m.name&&Number.isFinite(m.value)&&m.value>=0);
}
function pathTo(name,original){
 if(review){const p=original?.getAttribute("href")||name;return p.startsWith("https://power-atlas-unified.vercel.app/")?p.replace("https://power-atlas-unified.vercel.app/","/"):p;}
 return original?.getAttribute("href")||name;
}
function go(target,text,cls){const a=E("a",cls||"vs6-go",text||"Explore why →");a.href=target;return a;}
function metricPanel(metrics){
 const panel=E("section","vs6-metrics");panel.setAttribute("aria-label","Comparative price indexes");
 panel.append(E("span","vs6-micro vs6-micro--light","U.S. PRICE SIGNAL · SEP 2026"));
 const headline=E("div","vs6-metrics-head");headline.append(E("strong",null,"What moved most?"),E("small",null,"CPI change vs. Sep 2025"));panel.append(headline);
 if(metrics.length<2){panel.append(E("p","vs6-missing","Source-backed price indexes are unavailable."));return panel;}
 const max=Math.max(1,...metrics.map(x=>x.value));const wrap=E("div","vs6-metric-rows");
 const detail=E("div","vs6-metric-detail");detail.setAttribute("aria-live","polite");
 metrics.forEach((m,i)=>{
  const btn=E("button","vs6-metric");btn.type="button";btn.setAttribute("aria-pressed",String(i===0));
  const label=E("span","vs6-metric-label",m.name);
  const track=E("span","vs6-metric-track");const fill=E("span","vs6-metric-fill");fill.style.width=(m.value/max*100).toFixed(2)+"%";fill.style.background=m.tint;track.append(fill);
  btn.append(label,track,E("strong","vs6-metric-value","+"+m.value.toFixed(2)+"%"));
  btn.addEventListener("click",()=>{
   wrap.querySelectorAll("button").forEach(b=>b.setAttribute("aria-pressed",String(b===btn)));
   m.element.click();
   detail.replaceChildren(E("span",null,m.name+" · +"+m.value.toFixed(2)+"% year over year"),source(m.url,"Original data ↗"));
  });
  wrap.append(btn);
 });
 panel.append(wrap);
 const ticks=E("div","vs6-axis");ticks.append(E("span",null,"0"),E("span",null,"+"+(max/2).toFixed(1)+"%"),E("span",null,"+"+max.toFixed(1)+"%"));panel.append(ticks);
 detail.replaceChildren(E("span",null,metrics[0].name+" · +"+metrics[0].value.toFixed(2)+"% year over year"),source(metrics[0].url,"Original data ↗"));
 panel.append(detail);
 panel.append(E("small","vs6-caveat","National index changes—not your personal bill or proof of cause."));
 return panel;
}
const cardMeta=[
{tag:"OWNERSHIP",heading:"Who owns what?",line:"Follow the company behind the brand.",kind:"ownership",theme:"dark"},
{tag:"CONSUMER WATCH",heading:"The fine-print trap",line:"Shrinking packs, hidden fees, real costs.",kind:"consumer",theme:"peach"},
{tag:"POLITICAL MONEY",heading:"Follow the cash",line:"Follow donors, dark money, lobbying and decisions.",kind:"money",theme:"lilac"},
{tag:"MARKET POWER",heading:"When choice shrinks",line:"See who controls the market—and how it reaches you.",kind:"market",theme:"mint"},
{tag:"CLASS ACTIONS",heading:"Sued isn't paid",line:"Case status matters more than headlines.",kind:"claims",theme:"dark"},
{tag:"ECONOMIC RISK",heading:"Could the shock reach you?",line:"Connect markets with daily life.",kind:"economy",theme:"blue"}
];
/* Homepage ownership rotation uses the canonical graph, not unsourced visual placeholders. */
const ownerThreadIds=["tb-realpage","mars-kellanova","parent-brand-pepsi","parent-brand-tide","general-mills-blue-buffalo","blackstone-tricon","amazon-one-medical","amazon-whole-foods","berkshire-geico","pg-kindercare","cvs-caremark","as-portfolio-fleetpride"];
async function hydrateOwnerCard({graphic,prev,next,counter,links,target}){
 try{
  const res=await fetch("./owner-card-threads.json",{cache:"no-store"});
  if(!res.ok)throw Error("Ownership source unavailable");
  const graph=await res.json();
  if(graph.schema!=="power-atlas.corporate-ownership.evidence-graph.v1")throw Error("Unexpected ownership source");
  const nodes=Object.fromEntries((graph.entities||[]).map(n=>[n.id,n]));
  const refs=Object.fromEntries((graph.relations||[]).map(e=>[e.id,e]));
  const rows=ownerThreadIds.map(id=>refs[id]).filter(e=>e&&nodes[e.from]&&nodes[e.to]&&/^https:\/\/[^ ]+/.test(e.source)&&/^\d{4}-\d{2}-\d{2}$/.test(e.asOf));
  if(rows.length<2)throw Error("Fewer than two sourced ownership threads");
  let active=0;
  function type(n){if(n.kind==="consumer_brand")return"BRAND";if(["private_equity_firm","institutional_investor","investment_shareholder","investment_firm"].includes(n.kind))return"INVESTOR";if((n.kind||"").includes("operator"))return"OPERATOR";return"COMPANY";}
  function render(){
   const e=rows[active],from=nodes[e.from],to=nodes[e.to];
   const owned=graphic.querySelector(".vs6-owned"),note=graphic.querySelector(".vs6-art-foot");
   if(!owned||!note)return;
   const [a,b]=owned.querySelectorAll(".vs6-owned-entity");
   a.querySelector("i").textContent=type(from);a.querySelector("strong").textContent=from.name;
   b.querySelector("i").textContent=type(to);b.querySelector("strong").textContent=to.name;
   owned.querySelector(".vs6-owned-connector small").textContent=e.asOf.slice(0,4);
   const label=e.relation==="ACQUIRED_AND_PORTFOLIO_BACKED"?"Documented acquisition":e.relation==="BENEFICIAL_SHARES"?"Dated shareholding":e.relation==="REPORTS_BRAND_IN_PORTFOLIO"?"Documented brand":e.relation==="LISTED_PORTFOLIO_COMPANY"?"Dated portfolio listing":e.relation==="OPERATES_BUSINESS"?"Documented business relationship":"Source-backed relationship";
   note.textContent=label+" · Not proof of local price effects";
   counter.textContent=(active+1)+" of "+rows.length+" · sourced ownership threads";
   graphic.setAttribute("aria-label",from.name+" to "+to.name+", "+e.asOf+", "+label);
   const url=new URL(target,location.href);url.searchParams.delete("issue");url.searchParams.set("owner",e.from);url.hash="ownership-network";
   links.forEach(l=>{l.href=url.href;l.setAttribute("aria-label","Explore "+from.name+" and "+to.name+" ownership evidence")});
  }
  prev.addEventListener("click",()=>{active=(active-1+rows.length)%rows.length;render()});
  next.addEventListener("click",()=>{active=(active+1)%rows.length;render()});
  prev.disabled=false;next.disabled=false;render();
 }catch(e){counter.textContent="Explore more sourced ownership in the full research";prev.hidden=true;next.hidden=true;}
}


/* Case carousel: court records and documented public-integrity money trails.
   All case names, legal stages, figures and URLs come from the locally deployed
   reviewed index. The order is editorial variety, never a severity ranking. */
async function hydrateInfluenceCard({graphic,prev,next,counter,arrow,cta,sourceLink,heading,description}){
 const preferred=["ohio-firstenergy","illinois-comed","menendez-foreign-influence",
  "usaid-procurement","la-development","fat-leonard-navy","nyc-shelter-2026",
  "vi-police-procurement","nm-school-technology","newark-redevelopment",
  "ct-school-construction","santos-campaign-finance","hawaii-affordable-housing",
  "gsa-construction-bribery","army-hawaii-innovation"];
 const names={
  "ohio-firstenergy":"Ohio: the nuclear bailout",
  "illinois-comed":"Illinois: utility influence",
  "menendez-foreign-influence":"Senate: cash and gold",
  "usaid-procurement":"USAID: contract steering",
  "la-development":"Los Angeles: land deals",
  "fat-leonard-navy":"Navy: gifts for contracts",
  "nyc-shelter-2026":"New York: shelter contracts",
  "vi-police-procurement":"Virgin Islands: public contracts",
  "nm-school-technology":"New Mexico: school technology",
  "newark-redevelopment":"Newark: redevelopment",
  "ct-school-construction":"Connecticut: school construction",
  "santos-campaign-finance":"Congress: donor fraud",
  "hawaii-affordable-housing":"Hawaii: affordable housing",
  "gsa-construction-bribery":"Federal construction: bid steering",
  "army-hawaii-innovation":"Defense: innovation contracts"
 };
 const legal={convicted:"Conviction documented",pleaded:"Guilty plea documented",
  charged:"Charges only — allegations",mixed:"Mixed legal outcomes"};
 try{
  const res=await fetch("./investigations-data.json",{cache:"no-store"});
  if(!res.ok)throw Error("HTTP "+res.status);
  const data=await res.json();
  if(data.schema!=="power-atlas.public-integrity-case-index.v1"||!Array.isArray(data.cases))throw Error("Unexpected case index");
  const byId=Object.fromEntries(data.cases.map(c=>[c.id,c]));
  const rows=preferred.map(id=>byId[id]).filter(c=>c&&c.flow?.length===3&&c.sources?.some(s=>/^https:\/\/www\.justice\.gov\//.test(s.url||"")));
  if(rows.length<10)throw Error("Insufficient source-linked cases");
  let active=0;
  function render(){
   const c=rows[active];
   const caseFile="investigations.html?case="+encodeURIComponent(c.id);
   const evidence=c.sources.find(s=>/^https:\/\/www\.justice\.gov\//.test(s.url||""));
   const path=E("div","vs6-influence-path");
   ["BENEFIT OR PAYMENT","INTERMEDIARY","PUBLIC DECISION"].forEach((tag,i)=>{
    const step=E("div","vs6-influence-step");
    step.append(E("small",null,tag),E("strong",null,c.flow[i]));
    path.append(step);
   });
   const figure=E("div","vs6-influence-figure");
   figure.append(E("strong",null,c.money),E("span",null,c.meaning));
   const status=E("span","vs6-influence-status",legal[c.status]||"Check legal outcome");
   if(c.status==="charged")status.classList.add("vs6-influence-status--charge");
   const foot=E("span","vs6-art-foot","Reviewed public records · No guilt inferred from charges");
   graphic.replaceChildren(status,path,figure,foot);
   graphic.setAttribute("aria-label",c.title+"; "+(legal[c.status]||"case status recorded")+". "+c.flow.join(" to "));
   heading.textContent=names[c.id]||c.title;
   description.textContent=c.region+" · "+c.category;
   counter.textContent=(active+1)+" of "+rows.length+" · reviewed case stories";
   arrow.href=caseFile;cta.href=caseFile;
   arrow.setAttribute("aria-label","Read "+c.title);
   cta.setAttribute("aria-label","Open court records for "+c.title);
   sourceLink.href=evidence.url;
   sourceLink.setAttribute("aria-label","Official source for "+c.title);
  }
  prev.addEventListener("click",()=>{active=(active-1+rows.length)%rows.length;render()});
  next.addEventListener("click",()=>{active=(active+1)%rows.length;render()});
  prev.disabled=false;next.disabled=false;render();
 }catch(err){
  counter.textContent="Case index unavailable · Browse the source library";
  prev.hidden=true;next.hidden=true;sourceLink.hidden=true;
  heading.textContent="Follow documented influence cases";
  description.textContent="Explore official cases, the legal outcomes, and the original evidence.";
  arrow.href=cta.href="investigations.html";
 }
}

function home(){
 const original=document.getElementById("pa4-atlas-home");if(!original)return;
 const metric=readMetrics(original);
 const originalCards=[...original.querySelectorAll(".pa4-tile")];
 const portal=E("section","vs6-home");portal.id="vs6-home";portal.setAttribute("aria-label","Power Atlas visual stories");
 const mast=E("div","vs6-cover");
 const left=E("div","vs6-lead");
 left.append(E("span","vs6-micro","POWER ATLAS · THE BIG PICTURE"));
 const h=E("h1");h.append(E("span",null,"Your bills"),E("em",null,"have a backstory."));left.append(h);
 left.append(E("p","vs6-subtitle","Follow the money, ownership and decisions behind everyday life."));
 const entry=go(pathTo("my-life.html#where",originalCards[0]),"Explore your community ↗","vs6-primary");left.append(entry);
 const note=E("span","vs6-hero-footnote","One big question. Original sources one tap away.");left.append(note);
 mast.append(left,metricPanel(metric));portal.append(mast);
 const sectionTitle=E("div","vs6-gallery-head");sectionTitle.append(E("span","vs6-micro","CHOOSE A THREAD"),E("h2",null,"See the connection."),E("p",null,"Look first. Dive deeper when you're curious."));portal.append(sectionTitle);
 const gallery=E("div","vs6-gallery");
 const mapped=[
  {meta:cardMeta[0],idx:1},{meta:cardMeta[1],idx:2},{meta:cardMeta[2],idx:3},
  {meta:cardMeta[3],idx:7},{meta:cardMeta[4],idx:9},{meta:cardMeta[5],idx:6}
 ];
 mapped.forEach(({meta,idx},i)=>{
  const target=pathTo((originalCards[idx]?.getAttribute("href")||"index.html"),originalCards[idx]);
  const top=E("div","vs6-story-head");top.append(E("span","vs6-micro",meta.tag),E("span","vs6-arrow-icon","↗"));
  const graphic=visual(meta.kind);
  const bottom=E("div","vs6-story-foot");bottom.append(E("h3",null,meta.heading),E("p",null,meta.line),E("span","vs6-story-cta","Explore why →"));
  if(meta.kind==="ownership"){
    // Keep the exact existing V6 ownership card layout. The buttons are siblings of links, never nested inside a link.
    const tile=E("article","vs6-story vs6-story--dark vs6-story--wide vs6-owner-card");
    const arrow=go(target,"↗","vs6-arrow-icon");arrow.setAttribute("aria-label","Explore source-backed corporate ownership");top.lastElementChild.replaceWith(arrow);
    const cta=go(target,"Explore why →","vs6-story-cta vs6-owner-cta");bottom.lastElementChild.replaceWith(cta);
    const controls=E("nav","vs6-owner-controls");controls.setAttribute("aria-label","Browse ownership threads");
    const prev=E("button","vs6-owner-prev","←");prev.type="button";prev.disabled=true;prev.setAttribute("aria-label","Previous ownership relationship");
    const count=E("span","vs6-owner-count","1 of 1 · ownership");count.setAttribute("aria-live","polite");
    const next=E("button","vs6-owner-next","→");next.type="button";next.disabled=true;next.setAttribute("aria-label","Next ownership relationship");
    controls.append(prev,count,next);
    tile.append(top,graphic,bottom,controls);gallery.append(tile);
    hydrateOwnerCard({graphic,prev,next,counter:count,links:[arrow,cta],target});
    return;
  }
  if(meta.kind==="money"){
    // Real public-integrity cases rotate within the approved V6 card,
    // with independent controls and original-source links, not nested links.
    const tile=E("article","vs6-story vs6-story--lilac vs6-story--regular vs6-influence-card");
    const arrow=go("investigations.html","↗","vs6-arrow-icon");
    arrow.setAttribute("aria-label","Browse documented public-integrity cases");
    top.lastElementChild.replaceWith(arrow);
    const heading=bottom.querySelector("h3"),description=bottom.querySelector("p");
    const cta=go("investigations.html","Read the case →","vs6-story-cta");
    bottom.lastElementChild.replaceWith(cta);
    const sourceLink=go("investigations.html","Official source ↗","vs6-influence-source");
    sourceLink.setAttribute("target","_blank");
    sourceLink.setAttribute("rel","noopener noreferrer");
    const controls=E("nav","vs6-influence-controls");
    controls.setAttribute("aria-label","Browse political influence cases");
    const prev=E("button",null,"←");prev.type="button";prev.disabled=true;prev.setAttribute("aria-label","Previous political influence case");
    const counter=E("span",null,"Loading verified cases");counter.setAttribute("aria-live","polite");
    const next=E("button",null,"→");next.type="button";next.disabled=true;next.setAttribute("aria-label","Next political influence case");
    controls.append(prev,counter,next);
    const directory=go("business-candidates.html","Explore 8 more company money trails →","vs6-influence-directory");
    tile.append(top,graphic,bottom,sourceLink,controls,directory);gallery.append(tile);
    hydrateInfluenceCard({graphic,prev,next,counter,arrow,cta,sourceLink,heading,description});
    return;
  }
  if(meta.kind==="consumer"){
    // Separate independent links, not links nested within links.
    const tile=E("article","vs6-story vs6-story--peach vs6-story--regular vs6-consumer-card");
    const feature=go(target,"","vs6-consumer-feature");
    feature.setAttribute("aria-label","The fine-print trap; explore Consumer Watch");
    feature.append(top,graphic,bottom);
    const shortcuts=E("nav","vs6-consumer-shortcuts");
    shortcuts.setAttribute("aria-label","Explore Consumer Watch topics");
    [
      {icon:"📱",label:"Phone deals",url:"consumer-practices.html?story=tmobile#story-lab"},
      {icon:"🏠",label:"Rental fees",url:"consumer-practices.html?story=progress#story-lab"},
      {icon:"↻",label:"Subscriptions",url:"consumer-practices.html?story=amazon#story-lab"},
      {icon:"✈",label:"Travel extras",url:"consumer-practices.html?story=hopper#story-lab"},
      {icon:"📦",label:"Shrinking packages",url:"consumer-practices.html#shrinkflation"},
      {icon:"☎",label:"Automated support",url:"service-accountability.html"},
      {icon:"⚖",label:"Class actions",url:"https://power-atlas-unified.vercel.app/class-actions.html"}
    ].forEach(item=>{
      const shortcut=go(item.url,"","vs6-consumer-shortcut");
      shortcut.setAttribute("aria-label","Explore "+item.label);
      shortcut.append(E("span","vs6-consumer-shortcut-icon",item.icon),E("span","vs6-consumer-shortcut-label",item.label),E("span","vs6-consumer-shortcut-arrow","↗"));
      shortcuts.append(shortcut);
    });
    tile.append(feature,shortcuts,E("span","vs6-consumer-note","Company terms, allegations and legal findings are labeled separately."));
    gallery.append(tile);return;
  }
  const a=go(target,"","vs6-story vs6-story--"+meta.theme+" vs6-story--"+(i%3===0?"wide":"regular"));
  a.setAttribute("aria-label",meta.heading+"; explore full sourced story");
  if(meta.kind==="market")a.href="market-power.html";
  a.append(top,graphic,bottom);gallery.append(a);
 });
 // Same V6 card system and one primary navigation: tax investigation is a research thread.
 const taxStory=go("wealth-advantage.html","","vs6-story vs6-story--blue vs6-story--regular");
 taxStory.setAttribute("aria-label","Compare the tax treatment of households, small businesses and high-wealth owners");
 const taxTop=E("div","vs6-story-head");taxTop.append(E("span","vs6-micro","THE WEALTH ADVANTAGE"),E("span","vs6-arrow-icon","↗"));
 const taxArt=E("div","vs6-art vs6-art--money");taxArt.setAttribute("role","img");taxArt.setAttribute("aria-label","Three-column comparison: household, small business and wealthy owner");
 const taxChart=E("div","vs6-proof-viz");taxChart.append(E("span",null,"🏠 Household"),E("span",null,"🧰 Business"),E("span",null,"◆ Wealth"));taxArt.append(taxChart,E("span","vs6-art-foot","10 IRS-sourced tax comparisons · Rules and limits included"));
 const taxBottom=E("div","vs6-story-foot");taxBottom.append(E("h3",null,"Same rules. Different scale."),E("p",null,"Cars, private jets, investment gains and inherited wealth."),E("span","vs6-story-cta","Compare every advantage →"));
 taxStory.append(taxTop,taxArt,taxBottom);gallery.append(taxStory);
 portal.append(gallery);
 const rest=E("details","vs6-more");rest.append(E("summary",null,"Four more stories +"));
 const extras=E("div","vs6-extra-grid");
 [{i:0,label:"Your everyday costs",kind:"costs"},{i:4,label:"What is actually proven?",kind:"evidence"},{i:5,label:"What could change?",kind:"action"},{i:8,label:"How big is a trillion?",kind:"scale"}].forEach(o=>{
   const a=go(pathTo((originalCards[o.i]?.getAttribute("href")||"index.html"),originalCards[o.i]),"","vs6-extra");
   a.textContent="";a.append(visual(o.kind),E("strong",null,o.label),E("span",null,"Explore →"));extras.append(a);
 });rest.append(extras);portal.append(rest);
 const footer=E("div","vs6-research-gate");
 footer.append(E("span","vs6-micro","ALL THE DATA IS STILL HERE"),E("h2",null,"Want the receipts?"));
 const btn=E("button","vs6-research-button","Open full research ↗");btn.type="button";btn.setAttribute("aria-expanded","false");
 btn.addEventListener("click",()=>{
   const old=document.querySelector(".pa5-library-button");
   document.body.classList.toggle("vs6-full-research");
   const expanded=document.body.classList.contains("vs6-full-research");
   btn.textContent=expanded?"Hide full research ↑":"Open full research ↗";
   btn.setAttribute("aria-expanded",String(expanded));
   if(old&&old.getAttribute("aria-expanded")!==String(expanded))old.click();
   if(expanded){const x=document.querySelector(".pa5-library")||document.querySelector("main > section:not(.pa4-home)");x?.scrollIntoView({behavior:"smooth",block:"start"});}
 });
 footer.append(btn);portal.append(footer);
 original.classList.add("vs6-superseded");
 original.insertAdjacentElement("beforebegin",portal);
 document.body.classList.add("vs6-home-mode");
 if(location.hash)document.body.classList.add("vs6-full-research");
}
function topicKind(){
 const p=documentPath;
 if(p.includes("consumer")||p.includes("telecom")||p.includes("service-accountability"))return"consumer";
 if(p.includes("corporate")||p.includes("business"))return"ownership";
 if(p.includes("market-power"))return"market";
 if(p.includes("money-scale"))return"scale";
 if(p.includes("class-action")||p.includes("source-audit")||p.includes("investigation"))return"claims";
 if(p.includes("economic"))return"economy";
 if(p.includes("reform"))return"action";
 if(p.includes("my-life")||p.includes("cost-gap"))return"costs";
 return"money";
}
const topicCopy={
 "my-life.html":["Your ZIP. Your everyday costs.","Explore the local context, then follow the evidence."],
 "corporate-ownership.html":["Who owns the companies?","Documented ownership is a starting point—not proof of higher prices."],
 "consumer-practices.html":["The real cost of a deal","Follow the conditions behind the advertised price."],
 "class-actions.html":["A lawsuit isn't a refund.","Follow case status before checking a claim."],
 "market-power.html":["Who gains when choices shrink?","See what concentration data can—and can't—establish."],
 "dark-money.html":["Who funds power—and who benefits?","Follow campaign cash, dark money and lobbying. Separate the public records from unproven influence."],
 "money-scale.html":["Make billions feel real.","Compare numbers using the same units."],
 "service-accountability.html":["Where did the people go?","Investigate documented staffing and reported service gaps."],
 "economic-fragility.html":["Could market stress reach you?","Possible pathways are not predictions."],
 "reform-lab.html":["How can rules change?","See choices and trade-offs, not slogans."],
 "source-audit.html":["What's proven?","Know what is measured, documented, alleged or missing."]
};

/* Location-aware source chart: one user ZIP, four different Census ZCTA measures.
   Values arrive via the validated existing Census definitions in my-life.html.
   Indicators are NOT local retail prices, insurance premiums, fares or tax claims. */
function attachZIPVisual(section){
 if(documentPath!=="my-life.html")return;
 const art=section.querySelector(":scope > .vs6-art");
 if(!art||art.querySelector(".vs6-zip-live"))return;
 art.classList.add("vs6-zip-chart");
 const host=E("div","vs6-zip-live");
 const heading=E("div","vs6-zip-heading");
 const kicker=E("span","vs6-zip-kicker","YOUR LOCAL PICTURE");
 const place=E("strong","vs6-zip-place","Enter a ZIP to see your area");
 const note=E("small","vs6-zip-period","Market asking rents where verified · Census household indicators · separate HUD program data");
 heading.append(kicker,place,note);
 const grid=E("div","vs6-zip-grid");
 const foot=E("div","vs6-zip-footer");
 foot.append(E("span",null,"Market rent = advertised listings, not signed leases. HUD voucher benchmarks are shown separately; Census household estimates are historical."));
 const link=E("a","vs6-zip-method","How these figures are sourced ↗");
 link.href="https://www.census.gov/data/developers/data-sets/acs-5year.html";
 link.target="_blank";link.rel="noopener noreferrer";foot.append(link);
 const hudLink=E("a","vs6-zip-method","HUD bedroom benchmark source ↗");
 hudLink.href="https://www.huduser.gov/portal/datasets/fmr/smallarea/index.html";
 hudLink.target="_blank";hudLink.rel="noopener noreferrer";foot.append(hudLink);
 host.append(heading,grid,foot);
 art.replaceChildren(host);
 const topics=[
   {key:"housing",label:"MARKET ASKING RENT",desc:"Provider-reported listing averages by bedroom · not HUD program rents",color:"#39d4b0"},
   {key:"transport",label:"TRANSPORT",desc:"Commuters using transit",color:"#ff9d77"},
   {key:"groceries",label:"FOOD",desc:"Households on SNAP",color:"#ae98fd"},
   {key:"health",label:"HEALTH",desc:"Residents uninsured",color:"#ffce70"}
 ];
 const nodes=new Map();
 let currentZip="";
 let lastMarketResult=null;
 let activeHomeType="all";
 topics.forEach((t,i)=>{
   const tile=E("div","vs6-zip-tile");
   if(t.key==="housing")tile.classList.add("vs6-zip-tile--housing");
   tile.style.setProperty("--zip-accent",t.color);
   const top=E("div","vs6-zip-tile-top");
   top.append(E("span","vs6-zip-tile-number",String(i+1).padStart(2,"0")),E("strong","vs6-zip-tile-label",t.label));
   const local=E("strong","vs6-zip-tile-value","—");
   const title=E("span","vs6-zip-tile-title",t.desc);
   // One zero-based numerical axis per metric, shared by ZIP and U.S.
   // Never normalize either bar to the largest observation.
   const chart=E("div","vs6-zip-comparison");
   chart.setAttribute("role","img");
   const own=E("div","vs6-zip-comparison-row");
   const ownLabel=E("span","vs6-zip-comparison-name","ZIP area");
   const ownTrack=E("span","vs6-zip-track");const ownFill=E("span","vs6-zip-fill");
   const ownValue=E("strong","vs6-zip-comparison-value","—");
   ownTrack.append(ownFill);own.append(ownLabel,ownTrack,ownValue);
   const us=E("div","vs6-zip-comparison-row");
   const usLabel=E("span","vs6-zip-comparison-name","U.S.");
   const usTrack=E("span","vs6-zip-track");const usFill=E("span","vs6-zip-fill vs6-zip-fill--us");
   const usValue=E("strong","vs6-zip-comparison-value","—");
   usTrack.append(usFill);us.append(usLabel,usTrack,usValue);
   const axis=E("div","vs6-zip-comparison-axis");
   const ticks=E("div","vs6-zip-axis-ticks");
   ticks.append(E("span",null,"0%"),E("span",null,"—"),E("span",null,"—"));
   axis.append(ticks);
   chart.append(own,us,axis);
   const compare=E("small","vs6-zip-compare","Select a ZIP to compare");
   const detail=E("button","vs6-zip-detail","Explore this issue ↗");detail.type="button";
   detail.addEventListener("click",()=>{
     if(t.key==="housing"){
       const rentPanel=document.getElementById("pa-hud-safmr");
       if(rentPanel&&!rentPanel.hidden)rentPanel.scrollIntoView({behavior:"smooth",block:"start"});
       else document.getElementById("where")?.scrollIntoView({behavior:"smooth",block:"start"});
       return;
     }
     const open=section.querySelector(".vs6-expand");
     if(open?.getAttribute("aria-expanded")==="false")open.click();
     const choice=document.querySelector('#issueGrid button[data-topic="'+t.key+'"]');
     if(choice)choice.click();
     const issue=document.getElementById("issueResult")||document.getElementById("what");
     issue?.scrollIntoView({behavior:"smooth",block:"start"});
   });
   const bedrooms=t.key==="housing"?E("div","vs6-zip-bedroom-list"):null;
   if(bedrooms){
     bedrooms.setAttribute("aria-label","Advertised market asking rents by property type and bedroom");
     local.hidden=true;
     chart.hidden=true;
     detail.textContent="Compare with separate HUD voucher benchmark ↓";
     compare.textContent="Enter ZIP to check whether current listing-market rent data are available.";
   }
   tile.append(top,local,title);
   let typeSelect=null;
   if(bedrooms){
     const filter=E("label","vs6-zip-market-filter");
     filter.append(E("span",null,"Property type"));
     typeSelect=E("select","vs6-zip-market-select");
     typeSelect.setAttribute("aria-label","Filter advertised market rent by property type");
     for(const [value,label] of [["all","All homes"],["apartment_condo","Apartments & condos"],["house","Houses"],["townhouse","Townhomes"]]){
       const option=E("option",null,label);option.value=value;typeSelect.append(option);
     }
     typeSelect.addEventListener("change",()=>{
       activeHomeType=typeSelect.value;
       if(lastMarketResult?.zip===currentZip)renderMarket();
     });
     filter.append(typeSelect);
     tile.append(filter);
   }
   if(bedrooms)tile.append(bedrooms);
   tile.append(chart,compare,detail);
   grid.append(tile);
   nodes.set(t.key,{local,compare,chart,ownFill,usFill,ownValue,usValue,ticks,us,bedrooms,typeSelect});
 });
 function paint(event){
   const d=event?.detail;if(!d||!/^\d{5}$/.test(d.zip||""))return;
   place.textContent=d.place+" · "+d.zip;
   note.textContent=lastMarketResult?.zip===d.zip&&lastMarketResult?.status==="ready"?
     "Listing-market snapshot · "+lastMarketResult.market.snapshotMonth+" · citywide, not ZIP-specific · Census historical context":
     "Census ACS 2020–2024 household indicators · market asking-rent coverage separately verified";
   currentZip=d.zip;
   const metrics=new Map((d.metrics||[]).map(m=>[m.key,m]));
   for(const t of topics){
     const els=nodes.get(t.key),m=metrics.get(t.key);
     if(t.key==="housing"){
       // A 5-year all-unit ACS median and HUD voucher limits are not asking rents.
       els.chart.hidden=true;
       els.local.hidden=true;
       if(!lastMarketResult||lastMarketResult.zip!==d.zip){
         els.bedrooms.replaceChildren();
         els.compare.textContent="Checking independently sourced listing-market averages for this area…";
       }
       continue;
     }
     const have=Number.isFinite(m?.localValue)&&Boolean(m?.localText);
     const percentage=(m?.format==="share"||m?.format==="sumshare");
     const validLocal=have&&percentage&&m.localValue>=0&&m.localValue<=100;
     const hasUs=validLocal&&Number.isFinite(m.usValue)&&m.usValue>=0&&m.usValue<=100&&Boolean(m.usText);
     els.local.textContent=have?m.localText:d.status==="loading"?"…":"Unavailable";
     els.local.classList.toggle("vs6-zip-tile-value--unavailable",!have);
     els.chart.hidden=!validLocal;
     if(validLocal){
       // The two bars share a labeled axis that starts at zero. A rounded
       // ceiling leaves headroom, unlike the old maximum-equals-100%-width
       // presentation that made small survey percentages look oversized.
       const largest=Math.max(m.localValue,hasUs?m.usValue:0);
       const ceiling=Math.min(100,Math.max(5,Math.ceil(largest*1.08/5)*5));
       const midpoint=ceiling/2;
       const tick=n=>(Number.isInteger(n)?String(n):n.toFixed(1))+"%";
       els.ticks.replaceChildren(E("span",null,"0%"),E("span",null,tick(midpoint)),E("span",null,tick(ceiling)));
       els.ownFill.style.width=(100*m.localValue/ceiling).toFixed(2)+"%";
       els.usFill.style.width=hasUs?(100*m.usValue/ceiling).toFixed(2)+"%":"0%";
       els.ownValue.textContent=m.localText;
       els.usValue.textContent=hasUs?m.usText:"";
       els.us.hidden=!hasUs;
       els.chart.setAttribute("aria-label",
         t.desc+": ZIP area "+m.localText+
         (hasUs?", United States "+m.usText:"; U.S. comparison unavailable")+
         ". Both bars begin at zero on the same 0%–"+tick(ceiling)+" axis.");
       const difference=hasUs?Math.abs(m.localValue-m.usValue).toFixed(1):null;
       const delta=hasUs?
         Number(difference)===0?"Same as U.S. · "+d.survey:
         difference+" percentage points "+(m.localValue>m.usValue?"above":"below")+" U.S. · "+d.survey:
         "U.S. comparison unavailable · "+d.survey;
       els.compare.replaceChildren(E("span",null,delta));
       if(m.source&&/^https:\/\//.test(m.source)){
         const link=E("a",null,"Source ↗");link.href=m.source;link.target="_blank";link.rel="noopener noreferrer";els.compare.append(link);
       }
     }else{
       els.compare.textContent=d.status==="loading"?"Retrieving verified figures…":
         have?"Source metric is not a comparable percentage; no bar shown.":
         "This measure was not returned. No estimate inferred.";
     }
   }
 }
 window.addEventListener("poweratlas:zip-visual-context",paint);
 // A saved ZIP may finish loading before V6 mounts. Restore that exact
 // source-backed snapshot; do not fabricate fallback measurements.
 if(window.PowerAtlasLastZIPVisualContext)paint({detail:window.PowerAtlasLastZIPVisualContext});
 function renderMarket(){
   const els=nodes.get("housing"),d=lastMarketResult;
   if(!els?.bedrooms||!d||d.zip!==currentZip)return;
   els.bedrooms.replaceChildren();
   els.chart.hidden=true;
   if(d.status!=="ready"||!d.market){
     els.compare.textContent="No verified, recent asking-rent figures for this ZIP. HUD values are not substituted for market prices.";
     if(els.typeSelect)els.typeSelect.disabled=true;
     return;
   }
   if(els.typeSelect)els.typeSelect.disabled=false;
   const market=d.market,type=market.propertyTypes?.[activeHomeType];
   if(!type){
     els.compare.textContent="No verified property-type breakdown in this snapshot.";
     return;
   }
   for(const [label,key] of [["1 BR","1"],["2 BR","2"],["3 BR","3"],["4 BR","4"]]){
     const value=type.bedrooms?.[key];
     const item=E("div","vs6-zip-bedroom-cell");
     item.append(E("small","vs6-zip-bedroom-name",label),
       E("strong","vs6-zip-bedroom-price",Number.isFinite(value)&&value>0?
         "$"+Math.round(value).toLocaleString("en-US"):"Not reported"));
     els.bedrooms.append(item);
   }
   els.compare.replaceChildren(E("span",null,
     market.source.name+" · "+market.source.publishedPeriod+
     " · "+market.geography.name+" citywide, not exact ZIP · average advertised rents, not signed leases · individual subgroup counts undisclosed."));
   const link=E("a",null,"Source ↗");
   link.href=market.source.url;link.target="_blank";link.rel="noopener noreferrer";
   els.compare.append(link);
   note.textContent="Listing-market averages · "+market.source.publishedPeriod+
     " · citywide, not ZIP-specific · Census ACS historical indicators";
 }
 window.addEventListener("poweratlas:market-rent-ready",(event)=>{
   const d=event?.detail;
   if(!d||d.zip!==currentZip)return;
   lastMarketResult=d;
   renderMarket();
 });
 if(window.PowerAtlasLastMarketRent?.zip===currentZip){
   lastMarketResult=window.PowerAtlasLastMarketRent;
   renderMarket();
 }
}

function topic(){if(documentPath==="corporate-ownership.html")return;
 if(documentPath==="index.html")return;
 const main=document.querySelector("main");if(!main||document.querySelector(".vs6-topic"))return;
 const former=main.querySelector(".pa5-topic-hero");
 if(!former)return;
 const kind=topicKind();
 const fallback=[desc(former.querySelector("h2")?.textContent)||"Explore the evidence.",desc(former.querySelector(".pa5-intro p")?.textContent)||"Follow the facts and what remains unknown."];
 const copy=topicCopy[documentPath]||fallback;
 const section=E("section","vs6-topic vs6-topic--"+kind);
 const isPlaceStory=documentPath==="my-life.html";
 const intro=isPlaceStory?E("div","vs6-intro"):section;
 intro.append(E("span","vs6-micro","THE STORY IN 10 SECONDS"),E("h1",null,copy[0]),E("p","vs6-topic-summary",copy[1]));
 if(isPlaceStory){section.classList.add("vs6-topic-cover");section.append(intro);}
 /* A compact V6 infographic is always the opening visual. Detailed exploratory
    controls are preserved but revealed only when requested, not shown as a
    competing 1,300px page-long first screen. */
 const art=visual(kind);section.append(art);
 if(documentPath==="market-power.html"&&window.PowerAtlasMarketPower){window.PowerAtlasMarketPower.mount(section);}
 else if(documentPath==="dark-money.html"&&window.PowerAtlasPoliticalMoney){window.PowerAtlasPoliticalMoney.mount(section);}
 if(documentPath==="consumer-practices.html"){
   const peek=E("div","vs6-evidence-peek");
   peek.setAttribute("aria-label","Available consumer investigations");
   ["Deceptive deals","Shrinkflation","Class actions"].forEach(label=>peek.append(E("span",null,label)));
   section.append(peek);
 }
 if(documentPath==="corporate-ownership.html")section.append(source("https://www.realpage.com/news/thoma-bravo-completes-acquisition-of-realpage/","Original acquisition announcement ↗"));
 const collapsedCTA=documentPath==="consumer-practices.html"?"See cases, comparisons & sources ↗":"Explore the evidence ↗";
 const cta=E("button","vs6-primary vs6-expand",collapsedCTA);cta.type="button";cta.setAttribute("aria-expanded","false");
 cta.addEventListener("click",()=>{
   const active=section.classList.toggle("vs6-expanded");
   document.body.classList.toggle("vs6-topic-expanded",active);
   cta.setAttribute("aria-expanded",String(active));cta.textContent=active?"Back to the big picture ↑":collapsedCTA;
   const explorer=main.querySelector(".pa5-explorer");
   if(active){
     const pathways=section.querySelector(".pmx,.mpx");
     if(pathways){pathways.scrollIntoView({behavior:"smooth",block:"start"});}
     else {
       const first=explorer?.querySelector(".pa5-chapter-card");
       if(first){first.click();}
       else {const sec=main.querySelector(":scope > section:not(.vs6-topic):not(.pa5-topic-hero)");sec?.scrollIntoView({behavior:"smooth",block:"start"});}
     }
   }else section.scrollIntoView({behavior:"smooth",block:"start"});
 });
 if(documentPath==="consumer-practices.html"){
   // A visible, concise graphical path makes Consumer Watch useful even before
   // readers expand the detailed evidence. The original evidence remains intact.
   const shortcuts=E("nav","vs6-topic-shortcuts");
   shortcuts.setAttribute("aria-label","Explore Consumer Watch investigations");
   const subjects=[
     ["▦","SHRINKFLATION","Less inside. Higher unit cost.","#shrinkflation"],
     ["▤","PHONE DEALS","Compare the total plan cost.","telecom-promotions.html"],
     ["◉","CLASS ACTIONS","Lawsuit status is not a payout.","class-actions.html"]
   ];
   for(const [symbol,title,note,url] of subjects){
     const link=E("a","vs6-topic-shortcut");link.href=url;
     link.append(E("span","vs6-topic-shortcut-icon",symbol));
     const caption=E("span","vs6-topic-shortcut-copy");
     caption.append(E("strong",null,title),E("small",null,note));
     link.append(caption,E("span","vs6-topic-shortcut-arrow","↗"));
     if(url.startsWith("#")){
       link.addEventListener("click",event=>{
         event.preventDefault();
         if(!document.body.classList.contains("vs6-topic-expanded"))cta.click();
         const id=url.slice(1);
         const chapter=main.querySelector('.pa5-chapter-card[aria-controls="'+id+'"]');
         chapter?.click();
         const target=document.getElementById(id);
         if(target)target.scrollIntoView({behavior:window.matchMedia("(prefers-reduced-motion: reduce)").matches?"auto":"smooth",block:"start"});
         history.replaceState(null,"",url);
       });
     }
     shortcuts.append(link);
   }
   section.append(shortcuts);
 }
 if(isPlaceStory)intro.append(cta);else section.append(cta);
 former.classList.add("vs6-superseded");
 main.prepend(section);
 document.body.classList.add("vs6-topic-mode");
 attachZIPVisual(section);
 if(documentPath==="my-life.html"){
  const zip=document.getElementById("where");if(zip){const label=E("a","vs6-zip-link",window.PowerAtlasZIP?.get?.()?"Change ZIP ↗":"Enter your ZIP ↓");label.href="#where";intro.append(label);}
 }
 if(location.hash&&location.hash!=="#market-power-pathways"&&!(documentPath==="my-life.html"&&location.hash==="#where")){document.body.classList.add("vs6-topic-expanded");cta.setAttribute("aria-expanded","true");cta.textContent="Back to the big picture ↑";}
}
function compactNav(){
 let header=document.getElementById("pa-global-header");
 if(!header){
   // The Research frontend has a different legacy shell and no global header.
   // Supply the same compact navigation, retaining all original research sections.
   header=E("div","vs6-research-nav");
   header.id="pa-global-header";
   header.setAttribute("aria-label","Power Atlas primary navigation");
   const shell=E("div","pa-global-inner");
   const brand=E("a","pa-global-brand","◇ POWER ATLAS");
   brand.href="https://power-atlas-unified.vercel.app/my-life.html#where";
   brand.setAttribute("aria-label","Power Atlas — Start Here");
   const nav=E("nav","pa-global-links");
   nav.setAttribute("aria-label","Explore Power Atlas");
   // One canonical visitor journey, on both the Unified and Research origins.
   // Topic-specific research stays in the page, never in a competing masthead.
   // Keep review/unified navigation on its current origin. Research-site routes
   // intentionally lead back to the public unified experience.
   const host=location.hostname.toLowerCase();
   const onUnified=host.startsWith("power-atlas-unified")||
     host.startsWith("power-atlas-visual-review")||
     host==="localhost"||host==="127.0.0.1";
   const base=onUnified?new URL("/",location.href).href:
     "https://power-atlas-unified.vercel.app/";
   [
     ["place","Start Here","my-life.html#where"],
     ["issues","Issues","my-life.html#what"],
     ["costs","Costs","my-life.html#benchmarkStory"],
     ["why","The Why","my-life.html#why"],
     ["action","Actions","take-action.html"],
     ["research","Research","index.html"]
   ].forEach(([key,title,path])=>{
     const a=E("a",null,title);
     a.dataset.paNav=key;
     a.href=base+path;
     nav.append(a);
   });
   shell.append(brand,nav);
   header.append(shell);
   document.body.prepend(header);
 }
 const inner=header.querySelector(".pa-global-inner");
 const nav=header.querySelector(".pa-global-links");
 // The dedicated action page replaces the old My Life section as the action destination.
 const actionLink=nav?.querySelector('a[data-pa-nav="action"]');
 if(actionLink){const host=location.hostname.toLowerCase();const local=host.startsWith("power-atlas-unified")||host.startsWith("power-atlas-visual-review")||host==="localhost"||host==="127.0.0.1";actionLink.href=local?"take-action.html":"https://power-atlas-unified.vercel.app/take-action.html";}
 if(!inner||!nav||header.querySelector(".vs6-nav-toggle"))return;
 // Keep one active journey even when a legacy page had no preselected nav item.
 // Community pages own their in-page section state; all other sections use this route map.
 if(documentPath!=="my-life.html"){
   const active=documentPath==="take-action.html"?"action":["consumer-practices.html","telecom-promotions.html","service-accountability.html","cost-gap.html"].includes(documentPath)?"costs":"research";
   nav.querySelectorAll("a[data-pa-nav]").forEach(a=>{
     if(a.dataset.paNav===active)a.setAttribute("aria-current","page");
     else a.removeAttribute("aria-current");
   });
 }
 nav.id="vs6-primary-navigation";
 const button=E("button","vs6-nav-toggle","Explore menu ☰");
 button.type="button";button.setAttribute("aria-controls",nav.id);button.setAttribute("aria-expanded","false");
 button.setAttribute("aria-label","Open all Power Atlas sections");
 const toggle=(open,focus)=>{
   header.classList.toggle("vs6-nav-open",open);
   button.setAttribute("aria-expanded",String(open));
   button.setAttribute("aria-label",open?"Close Power Atlas sections":"Open all Power Atlas sections");
   button.textContent=open?"Close menu ×":"Explore menu ☰";
   if(focus)button.focus();
 };
 button.addEventListener("click",()=>toggle(!header.classList.contains("vs6-nav-open"),false));
 nav.addEventListener("click",e=>{if(e.target.closest("a"))toggle(false,false);});
 // Listen on the document: Escape must work even when focus has left the header.
 document.addEventListener("keydown",e=>{
   if(e.key==="Escape"&&header.classList.contains("vs6-nav-open")){
     e.preventDefault();
     toggle(false,true);
   }
 });
 inner.append(button);
}
function init(){
 if(root.dataset.vs6==="active")return;
 const v4=document.querySelector("#pa4-atlas-home");
 // The Research archive intentionally has its own evidence-rich body, but must
 // share the same persistent global navigation and visual tokens.
 if(documentPath==="index.html"&&!v4){
   root.dataset.vs6="active";
   compactNav();
   return;
 }
 root.dataset.vs6="active";
 compactNav();
 documentPath==="index.html"?home():topic();
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init,{once:true});else init();
})();
