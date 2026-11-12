/* Shared Power Atlas story-and-chart layer.
   Adds progressive visual explanation without changing page data connectors. */
(()=>{"use strict";
const path=location.pathname.split("/").pop()||"index.html";
const researchSurface=location.hostname.includes("research")||document.body.classList.contains("pa-research-site");
const config={
"index.html":{title:"From your bill to the decision behind it",intro:"Start with what you pay, follow documented drivers, then examine your options.",steps:[["Start with everyday costs","Housing, food, transport and healthcare"],["Follow the evidence","See who sets prices, rules and incentives"],["Understand your options","Inspect sources and practical alternatives"]],jump:"my-life.html#where",jumpLabel:"Explore my community",chart:"bls"},
"my-life.html":{title:"See the cost. Trace the cause. Explore a solution.",intro:"Every story should connect an everyday problem with a supported explanation.",steps:[["Choose an expense","Housing, transport, groceries, health and more"],["See what drives it","Market forces, companies, officials and laws"],["Find your next step","Compare your options and verify the evidence"]],jump:"#what",jumpLabel:"Explore the issues",chart:"bls"},
"business-candidates.html":{title:"A donation is a lead—not proof of a favor",steps:[["Identify the contributor","Distinguish parent, PAC and subsidiary"],["Match government records","Inspect dates, recipients and contracts"],["Test the connection","Separate documented links from unknowns"]],jump:"business-influence.html",jumpLabel:"Explore business outcomes"},
"business-influence.html":{title:"Follow the trail, not the assumption",steps:[["Record the money","PAC donations and lobbying records"],["Examine public business","Contracts, grants and decisions"],["Evaluate evidence","Check timing, identity and alternative explanations"]],jump:"business-candidates.html",jumpLabel:"Open company investigations"},
"corporate-ownership.html":{title:"From the brand to the owner",steps:[["Identify the brand","Who sells the product or service?"],["Follow verified ownership","Map parent and subsidiary relationships"],["Test the price effect","Ownership alone does not prove a price increase"]],jump:"my-life.html#what",jumpLabel:"See everyday costs"},
"dark-money.html":{title:"Trace political cash until the record stops",steps:[["Start at a committee","Find an actual filing and amount"],["Follow reported transfers","Check recipients, dates and reporting rules"],["Mark the unknowns","Opaque original funding is not proof of crime"]],jump:"money-sources.html",jumpLabel:"Inspect source filings",chart:"fec"},
"donor-intelligence.html":{title:"Who gives the most—and what can that tell us?",steps:[["Review the donor list","Published totals in defined periods"],["Compare election cycles","Keep categories and deadlines consistent"],["Find the evidence gap","Donation size alone cannot prove influence"]],jump:"dark-money.html",jumpLabel:"Explore the money trail",chart:"donors"},
"election-money.html":{title:"Put every election's dollars on the same scale",steps:[["Pick a cycle","Use the same reporting window"],["Compare receipts","Separate committee types and spending"],["Check the public filing","Avoid mixing preliminary and final totals"]],jump:"donor-intelligence.html",jumpLabel:"Explore major donors",chart:"fec"},
"money-sources.html":{title:"Where does the number come from?",steps:[["See the reported total","Use an official source and time period"],["Understand the denominator","Do not mix spending with receipts"],["Open the original filing","Check coverage and reporting limits"]],jump:"#sources",jumpLabel:"Inspect primary sources",chart:"fec"},
"investigations.html":{title:"Three questions before drawing a conclusion",steps:[["Who paid whom?","Identify actual transactions"],["Who decided what?","Match official actions and dates"],["What was established?","Distinguish allegations and findings"]],jump:"navatek.html",jumpLabel:"Explore a documented case"},
"navatek.html":{title:"Separate the donation from the decision",steps:[["Document contributions","Follow FEC records"],["Document contracts","Verify recipient and award records"],["Test the allegation","Only state what investigators proved"]],jump:"investigations.html",jumpLabel:"Explore more cases"},
"compare.html":{title:"Two sides. One measuring stick.",steps:[["Choose a question","Voting, campaign money or representation"],["Hold the standard constant","Match periods, definitions and samples"],["Inspect both records","Evidence first, no partisan shortcuts"]],jump:"#votes",jumpLabel:"Compare recorded votes"},
"reform-lab.html":{title:"Follow the problem into a possible reform",steps:[["Identify a measured weakness","Money, access, enforcement or accountability"],["Compare policy options","Show tradeoffs and implementation"],["Check what actually happened","A proposal is not an enacted reform"]],jump:"#reforms",jumpLabel:"Explore the reform ideas"},
"source-audit.html":{title:"What is documented—and what still needs data?",steps:[["Find the claim","Identify the question being asked"],["Inspect coverage","Indexed is not the same as verified"],["Track the missing link","Show the original source needed next"]],jump:"#gapList",jumpLabel:"Review data gaps"},
"service-accountability.html":{title:"Does automation lower costs—or shift work to customers?",steps:[["Observe the service","Document the support journey"],["Measure the friction","Wait time, escalation and resolution"],["Compare alternatives","Distinguish measured harm from anecdote"]],jump:"consumer-practices.html",jumpLabel:"Explore Consumer Watch"},
"telecom-promotions.html":{title:"What is an advertised upgrade really worth?",steps:[["Read the deal","Separate device offer and plan price"],["Find the conditions","Credits, Picks and contract term"],["Compare all-in costs","Include service and early-exit costs"]],jump:"consumer-practices.html#true-cost",jumpLabel:"Compare ownership costs"},
"class-actions.html":{title:"A lawsuit is not a refund check",steps:[["Read the allegation","Check the court case and parties"],["Check procedural status","Proposed, approved and claims open are distinct"],["Verify the deadline","Use the settlement's official administrator"]],jump:"#cases",jumpLabel:"Inspect available case records",chart:"class"},
"election-2026.html":{title:"From the vote to who draws the next map",steps:[["Check certified returns","Election-night reporting is not final"],["Identify the decision-makers","Legislatures, governors, commissions and courts"],["Follow legal map changes","Only verified boundaries show the result"]],jump:"index.html",jumpLabel:"Review the research"},
"economic-fragility.html":{title:"From a warning indicator to a testable scenario",steps:[["Measure conditions","Use dated macroeconomic indicators"],["Trace the transmission","Debt, credit, earnings and liquidity"],["Separate risk from forecast","No unsupported crash probabilities"]],jump:"#money",jumpLabel:"Inspect financial pathways"},
"economic-fragility-review.html":{title:"A risk scenario is not a prediction",steps:[["Measure the indicators","Find the dated financial evidence"],["Show how stress could travel","Households, lenders and markets"],["Disclose uncertainty","Scenarios do not prove a future crash"]],jump:"#paths",jumpLabel:"Review the scenarios"}
};
const current=config[path];if(!current||path==="consumer-practices.html")return;
document.documentElement.classList.add("pa3");
const make=(tag,cls)=>{const el=document.createElement(tag);if(cls)el.className=cls;return el};
function story(){
 const target=document.querySelector("main")||document.body;if(!target)return;
 const section=make("section","pa3-story");section.setAttribute("aria-label","Visual research guide");
 const head=make("div","pa3-story-head");
 const left=make("div");const kicker=make("span","pa3-story-kicker");kicker.textContent="VISUAL GUIDE / THREE STEPS";
 const h=make("h2");h.textContent=current.title;left.append(kicker,h);head.append(left);
 if(current.intro){const desc=make("p","pa3-story-intro");desc.textContent=current.intro;head.append(desc)}
 const list=make("ol","pa3-steps");
 current.steps.forEach((v,i)=>{const li=make("li","pa3-step"),num=make("span","pa3-step-num"),copy=make("div","pa3-step-copy"),b=make("strong"),p=make("p");num.textContent=String(i+1).padStart(2,"0");b.textContent=v[0];p.textContent=v[1];copy.append(b,p);li.append(num,copy);list.append(li)});
 const foot=make("div","pa3-story-foot"),note=make("span");note.textContent="Original records and caveats remain available below.";
 const a=make("a");a.href=researchSurface&&String(current.jump).startsWith("my-life.html")?"https://power-atlas-unified.vercel.app/"+current.jump:(current.jump||"#");a.textContent=(current.jumpLabel||"Open the evidence")+" →";foot.append(note,a);section.append(head,list,foot);
 const hero=target.querySelector(":scope > .hero, :scope > section.hero, :scope > header.hero");
 if(hero)hero.insertAdjacentElement("afterend",section);
 else if(path==="index.html"){
   const first=target.querySelector("#overview .storyHero");
   if(first)first.insertAdjacentElement("afterend",section);else target.prepend(section);
 }else target.prepend(section);
}
const number=(n,kind)=>kind==="money"?"$"+Math.round(n).toLocaleString("en-US"):Number(n).toLocaleString("en-US",{maximumFractionDigits:1});
function chartShell(title,sub){
 const root=make("section","pa3-chart"),head=make("div","pa3-chart-head"),wrap=make("div"),k=make("span","pa3-chart-kicker"),h=make("h2"),desc=make("p");
 k.textContent="SOURCE-BACKED CHART";h.textContent=title;desc.textContent=sub;wrap.append(k,h,desc);head.append(wrap);root.append(head);
 const content=make("div","pa3-chart-loading");content.textContent="Loading reviewed values from the evidence registry…";root.append(content);
 const note=make("p","pa3-chart-notes");root.append(note);
 const links=make("div","pa3-chart-links");root.append(links);
 const mount=document.querySelector(".pa3-story");
 if(mount)mount.insertAdjacentElement("afterend",root);
 return {root,content,note,links};
}
function bars(host,rows,formatter){
 const max=Math.max(1,...rows.map(r=>r.value));const wrap=make("div","pa3-chart-bars");wrap.setAttribute("role","group");wrap.setAttribute("aria-label","Select a chart bar to explain its recorded value");
 const panel=make("p","pa4-chart-takeaway");panel.setAttribute("role","status");panel.setAttribute("aria-live","polite");
 rows.forEach((row,i)=>{
 const outer=make("button","pa3-chart-row"),label=make("span","pa3-chart-row-label"),track=make("span","pa3-chart-track"),bar=make("span","pa3-chart-bar"),value=make("strong","pa3-chart-value");
 outer.type="button";outer.setAttribute("aria-pressed",i===0?"true":"false");outer.setAttribute("aria-label",row.label+": "+formatter(row.value)+". Select for explanation.");
 label.textContent=row.label;bar.style.width=(row.value/max*100)+"%";track.append(bar);value.textContent=formatter(row.value);outer.append(label,track,value);wrap.append(outer);
 outer.addEventListener("click",()=>{wrap.querySelectorAll(".pa3-chart-row").forEach(b=>b.setAttribute("aria-pressed",String(b===outer)));panel.textContent=row.label+": "+formatter(row.value)+". Values are descriptive and reflect this chart's dated source definitions. The size of a bar does not prove a causal relationship."});
 });host.replaceWith(wrap);wrap.insertAdjacentElement("afterend",panel);if(rows[0])panel.textContent=rows[0].label+": "+formatter(rows[0].value)+". Select another bar to compare source-reported values; this chart does not establish causation.";return wrap;
}
function details(root,rows,formatter){
 const d=make("details"),sum=make("summary");sum.textContent="See exact data and source context";d.append(sum);
 const table=make("table"),head=make("tr"),th1=make("th"),th2=make("th");th1.textContent="Category / year";th2.textContent="Value";head.append(th1,th2);table.append(head);
 rows.forEach(r=>{const tr=make("tr"),a=make("td"),b=make("td");a.textContent=r.label;b.textContent=formatter(r.value);tr.append(a,b);table.append(tr)});
 d.append(table);root.append(d);
}
function source(links,href,label){if(!/^https:\/\//i.test(href))return;const a=make("a");a.href=href;a.target="_blank";a.rel="noopener noreferrer";a.textContent=label+" ↗";links.append(a)}
const base="https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/main/data/";
async function chart(){
 if(!current.chart)return;
 const options={
 bls:["What households spend on major needs","2025 U.S. average annual spending per consumer unit. These are national averages, not your local bills."],
 fec:["How congressional campaign receipts have changed","FEC-reported congressional committee receipts, completed 24-month cycles only. Values are nominal USD millions."],
 donors:["How giving by the top 40 donors changed","Brennan Center curated top-40 donor totals at the same Oct. 14 election-year cutoff. Nominal USD; not all political donations."],
 class:["Where these class-action cases stand","Counts by procedural status for this selected case register. These are not all consumer lawsuits."]
 };
 const {root,content,note,links}=chartShell(...options[current.chart]);
 try{
 let rows,unit,src,summary,format;
 if(current.chart==="bls"){
  const res=await fetch(base+"place-impact/cost-benchmark-drivers-v1.json",{cache:"no-store"});if(!res.ok)throw Error();const d=await res.json();
  if(d.schema!=="power-atlas.cost-benchmark-drivers.v1")throw Error();
  const keys=[["housing","Housing"],["transport","Transport"],["groceries","Groceries"],["health","Health"],["schools","Education"]];
  rows=keys.map(([k,label])=>({label,value:d.topics[k]?.headline?.annual})).filter(r=>Number.isFinite(r.value));
  if(rows.length!==5)throw Error();rows.sort((a,b)=>b.value-a.value);format=n=>number(n,"money");
  summary="National survey averages per consumer unit—not prices for equivalent individual products or median household spending. Categories use distinct BLS definitions; don't add them indiscriminately.";
  src=d.primarySource;
 }else if(current.chart==="fec"){
  const res=await fetch(base+"money-influence/fec-federal-cycle-overview-2002-2026.json",{cache:"no-store"});if(!res.ok)throw Error();const d=await res.json();
  if(!Array.isArray(d.cycles))throw Error();
  rows=d.cycles.filter(x=>x.coverage==="complete_24mo"&&Number.isFinite(x.congressionalReceipts24M)).slice(-7).map(x=>({label:String(x.cycle),value:x.congressionalReceipts24M}));
  if(rows.length<4)throw Error();
  format=n=>"$"+Math.round(n).toLocaleString("en-US")+"M";
  summary="This chart compares congressional committee receipts, not all campaign financing, and excludes incomplete cycles. Amounts are nominal, not adjusted for inflation.";
  src=d.cycles.filter(x=>x.coverage==="complete_24mo"&&x.congressionalSource24).slice(-1)[0]?.congressionalSource24||"https://www.fec.gov/data/";
 }else if(current.chart==="donors"){
  const res=await fetch(base+"money-influence/brennan-top40-midterms-2014-2026.json",{cache:"no-store"});if(!res.ok)throw Error();const d=await res.json();
  if(!Array.isArray(d.records))throw Error();
  const tally={};for(const x of d.records){if(!Number.isFinite(x.amountUsd))continue;tally[x.cycle]=(tally[x.cycle]||0)+x.amountUsd;}
  rows=Object.entries(tally).sort(([a],[b])=>Number(a)-Number(b)).map(([label,value])=>({label,value:value/1e9}));
  if(rows.length<3)throw Error();
  format=n=>"$"+n.toFixed(2)+"B";
  summary="Same October 14 cutoff each cycle; 2026 is a preliminary snapshot, not final totals. This is a curated top-40 list, not a complete FEC ledger. Amounts are not inflation-adjusted.";
  src=d.sourceArticle||"https://www.brennancenter.org/";
 }else{
  const res=await fetch(base+"consumer-class-actions/cases-v1.json",{cache:"no-store"});if(!res.ok)throw Error();const d=await res.json();if(!Array.isArray(d.cases))throw Error();
  const agg={};d.cases.forEach(c=>{const k=c.proceduralStatus==="settlement-final"?"Final settlement":c.proceduralStatus==="settlement-proposed"?"Proposed settlement":c.proceduralStatus;agg[k]=(agg[k]||0)+1});
  rows=Object.entries(agg).map(([label,value])=>({label,value})).sort((a,b)=>b.value-a.value);
  format=n=>String(n)+" case"+(n===1?"":"s");
  summary="These are selected cases, not a nationwide count. A proposed settlement, final settlement and open claims window mean different things.";
  src="https://github.com/jbmeadows26/Power-Atlas/blob/main/data/consumer-class-actions/cases-v1.json";
 }
 if(!rows?.length)throw Error();
 bars(content,rows,format);details(root,rows,format);note.textContent=summary;
 source(links,src,"Original source");source(links,"https://github.com/jbmeadows26/Power-Atlas/blob/main/data/"+(current.chart==="bls"?"place-impact/cost-benchmark-drivers-v1.json":current.chart==="fec"?"money-influence/fec-federal-cycle-overview-2002-2026.json":current.chart==="donors"?"money-influence/brennan-top40-midterms-2014-2026.json":"consumer-class-actions/cases-v1.json"),"Review dataset");
 }catch(e){content.textContent="Reviewed data unavailable. No chart is shown without verified source values.";note.textContent="Inspect the underlying data and source registry before drawing conclusions."}
}
function start(){if(path!=="corporate-ownership.html")story();chart()}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",start,{once:true});else start();
})();


/* Power Atlas v4 production — an original, source-led visual atlas.
   Enhances existing evidence connectors in place; never substitutes invented local estimates. */
(()=>{"use strict";
const path=(location.pathname.split("/").pop()||"index.html").split("?")[0];
const researchSurface=location.hostname.includes("research")||document.body.classList.contains("pa-research-site");
const unifiedProductionBase="https://power-atlas-unified.vercel.app/";
const researchProductionBase="https://power-atlas-research.vercel.app/";
const localResearchFiles=new Set(["index.html","consumer-practices.html","telecom-promotions.html","service-accountability.html","economic-fragility.html","economic-fragility-review.html","election-2026.html","market-power.html","money-scale.html"]);
const link=name=>researchSurface&&!localResearchFiles.has(name)?unifiedProductionBase+name:(!researchSurface&&name==="economic-fragility.html"?researchProductionBase+name:name);
const chapters={
"index.html":["Visual atlas",["my-life.html","Your community"],["market-power.html","Concentration and household costs"],["money-scale.html","Billions and trillions"],["dark-money.html","Election money"]],
"my-life.html":["Everyday life",["corporate-ownership.html","Ownership and prices"],["market-power.html","Concentration and household costs"],["money-scale.html","Billions and trillions"],["consumer-practices.html","Consumer Watch"],["source-audit.html","Coverage and limitations"],["economic-fragility.html","Economic stability"]],
"corporate-ownership.html":["Corporate power",["my-life.html","See everyday costs"],["market-power.html","Market concentration"],["business-influence.html","Business and government"],["economic-fragility.html","Market stress"]],
"consumer-practices.html":["Consumer Watch",["market-power.html","Market power"],["telecom-promotions.html","Phone promotions"],["class-actions.html","Class-action cases"],["service-accountability.html","Customer-service access"]],
"telecom-promotions.html":["Consumer Watch",["consumer-practices.html","Consumer Watch"],["my-life.html","Personal cost context"],["class-actions.html","Consumer lawsuits"]],
"service-accountability.html":["Consumer Watch",["consumer-practices.html","Hidden costs and practices"],["class-actions.html","Consumer lawsuits"],["my-life.html","Daily-life impacts"]],
"class-actions.html":["Consumer Watch",["consumer-practices.html","Consumer Watch"],["source-audit.html","Evidence methodology"],["service-accountability.html","Customer service"]],
"dark-money.html":["Political finance",["money-sources.html","Primary filing sources"],["donor-intelligence.html","Major donors"],["election-money.html","Election spending"]],
"donor-intelligence.html":["Political finance",["dark-money.html","Trace the money"],["election-money.html","Campaign cycles"],["money-sources.html","Source records"]],
"election-money.html":["Political finance",["donor-intelligence.html","Major donors"],["dark-money.html","Dark-money research"],["money-sources.html","Original filings"]],
"money-sources.html":["Political finance",["dark-money.html","Follow transfers"],["business-influence.html","Business influence"],["source-audit.html","Data coverage"]],
"business-influence.html":["Power and money",["business-candidates.html","Investigated businesses"],["corporate-ownership.html","Corporate ownership"],["investigations.html","Case investigations"]],
"business-candidates.html":["Power and money",["business-influence.html","Business outcomes"],["corporate-ownership.html","Corporate ownership"],["source-audit.html","Source status"]],
"investigations.html":["Accountability",["navatek.html","Case study"],["business-influence.html","Follow the records"],["source-audit.html","Verification and gaps"]],
"navatek.html":["Accountability",["investigations.html","Other investigations"],["money-sources.html","Source filings"],["business-influence.html","Business and policy"]],
"compare.html":["Democracy",["election-2026.html","Election context"],["dark-money.html","Political financing"],["reform-lab.html","Reform choices"]],
"election-2026.html":["Democracy",["compare.html","Compare evidence"],["dark-money.html","Campaign finance"],["source-audit.html","Evidence status"]],
"reform-lab.html":["Civic power",["compare.html","Compare outcomes"],["my-life.html","Everyday impacts"],["source-audit.html","Known limitations"]],
"source-audit.html":["Evidence and methods",["my-life.html","Everyday measurements"],["money-sources.html","Money sources"],["reform-lab.html","Possible responses"]],
"economic-fragility.html":["Economic resilience",["my-life.html","Household exposure"],["money-scale.html","Wealth and debt in context"],["market-power.html","Market power"],["source-audit.html","Source quality"]],
"market-power.html":["Market concentration",["my-life.html","Household cost context"],["money-scale.html","Financial scale"],["corporate-ownership.html","Ownership evidence"],["source-audit.html","Evidence gaps"]],
"money-scale.html":["Financial scale",["market-power.html","Market power and costs"],["my-life.html","Everyday benchmarks"],["economic-fragility.html","Economic resilience"],["source-audit.html","Evidence limitations"]],
"economic-fragility-review.html":["Economic resilience",["my-life.html","Household exposure"],["source-audit.html","Source quality"],["economic-fragility.html","Economic risk overview"]]
};
const measures=[
{key:"transport",label:"Transportation",value:7.77,color:"#e99a7a",src:"https://fred.stlouisfed.org/data/CPITRNSL",explain:"Transportation CPI: +7.77% year over year in September 2026. This includes different transport prices; it does not isolate a toll or fare change."},
{key:"housing",label:"Rent",value:2.78,color:"#7ed2b9",src:"https://fred.stlouisfed.org/data/CUSR0000SEHA",explain:"Rent of primary residence CPI: +2.78%. Not a measure of a specific bedroom size or current asking rent."},
{key:"groceries",label:"Groceries",value:1.77,color:"#b59de7",src:"https://fred.stlouisfed.org/data/CUSR0000SAF11",explain:"Food-at-home CPI: +1.77%. Not a local grocery-basket or retailer-specific figure."},
{key:"health",label:"Medical care",value:1.50,color:"#f3cc76",src:"https://fred.stlouisfed.org/data/CPIMEDSL",explain:"Medical-care CPI: +1.50%. Not a health-insurance premium or personal medical bill."}
];
const tiles=[
["01 · Everyday life","What pushes costs up?","Housing, food, utilities and transportation.","my-life.html","#f3b9a4"],
["02 · Corporate power","Who owns what?","See investors, companies and the limits of ownership data.","corporate-ownership.html","#dac6f3"],
["03 · Consumer Watch","What's in the fine print?","Phone deals, subscriptions and hidden conditions.","consumer-practices.html","#bce9df"],
["04 · Political money","Where does the money go?","Follow reported contributions through public filings.","dark-money.html","#cbdff7"],
["05 · Accountability","What's actually proven?","Separate measured records, claims and open questions.","source-audit.html","#f0dcaa"],
["06 · Civic action","What can change?","Explore options and their documented trade-offs.","reform-lab.html","#dfeac8"],
["07 · Economic resilience","Could a market sell-off affect you?","Compare market declines with historical crashes and potential household spillovers.","economic-fragility.html","#bddce8"],
["08 · Market power","Who gains when competition shrinks?","Follow evidence on food, housing, healthcare and wages to everyday cost categories.","market-power.html","#c1e7d3"],
["09 · Financial scale","How big is a trillion dollars?","Separate wealth, debt, GDP and public spending with sourced, dated comparisons.","money-scale.html","#decdf3"],
["10 · Class actions","When companies get sued","Read case status, deadlines and official settlement notices.","class-actions.html","#f4d6ac"]
];
function el(tag,cls,txt){const x=document.createElement(tag);if(cls)x.className=cls;if(txt!==undefined)x.textContent=txt;return x}
function intro(){
const root=el("section","pa4-home");root.id="pa4-atlas-home";root.setAttribute("aria-label","Explore Power Atlas stories");
const hero=el("div","pa4-home-main"),copy=el("div"),k=el("span","pa4-kicker","THE STORY BEHIND THE SYSTEM");
const h=el("h1");h.append("See the big picture. ",(()=>{const em=el("em",null,"Then follow the details.");return em})());copy.append(k,h);
copy.append(el("p","pa4-lead","From everyday bills to decisions made by companies and governments, explore measurable changes, documented relationships and the unanswered questions. Easy to scan. Deep enough to investigate."));
const a=el("a","pa4-primary","Explore what affects your life ↗");a.href=link("my-life.html");copy.append(a,el("p","pa4-mini","No ZIP is required for this overview. Local detail remains available through the community explorer."));
const chart=el("div","pa4-graphic");chart.append(el("span","pa4-kicker","UNITED STATES · SEPTEMBER 2026"),el("h2",null,"How quickly are selected everyday price indexes rising?"));
const bars=el("div","pa4-bars");bars.setAttribute("role","group");bars.setAttribute("aria-label","Select a national CPI category");
const detail=el("div","pa4-chart-detail");detail.setAttribute("aria-live","polite");
function selected(m){detail.textContent="";const b=el("strong",null,m.explain);const s=el("span",null," · National, seasonally adjusted CPI; year-over-year change. Not household bill dollars. ");const source=el("a",null,"Original data ↗");source.href=m.src;source.target="_blank";source.rel="noopener noreferrer";detail.append(b,s,source)}
measures.forEach((m,i)=>{const btn=el("button","pa4-bar");btn.type="button";btn.setAttribute("aria-pressed",String(i===0));btn.style.setProperty("--val",String(m.value));btn.style.setProperty("--shade",m.color);
btn.append(el("span",null,m.label));const track=el("span","pa4-bar-track"),fill=el("span","pa4-bar-fill");track.append(fill);btn.append(track,el("b",null,"+"+m.value.toFixed(2)+"%"));
btn.addEventListener("click",()=>{bars.querySelectorAll("button").forEach(x=>x.setAttribute("aria-pressed",String(x===btn)));selected(m)});bars.append(btn)});
chart.append(bars,detail);selected(measures[0]);hero.append(copy,chart);root.append(hero);
const headline=el("div","pa4-atlas-head");const hl=el("div");hl.append(el("span","pa4-kicker","VISUAL ATLAS"),el("h2",null,"Start with a question, not a spreadsheet."));headline.append(hl,el("p",null,"Ten paths into the evidence. Every chapter connects to a real Power Atlas section."));root.append(headline);
const gallery=el("div","pa4-gallery");
tiles.forEach(t=>{const card=el("a",t[3]==="class-actions.html"?"pa4-tile pa4-tile--claims":"pa4-tile");card.href=link(t[3]);const pic=el("span","pa4-tile-visual");pic.style.setProperty("--tile",t[4]);pic.setAttribute("aria-hidden","true");card.append(pic,el("span","pa4-tile-kicker",t[0]),el("strong",null,t[1]),el("small",null,t[2]),el("span","pa4-go","Explore story ↗"));gallery.append(card)});root.append(gallery);
const target=document.querySelector("main");
if(target){target.prepend(root);document.body.classList.add("pa4-unified-home");
 const promos=Array.from(target.children).filter(x=>x!==root&&(x.tagName==="ASIDE"||x.tagName==="DIV")&&x.getAttribute("style")?.includes("max-width:1240"));
 if(promos.length>0){const box=el("details","pa4-latest"),summary=el("summary",null,"Recently added investigations and research");box.append(summary);promos.forEach(x=>box.append(x));root.insertAdjacentElement("afterend",box)}
}else{const old=document.querySelector("header.hero");if(old){old.insertAdjacentElement("beforebegin",root);document.body.classList.add("pa4-research-home")}else document.body.prepend(root)}
}
function context(){
const cfg=chapters[path];if(!cfg)return;
const story=document.querySelector(".pa3-story");if(story){const head=story.querySelector(".pa3-story-head > div");if(head)head.prepend(el("span","pa4-topic-flag",cfg[0]))}
if(path==="index.html")return;
const row=el("nav","pa4-crossroads");row.setAttribute("aria-label","Related visual stories");row.append(el("span",null,"Continue exploring"));
cfg.slice(1).forEach(p=>{const a=el("a",null,p[1]+" ↗");a.href=link(p[0]);row.append(a)});
const chart=document.querySelector(".pa3-chart");const anchor=chart||story||document.querySelector("main > .hero")||document.querySelector("main > section")||document.querySelector("main > div")||document.querySelector("main");
if(anchor){if(anchor.matches("main"))anchor.prepend(row);else anchor.insertAdjacentElement("afterend",row)}else document.body.append(row);
}
function main(){
document.documentElement.classList.add("pa4");if(!chapters[path])return;
if(path==="index.html")intro();context();
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",main,{once:true});else main();
})();

/* Shared location-first navigation — applied consistently across Power Atlas pages.
   Consumer Watch remains discoverable in the Costs journey, without misrouting its tab. */
(()=>{
  "use strict";
  const nav=document.querySelector("#pa-global-header .pa-global-links");
  if(!nav)return;
  const definitions=[
    ["place","my-life.html#where","Start Here"],
    ["issues","my-life.html#what","Issues"],
    ["costs","my-life.html#benchmarkStory","Costs"],
    ["why","my-life.html#why","The Why"],
    ["action","my-life.html#how","Actions"],
    ["research","index.html","Research"]
  ];
  const existing=new Map();
  for(const link of nav.querySelectorAll("a[data-pa-nav]")){
    const key=link.dataset.paNav==="consumer"?"costs":link.dataset.paNav;
    existing.set(key,link);
  }
  if(definitions.some(([key])=>!existing.has(key)))return;
  for(const [key,href,label] of definitions){
    const link=existing.get(key);
    link.dataset.paNav=key;
    link.setAttribute("href",href);
    const long=link.querySelector(".pa-long"),short=link.querySelector(".pa-short");
    if(long)long.textContent=label;
    if(short)short.textContent=label;
    if(key==="costs"&&link.getAttribute("aria-current")==="page")link.setAttribute("aria-current","location");
    nav.append(link);
  }
  if(location.pathname.endsWith("/my-life.html")&&!location.hash){
    for(const link of nav.querySelectorAll("a[data-pa-nav]")){
      if(link.dataset.paNav==="place")link.setAttribute("aria-current","location");
      else link.removeAttribute("aria-current");
    }
  }
})();


/* V5 visual-first presentation: progressive enhancement, not a data-feed change. */
(()=>{"use strict";
 if(document.querySelector('script[data-pa5-loader]'))return;
 const style=document.createElement("link");
 style.rel="stylesheet";style.href="visual-first-v5.css";style.setAttribute("data-pa5-loader","css");
 document.head.appendChild(style);
 const script=document.createElement("script");
 script.src="visual-first-v5.js";script.setAttribute("data-pa5-loader","js");
 document.head.appendChild(script);
})();


/* One optional QA monitor across all pages using the shared visual system. */
(()=>{"use strict";if(document.querySelector('script[data-pa-monitor]'))return;
  if(!location.hostname.startsWith("power-atlas-unified") && !["localhost","127.0.0.1"].includes(location.hostname))return;
  const script=document.createElement("script");script.src="qa-monitor.js";
  script.defer=true;script.dataset.paMonitor="1";
  document.head.append(script);
})();


/* Single-origin, device-local ZIP preference. Shared by every public page. */
(()=>{"use strict";
 if(window.PowerAtlasZIP||document.querySelector('script[src^="pa-zip-persistence.js"]'))return;
 const script=document.createElement("script");script.src="pa-zip-persistence.js";
 script.defer=true;script.dataset.paZipLoader="1";document.head.appendChild(script);
})();
