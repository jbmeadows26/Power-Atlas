/* Power Atlas: shared V6 evidence discovery.
   Links to existing investigations; does not invent unpublished facts. */
(()=>{"use strict";
const path=(location.pathname.split("/").pop()||"index.html").toLowerCase();
if(path!=="my-life.html")return;
const threads=[
 {icon:"🏛",name:"Political influence",caption:"Donors, contracts and documented decisions",href:"business-influence.html"},
 {icon:"💸",name:"Dark money",caption:"Trace disclosures and unknown funders",href:"dark-money.html"},
 {icon:"🏢",name:"Who owns what?",caption:"Parents, investors and operating brands",href:"corporate-ownership.html"},
 {icon:"↘",name:"Market power",caption:"Who benefits when choices shrink?",href:"market-power.html"},
 {icon:"🧾",name:"Consumer Watch",caption:"Hidden fees, unfair offers and true costs",href:"consumer-practices.html"},
 {icon:"⚖",name:"Class actions",caption:"Court status, official claims and deadlines",href:"class-actions.html"},
 {icon:"📦",name:"Shrinkflation",caption:"Less product for the same or higher price",href:"consumer-practices.html#shrinkflation"},
 {icon:"☎",name:"Human service",caption:"Automation, staffing and customer access",href:"service-accountability.html"},
 {icon:"✈",name:"Wealth advantage",caption:"Household, business and luxury tax rules",href:"wealth-advantage.html"},
 {icon:"🌡",name:"Economic fragility",caption:"Risks and resilience, not crash predictions",href:"economic-fragility-review.html"},
 {icon:"⇄",name:"City cost gaps",caption:"Comparable benchmarks, not a calculator",href:"cost-gap.html"},
 {icon:"📑",name:"Official trades",caption:"Disclosures, holdings and policy dates",href:"public-trading.html"},
 {icon:"🏦",name:"Financial flows",caption:"Trace who paid and who received",href:"financial-flows.html"},
 {icon:"🗳",name:"Representation",caption:"Voting, public decisions and political rules",href:"compare.html"},
 {icon:"📣",name:"Take action",caption:"Reach representatives with verified facts",href:"take-action.html"},
 {icon:"🗳",name:"Voting access",caption:"Voter ID, early/mail ballots and state-law evidence",href:"voting-access.html"},
 {icon:"📉",name:"Economic fragility detail",caption:"Market scenarios and source-linked risk evidence",href:"economic-fragility.html"},
 {icon:"📚",name:"Deep research archive",caption:"Political promises, authenticity and institutional trust",href:"research-archive.html"},
 {icon:"🔎",name:"Evidence gaps",caption:"Which claims still need original records?",href:"source-audit.html"}
];
function e(tag,cls,txt){const n=document.createElement(tag);if(cls)n.className=cls;if(txt!==undefined)n.textContent=txt;return n;}
function card(item){const a=e("a","pa-coverage-card");a.href=item.href;
 a.append(e("span","pa-coverage-symbol",item.icon),e("b",null,item.name),
 e("small",null,item.caption),e("span",null,"Explore the evidence ↗"));return a;}
function render(){
 if(document.getElementById("pa-coverage-discovery"))return;
 const why=document.getElementById("why");if(!why)return;
 const section=e("section","pa-coverage");
 section.id="pa-coverage-discovery";
 section.setAttribute("aria-labelledby","pa-coverage-title");
 const head=e("div","pa-coverage-head"),left=e("div");
 left.append(e("span","vs6-micro","KEEP EXPLORING · ORIGINAL EVIDENCE"),
 e("h2",null,"Follow the whole story."),
 e("p",null,"The connections behind prices and public decisions. Open a topic for the charts, cases and source records."));
 const status=e("div","pa-coverage-status");
 status.setAttribute("role","status");status.setAttribute("aria-live","polite");
 status.textContent="Data gaps are tracked openly. Records are not proof of misconduct or local price causation.";
 head.append(left,status);section.append(head);
 const grid=e("div","pa-coverage-grid");threads.slice(0,8).forEach(x=>grid.append(card(x)));
 section.append(grid);
 const more=e("details","pa-coverage-more");
 const summary=e("summary",null,"Explore "+(threads.length-8)+" more investigations +");more.append(summary);
 const extra=e("div","pa-coverage-grid");extra.style.marginTop="13px";
 threads.slice(8).forEach(x=>extra.append(card(x)));more.append(extra);section.append(more);
 const foot=e("div","pa-coverage-foot");
 foot.append(e("span",null,"Measured data · documented relationships · allegations · unknowns are kept separate."));
 const a=e("a",null,"See source coverage and missing joins ↗");a.href="source-audit.html";foot.append(a);
 section.append(foot);
 why.insertAdjacentElement("afterend",section);
 const urls=["sitewide-audit-v1.json","https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/main/data/health/sitewide-audit-v1.json"];
 (async()=>{for(const url of urls){try{
   const r=await fetch(url,{cache:"no-store"});if(!r.ok)continue;const data=await r.json();
   if(data.schema!=="power-atlas.sitewide-static-source-audit.v1")continue;
   const open=Number(data.summary?.unresolvedOriginalSourceGaps);
   if(Number.isInteger(open)&&open>=0){
     status.replaceChildren(e("b",null,open+" original-source joins still open"),
       e("div",null,"A source directory is not a completed investigation."));
   }break;
 }catch(_){/* Keep honest fallback. */}}})();
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",render,{once:true});else render();
})();
