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
"source-audit.html":{title:"What is documented—and what still needs data?",steps:[["Find the claim","Identify the question being asked"],["Inspect coverage","Indexed is not the same as verified"],["Track the missing link","Show the original source needed next"]],jump:"#gaps",jumpLabel:"Review data gaps"},
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
 const target=document.querySelector("main");if(!target)return;
 const section=make("section","pa3-story");section.setAttribute("aria-label","Visual research guide");
 const head=make("div","pa3-story-head");
 const left=make("div");const kicker=make("span","pa3-story-kicker");kicker.textContent="VISUAL GUIDE / THREE STEPS";
 const h=make("h2");h.textContent=current.title;left.append(kicker,h);head.append(left);
 if(current.intro){const desc=make("p","pa3-story-intro");desc.textContent=current.intro;head.append(desc)}
 const list=make("ol","pa3-steps");
 current.steps.forEach((v,i)=>{const li=make("li","pa3-step"),num=make("span","pa3-step-num"),copy=make("div","pa3-step-copy"),b=make("strong"),p=make("p");num.textContent=String(i+1).padStart(2,"0");b.textContent=v[0];p.textContent=v[1];copy.append(b,p);li.append(num,copy);list.append(li)});
 const foot=make("div","pa3-story-foot"),note=make("span");note.textContent="Original records and caveats remain available below.";
 const a=make("a");a.href=current.jump||"#";a.textContent=(current.jumpLabel||"Open the evidence")+" →";foot.append(note,a);section.append(head,list,foot);
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
 const max=Math.max(1,...rows.map(r=>r.value));const wrap=make("div","pa3-chart-bars");wrap.setAttribute("role","img");wrap.setAttribute("aria-label",rows.map(x=>x.label+": "+formatter(x.value)).join("; "));
 rows.forEach(row=>{
 const outer=make("div","pa3-chart-row"),label=make("span","pa3-chart-row-label"),track=make("span","pa3-chart-track"),bar=make("span","pa3-chart-bar"),value=make("strong","pa3-chart-value");
 label.textContent=row.label;bar.style.width=(row.value/max*100)+"%";track.append(bar);value.textContent=formatter(row.value);outer.append(label,track,value);wrap.append(outer);
 });host.replaceWith(wrap);return wrap;
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
function start(){story();chart()}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",start,{once:true});else start();
})();
