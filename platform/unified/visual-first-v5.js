/* Power Atlas v5: visual first; detailed research on demand.
   Non-destructive enhancement: source data and calculation code remain untouched. */
(()=>{"use strict";
const path=(location.pathname.split("/").pop()||"index.html").toLowerCase();
const themes={
"my-life.html":["What shapes your daily costs?","Start with your community. Follow the measured costs and decisions.","place",["Your place","The costs","Who decides"]],
"corporate-ownership.html":["Who is behind the brands?","Trace ownership first. Test any alleged price impact separately.","owners",["Investor","Company","Cost impact?"]],
"market-power.html":["When choices shrink, who gains?","Compare market concentration with outcomes and consumer exposure.","owners",["Market","Competition","Your costs"]],
"money-scale.html":["How big is the money?","Compare wealth, debt, annual spending and output without mixing units.","money",["Amount","Measure","Meaning"]],
"consumer-practices.html":["What did the deal really cost?","See the offer, the conditions and the final cost.","phone",["The offer","The terms","Full cost"]],
"telecom-promotions.html":["Look past the phone promotion.","Compare the total bill, not the teaser credit.","phone",["Phone","Plan","Total"]],
"service-accountability.html":["Where did the humans go?","Look at documented workforce figures and reported service barriers.","phone",["Automation","Service","Evidence"]],
"class-actions.html":["A lawsuit is not a refund.","See verified case status and claim deadlines first.","proof",["Complaint","Court status","Claim window"]],
"dark-money.html":["Follow the money.","See reported transfers and where the public record stops.","money",["Source","Transfer","Disclosure gap"]],
"donor-intelligence.html":["Who is funding politics?","Follow disclosed contributors and limits of the record.","money",["Donor","Committee","Report"]],
"election-money.html":["Campaign money isn't a vote.","Follow spending without inventing the effect on results.","money",["Contributions","Spending","Result?"]],
"money-sources.html":["Where is the original filing?","Start with public records, then trace known connections.","money",["Source","Filing","Gap"]],
"business-influence.html":["Are businesses influencing decisions?","Separate recorded money relationships from proven outcomes.","owners",["Business","Funding","Decision?"]],
"business-candidates.html":["Which companies warrant scrutiny?","Compare source-backed cases, not accusations.","owners",["Company","Evidence","Status"]],
"investigations.html":["What can we prove?","Follow sources, dates and remaining unknowns.","proof",["Claim","Evidence","Uncertainty"]],
"navatek.html":["Follow this one case.","Read documented connections and the limits of the record.","proof",["Document","Finding","Limit"]],
"compare.html":["What changed in representation?","Compare elections and institutions using compatible measures.","money",["Rules","Voters","Outcome"]],
"election-2026.html":["What did the election reveal?","Read vote outcomes alongside uncertainty and context.","money",["Votes","Results","Context"]],
"reform-lab.html":["What could actually change?","Compare reform proposals and their trade-offs.","proof",["Problem","Proposal","Trade-off"]],
"source-audit.html":["Is this evidence reliable?","See what is measured, alleged, missing or uncertain.","proof",["Measured","Documented","Unknown"]],
"economic-fragility.html":["How could market stress reach you?","Follow possible economic spillovers, not crash predictions.","money",["Markets","Businesses","Households?"]],
"economic-fragility-review.html":["A warning isn't a prediction.","Compare leading indicators and their limits.","money",["Indicators","Scenarios","Limits"]],
"cost-gap.html":["Why does one place cost more?","Compare like-for-like measures, then investigate the drivers.","place",["Place A","Cost gap","Place B"]],
"financial-flows.html":["Who receives the money?","Trace documented financial flows without assuming intent.","money",["Payer","Transfer","Recipient"]],
"public-trading.html":["What do officials disclose?","See reported trades and interests alongside policy roles.","money",["Disclosure","Interest","Decisions?"]]
};
const colors=["#239f94","#9274d0","#e68b71","#4b93c5","#ddba63","#73b58d"];
function el(tag,cls,text){const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n;}
function brief(s,max){s=(s||"").replace(/\s+/g," ").trim();if(s.length<=max)return s;return s.slice(0,max).replace(/\s+\S*$/,"")+"…";}
function illustration(kind,color){
 const v=document.createElementNS("http://www.w3.org/2000/svg","svg");
 v.setAttribute("viewBox","0 0 180 100");v.setAttribute("aria-hidden","true");v.setAttribute("focusable","false");v.classList.add("pa5-illustration");v.style.color=color||colors[0];
 const paths={
 place:'<rect x="16" y="46" width="41" height="37" rx="7" fill="currentColor" opacity=".35"/><rect x="69" y="21" width="41" height="62" rx="7" fill="currentColor" opacity=".6"/><rect x="122" y="35" width="41" height="48" rx="7" fill="currentColor"/><path d="M16 90 H163" stroke="currentColor" stroke-width="4"/>',
 owners:'<path d="M43 52 L92 19 L139 52 L92 83 Z M43 52 H139" stroke="currentColor" stroke-width="5" fill="none" opacity=".45"/><circle cx="43" cy="52" r="18" fill="currentColor"/><circle cx="92" cy="19" r="15" fill="currentColor" opacity=".6"/><circle cx="139" cy="52" r="19" fill="currentColor" opacity=".85"/><circle cx="92" cy="83" r="14" fill="currentColor" opacity=".4"/>',
 phone:'<rect x="53" y="6" width="74" height="89" rx="12" fill="none" stroke="currentColor" stroke-width="6"/><path d="M65 26 H115 M65 43 H115 M65 59 H96" stroke="currentColor" stroke-width="5" stroke-linecap="round" opacity=".65"/><circle cx="100" cy="74" r="9" fill="currentColor"/>',
 money:'<path d="M19 50 H163 M145 33 L163 50 L145 67" stroke="currentColor" stroke-width="5" fill="none"/><rect x="17" y="31" width="35" height="44" rx="8" fill="currentColor" opacity=".42"/><rect x="75" y="20" width="33" height="61" rx="8" fill="currentColor"/><rect x="131" y="31" width="35" height="44" rx="8" fill="currentColor" opacity=".6"/>',
 proof:'<circle cx="88" cy="49" r="36" fill="none" stroke="currentColor" stroke-width="6"/><path d="M69 51 L82 63 L108 35" fill="none" stroke="currentColor" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/><circle cx="146" cy="24" r="11" fill="currentColor" opacity=".35"/>',
 trend:'<path d="M19 83 H161" stroke="currentColor" stroke-width="5" opacity=".35"/><path d="M19 66 L56 32 L89 59 L121 20 L161 44" fill="none" stroke="currentColor" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>'
 };
 v.innerHTML=paths[kind]||paths.proof;return v;
}
function home(){
 const root=document.getElementById("pa4-atlas-home");if(!root)return;
 const h=root.querySelector("h1");if(h){h.replaceChildren(document.createTextNode("Who shapes what you pay? "),el("em",null,"Follow the evidence."));}
 const l=root.querySelector(".pa4-lead");if(l)l.textContent="Prices. Power. People. See what connects them.";
 const heading=root.querySelector(".pa4-atlas-head h2");if(heading)heading.textContent="Pick a story. Get the picture.";
 const desc=root.querySelector(".pa4-atlas-head p");if(desc)desc.textContent="Tap to explore. Evidence is one click away.";
 const types=["place","owners","phone","money","proof","trend","trend","owners","money","proof"];
 const gallery=root.querySelector(".pa4-gallery");if(!gallery)return;
 const tiles=[...gallery.querySelectorAll(".pa4-tile")];
 tiles.forEach((a,i)=>{const art=a.querySelector(".pa4-tile-visual");if(art){art.replaceChildren(illustration(types[i]||"proof",colors[i%colors.length]));}const summary=a.querySelector("small");if(summary)summary.textContent=brief(summary.textContent,61);const go=a.querySelector(".pa4-go");if(go)go.textContent="Explore →";if(i>=4)a.classList.add("pa5-extra-story");});
 if(tiles.length>4){gallery.dataset.pa5Compact="true";const more=el("button","pa5-toggle","See all "+tiles.length+" stories ↓");more.type="button";more.setAttribute("aria-expanded","false");more.addEventListener("click",()=>{const open=gallery.dataset.pa5Compact==="true";gallery.dataset.pa5Compact=open?"false":"true";more.setAttribute("aria-expanded",String(open));more.textContent=open?"Show fewer stories ↑":"See all "+tiles.length+" stories ↓";});gallery.after(more);}
 const main=document.querySelector("main");const research=document.body.classList.contains("pa4-research-home");
 const extra=research?[...document.querySelectorAll("body > header.hero, body > .wrap, body > main")]:[...main?.children||[]].filter(x=>x!==root&&!x.contains(root));
 const rest=extra.filter(x=>!x.contains(root));if(!rest.length)return;
 const c=el("div","pa5-library");const copy=el("div");copy.append(el("span","pa5-eyebrow","WANT THE FULL INVESTIGATION?"),el("h2",null,"All the research. One click away."),el("p",null,"Open the original charts, source citations and detailed findings."));
 const btn=el("button","pa5-library-button","Explore the full research →");btn.type="button";btn.setAttribute("aria-expanded","false");c.append(copy,btn);root.after(c);
 rest.forEach(x=>x.classList.add("pa5-home-hidden"));
 const reveal=()=>{rest.forEach(x=>x.classList.remove("pa5-home-hidden"));btn.setAttribute("aria-expanded","true");btn.textContent="Hide detailed research ↑";};
 const conceal=()=>{rest.forEach(x=>x.classList.add("pa5-home-hidden"));btn.setAttribute("aria-expanded","false");btn.textContent="Explore the full research →";c.scrollIntoView({block:"start"});};
 btn.addEventListener("click",()=>btn.getAttribute("aria-expanded")==="false"?reveal():conceal());
 if(location.hash)reveal();
 document.addEventListener("click",e=>{const a=e.target.closest?.('a[href^="#"]');if(a&&a.getAttribute("href")!=="#")reveal();},true);
 window.addEventListener("hashchange",()=>{if(location.hash)reveal();});
}
function topic(main){
 const data=themes[path];if(!data)return;
 const pre=el("section","pa5-topic-hero");pre.setAttribute("aria-label","Topic in ten seconds");
 const left=el("div","pa5-intro");left.append(el("span","pa5-eyebrow","THE 10-SECOND VERSION"),el("h2",null,data[0]),el("p",null,data[1]));
 const diagram=el("div","pa5-process");diagram.setAttribute("aria-label","Illustrative topic pathway, not quantitative data");diagram.append(el("small",null,"HOW TO EXPLORE THIS"));
 data[3].forEach((t,i)=>{const item=el("div","pa5-stage");item.append(illustration(i===0?"place":i===1?data[2]:"proof",colors[i]),el("b",null,t));diagram.append(item);if(i<2)diagram.append(el("span","pa5-arrow","→"));});
 pre.append(left,diagram);main.prepend(pre);
 const hero=main.querySelector(":scope > section.hero, :scope > .hero");
 if(hero&&!hero.querySelector("input,select,textarea,form"))hero.classList.add("pa5-old-hero-hidden");
 if(path==="my-life.html"){pre.classList.add("pa5-topic-light");return;}
 const sections=[...main.children].filter(x=>x.tagName==="SECTION"&&x!==pre&&!x.classList.contains("hero")&&x.querySelector("h2"));
 const rows=[],seen=new Set();
 for(const sec of sections){
  const h=sec.querySelector("h2");const title=brief(h?.textContent||"",73);if(!title||seen.has(title))continue;seen.add(title);
  if(!sec.id)sec.id="pa5-chapter-"+(rows.length+1);
  const essential=!!sec.querySelector("input, select, textarea, form");
  rows.push({sec,id:sec.id,title,essential});
 }
 if(rows.length<2)return;
 const panel=el("section","pa5-explorer");panel.id="pa5-explorer";
 const head=el("div","pa5-explorer-head");head.append(el("span","pa5-eyebrow","CHOOSE A CHAPTER"),el("h2",null,"A quick picture. A deeper answer when you want it."));panel.append(head);
 const grid=el("div","pa5-chapter-grid");grid.dataset.compact=rows.length>6?"true":"false";
 const buttonMap=new Map();
 function reveal(selected,scroll){
  for(const r of rows){if(r.essential)continue;const show=r===selected;r.sec.classList.toggle("pa5-hidden-chapter",!show);r.sec.setAttribute("aria-hidden",String(!show));}
  for(const [id,b] of buttonMap){const on=id===selected?.id;b.setAttribute("aria-expanded",String(on));b.classList.toggle("pa5-selected",on);}
  if(selected&&scroll)selected.sec.scrollIntoView({behavior:window.matchMedia("(prefers-reduced-motion: reduce)").matches?"auto":"smooth",block:"start"});
 }
 rows.forEach((r,i)=>{
  const b=el("button","pa5-chapter-card");b.type="button";b.setAttribute("aria-controls",r.id);b.setAttribute("aria-expanded",String(r.essential));
  const art=el("span","pa5-chapter-art");art.append(illustration(["place","owners","trend","proof"][i%4],colors[i%colors.length]));
  const title=el("span","pa5-chapter-copy");title.append(el("small",null,"CHAPTER "+String(i+1).padStart(2,"0")),el("strong",null,r.title),el("span","pa5-cta",r.essential?"Go to the tool →":"Explore the evidence →"));
  b.append(art,title);b.addEventListener("click",()=>r.essential?r.sec.scrollIntoView({behavior:"smooth",block:"start"}):reveal(r,true));
  grid.append(b);buttonMap.set(r.id,b);
  if(!r.essential)r.sec.classList.add("pa5-hidden-chapter");
 });
 panel.append(grid);
 if(rows.length>6){const more=el("button","pa5-toggle","Show all "+rows.length+" chapters ↓");more.type="button";more.setAttribute("aria-expanded","false");more.addEventListener("click",()=>{const show=grid.dataset.compact==="true";grid.dataset.compact=show?"false":"true";more.setAttribute("aria-expanded",String(show));more.textContent=show?"Show fewer chapters ↑":"Show all "+rows.length+" chapters ↓";});panel.append(more);}
 pre.after(panel);
 for(const r of rows){if(r.essential)continue;const back=el("button","pa5-back","← Back to chapter cards");back.type="button";back.addEventListener("click",()=>{reveal(null,false);panel.scrollIntoView({behavior:"smooth",block:"start"});});r.sec.append(back);}
 function showHash(){
  if(!location.hash)return;let target;try{target=document.getElementById(decodeURIComponent(location.hash.slice(1)));}catch(e){return;}
  if(!target)return;const found=rows.find(x=>x.sec===target||x.sec.contains(target));if(found&&!found.essential)reveal(found,false);
 }
 document.addEventListener("click",e=>{const a=e.target.closest?.('a[href^="#"]');if(!a)return;const id=a.getAttribute("href")?.slice(1);if(!id)return;const target=document.getElementById(id);if(!target)return;const r=rows.find(x=>x.sec===target||x.sec.contains(target));if(r&&!r.essential)reveal(r,false);},true);
 window.addEventListener("hashchange",showHash);showHash();
}
function start(){if(document.documentElement.dataset.pa5)return;const main=document.querySelector("main");if(!main)return;document.documentElement.dataset.pa5="active";path==="index.html"?home():topic(main);}
const ready=()=>window.requestAnimationFrame(start);
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",ready,{once:true});else ready();
})();