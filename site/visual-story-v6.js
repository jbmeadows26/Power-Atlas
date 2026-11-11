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
  const res=await fetch("https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/main/data/corporate-ownership/verified-relationships-v1.json");
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
function topic(){if(documentPath==="corporate-ownership.html")return;
 if(documentPath==="index.html")return;
 const main=document.querySelector("main");if(!main||document.querySelector(".vs6-topic"))return;
 const former=main.querySelector(".pa5-topic-hero");
 if(!former)return;
 const kind=topicKind();
 const fallback=[desc(former.querySelector("h2")?.textContent)||"Explore the evidence.",desc(former.querySelector(".pa5-intro p")?.textContent)||"Follow the facts and what remains unknown."];
 const copy=topicCopy[documentPath]||fallback;
 const section=E("section","vs6-topic vs6-topic--"+kind);
 section.append(E("span","vs6-micro","THE STORY IN 10 SECONDS"),E("h1",null,copy[0]),E("p","vs6-topic-summary",copy[1]));
 if(documentPath==="market-power.html"&&window.PowerAtlasMarketPower){window.PowerAtlasMarketPower.mount(section);}else if(documentPath==="dark-money.html"&&window.PowerAtlasPoliticalMoney){window.PowerAtlasPoliticalMoney.mount(section);}else{const art=visual(kind);section.append(art);}
 if(documentPath==="corporate-ownership.html")section.append(source("https://www.realpage.com/news/thoma-bravo-completes-acquisition-of-realpage/","Original acquisition announcement ↗"));
 const cta=E("button","vs6-primary vs6-expand","Explore the evidence ↗");cta.type="button";cta.setAttribute("aria-expanded","false");
 cta.addEventListener("click",()=>{
   const active=section.classList.toggle("vs6-expanded");
   document.body.classList.toggle("vs6-topic-expanded",active);
   cta.setAttribute("aria-expanded",String(active));cta.textContent=active?"Back to the big picture ↑":"Explore the evidence ↗";
   const explorer=main.querySelector(".pa5-explorer");
   if(active){
     const requested=documentPath==="market-power.html"?explorer?.querySelector('button.pa5-chapter-card[aria-controls="explore"]'):null;
     const first=requested||explorer?.querySelector(".pa5-chapter-card");
     if(first){first.click();}else{const sec=main.querySelector(":scope > section:not(.vs6-topic):not(.pa5-topic-hero)");sec?.scrollIntoView({behavior:"smooth",block:"start"});}
   }else section.scrollIntoView({behavior:"smooth",block:"start"});
 });
 section.append(cta);
 former.classList.add("vs6-superseded");
 main.prepend(section);
 document.body.classList.add("vs6-topic-mode");
 if(documentPath==="my-life.html"){
  const zip=document.getElementById("where");if(zip){const label=E("a","vs6-zip-link","Enter your ZIP ↓");label.href="#where";section.append(label);}
 }
 if(location.hash&&location.hash!=="#market-power-pathways"){document.body.classList.add("vs6-topic-expanded");cta.setAttribute("aria-expanded","true");cta.textContent="Back to the big picture ↑";}
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
     ["action","Actions","my-life.html#how"],
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
 if(!inner||!nav||header.querySelector(".vs6-nav-toggle"))return;
 // Keep one active journey even when a legacy page had no preselected nav item.
 // Community pages own their in-page section state; all other sections use this route map.
 if(documentPath!=="my-life.html"){
   const active=["consumer-practices.html","telecom-promotions.html","service-accountability.html","cost-gap.html"].includes(documentPath)?"costs":"research";
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
