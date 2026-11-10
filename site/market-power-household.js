/* Evidence and BLS spending linkage, review only. All values come from versioned JSON. */
(async function(){
"use strict";
const root=document.getElementById("household-bridge");
if(!root)return;
const barList=document.getElementById("hbBars"),detail=document.getElementById("hbDetail"),income=document.getElementById("hbIncome"),status=document.getElementById("hbStatus");
const el=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=String(text);return n};
const fmt=n=>new Intl.NumberFormat("en-US",{style:"currency",currency:"USD",maximumFractionDigits:0}).format(n);
let bridge=null,cases=new Map(),selected=null;
function addPara(where,label,value){const p=el("p");const b=el("strong",null,label+" ");p.append(b,document.createTextNode(value));where.append(p)}
function renderDetail(c){
selected=c.id;
for(const button of barList.querySelectorAll("button[data-category]"))button.setAttribute("aria-pressed",String(button.dataset.category===c.id));
detail.replaceChildren();
detail.append(el("span","hb-eyebrow","Cost benchmark / U.S. national"),el("h3",null,c.label+" · "+fmt(c.annualUsd)+"/year"));
addPara(detail,"What that number includes.",c.coverage);
addPara(detail,"Where market power can matter.",c.mechanism);
addPara(detail,"Who may benefit.",c.whatBenefits);
addPara(detail,"Who may bear the costs.",c.whoPays);
addPara(detail,"What remains unknown.",c.unresolved);
detail.append(el("h4",null,"Investigations behind this category"));
for(const id of c.caseIds){const item=cases.get(id);if(!item)continue;const card=el("div","hb-case");card.append(el("strong",null,item.name),el("small",null,item.status+" · "+item.period),el("small",null,item.metricLabel));
const link=el("a",null,"Open this evidence case →");link.href="market-power.html?case="+encodeURIComponent(id)+"#explore";card.append(link);
const source=el("a",null,"Original source ↗");source.href=item.source;source.target="_blank";source.rel="noopener noreferrer";source.style.marginLeft="14px";card.append(source);detail.append(card)}
const links=el("div","hb-linkrow");const life=el("a",null,"Explore national and local cost context →");life.href=c.linkedPage==="my-life.html"?"https://power-atlas-unified.vercel.app/my-life.html":c.linkedPage;links.append(life);detail.append(links);
}
function render(){barList.replaceChildren();const max=Math.max(...bridge.categories.map(c=>c.annualUsd));
for(const c of bridge.categories){const button=el("button","hb-bar");button.type="button";button.dataset.category=c.id;button.setAttribute("aria-pressed","false");button.setAttribute("aria-label",c.label+", average "+fmt(c.annualUsd)+" annually. Open market-power evidence and limitations.");
button.append(el("span","hb-bar-label",c.label),el("span","hb-bar-value",fmt(c.annualUsd)));
const track=el("span","hb-track"),fill=el("span","hb-fill");fill.style.width=(c.annualUsd/max*100)+"%";track.append(fill);button.append(track);button.addEventListener("click",()=>renderDetail(c));barList.append(button)}
status.textContent="Source: BLS Consumer Expenditure Survey 2025, published October 29, 2026. Spending levels, not estimates of monopoly overcharges.";
income.replaceChildren();income.append(el("strong",null,fmt(bridge.incomeExample.annualUsd)),el("span",null,"National average pre-tax consumer-unit income in 2025. Income is not spending, so it is excluded from the bar chart."));
const work=el("a",null,"Investigate employer concentration and wage bargaining →");work.href="market-power.html?case=jobs#explore";income.append(work);
renderDetail(bridge.categories[0]);}
try{
const r=await Promise.all([fetch("household-market-bridge.json",{cache:"no-store"}),fetch("market-power.json",{cache:"no-store"})]);
if(r.some(x=>!x.ok))throw new Error("Linked source data unavailable");
const ds=await Promise.all(r.map(x=>x.json()));bridge=ds[0];const market=ds[1];
if(bridge.schema!=="power-atlas.market-power.household-bridge.v1"||market.schema!=="power-atlas.market-power.v1")throw new Error("Unexpected evidence schema");
if(!Array.isArray(bridge.categories)||!Array.isArray(market.cases))throw new Error("Incomplete evidence");
cases=new Map(market.cases.map(x=>[x.id,x]));
if(bridge.categories.some(x=>x.caseIds.some(id=>!cases.has(id))))throw new Error("Case reference missing");
render();
}catch(e){status.textContent="Source data unavailable; no chart values or household impacts have been invented.";detail.replaceChildren(el("p","hb-selected","The linked evidence register could not be loaded. Try the original published sources in the main evidence explorer."));}
})();