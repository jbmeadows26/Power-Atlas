/* Power Atlas: Political Money visual explainer.
   Illustrative paths only; record-level connections remain in the linked source explorers. */
(()=>{
"use strict";
const pathways=[
  {
    id:"campaign",name:"Campaign cash",icon:"●",tag:"RECORDED CONTRIBUTIONS",
    headline:"Who finances the candidates?",
    summary:"Match reported contributors to candidates and committees. Keep the election cycle and committee type visible.",
    stages:[["DONOR","Named contributor"],["RECIPIENT","Candidate or PAC"],["DISCLOSED USE","Campaign spending"],["NEXT QUESTION","Public decisions"]],
    known:"FEC filings can establish a reported contribution, recipient, date and amount.",
    gap:"A contribution alone cannot establish a change in a vote, rule or policy.",
    internal:"election-money.html",internalLabel:"Compare election funding",
    source:"FEC campaign finance",sourceUrl:"https://www.fec.gov/data/",coverage:"Indexed committee data and original filing links"
  },
  {
    id:"outside",name:"Outside spending",icon:"◎",tag:"INDEPENDENT EXPENDITURES",
    headline:"Who pays to shape the message?",
    summary:"Independent groups may spend for or against candidates. Separate committee donations from advertisements and other expenditures.",
    stages:[["FUNDING","Donor or group"],["ORGANIZATION","Outside-spending committee"],["REPORTED USE","Ads or outreach"],["NEXT QUESTION","Election outcomes"]],
    known:"FEC reports identify disclosed committee receipts and reported independent expenditures.",
    gap:"Outside spending is not automatically candidate coordination or proof that an ad changed an election.",
    internal:"donor-intelligence.html",internalLabel:"Explore major donors",
    source:"FEC independent expenditures",sourceUrl:"https://www.fec.gov/data/independent-expenditures/",coverage:"Source-linked federal records; not a causal ad-effect study"
  },
  {
    id:"opaque",name:"Dark money",icon:"◐",tag:"DISCLOSURE BLIND SPOTS",
    headline:"Where does the trail go dark?",
    summary:"A group may report political spending even when its original contributors are not publicly named.",
    stages:[["ORIGIN","Original donor unknown"],["VEHICLE","Certain nonprofit groups"],["VISIBLE RECORD","Reported grants or spending"],["OPEN GAP","Source of funds"]],
    known:"Public nonprofit and election filings can establish some organization-level grants or expenses.",
    gap:"Most non-527 tax-exempt filers generally need not make contributor names public. A grant does not identify the grantmaker's own donors.",
    internal:"money-sources.html",internalLabel:"Inspect the source trail",
    source:"IRS disclosure rules",sourceUrl:"https://www.irs.gov/charities-non-profits/public-disclosure-and-availability-of-exempt-organizations-returns-and-applications-contributors-identities-not-subject-to-disclosure",coverage:"Partially indexed; undisclosed original funders remain unknown"
  },
  {
    id:"lobbying",name:"Lobbying",icon:"↗",tag:"POLICY ADVOCACY",
    headline:"Who seeks access to decision-makers?",
    summary:"Follow lobbying clients, registrants, issues and reported costs before comparing with public legislative or agency actions.",
    stages:[["CLIENT","Company or association"],["ADVOCATE","Lobbying firm or staff"],["REPORTED ISSUE","Bill, rule or agency"],["NEXT QUESTION","Official action"]],
    known:"LD-1, LD-2 and LD-203 filings can describe clients, lobbying issues and reportable activity.",
    gap:"The filings do not show that a lobbying effort caused any particular vote, award or regulatory change.",
    internal:"business-influence.html",internalLabel:"Investigate business influence",
    source:"Official LDA filings",sourceUrl:"https://lda.gov/filings/public/filing/search/",coverage:"Official source portal; do not imply records are fully joined"
  },
  {
    id:"benefits",name:"Public benefits",icon:"▥",tag:"TAXPAYER MONEY",
    headline:"Did a company also receive public money?",
    summary:"Compare documented corporate political activity with actual federal awards, subsidies and decisions—without treating coincidence as causation.",
    stages:[["COMPANY","Identified entity"],["SEPARATE RECORD","Political activity"],["PUBLIC RECORD","Contract or grant"],["IMPACT TO TEST","Jobs, prices, services"]],
    known:"USAspending identifies many federal contracts, grants and other awards by recipient.",
    gap:"Ownership must be matched accurately; timing and alternative explanations must be tested before alleging favoritism or harm.",
    internal:"business-influence.html",internalLabel:"Explore company investigations",
    source:"USAspending award data",sourceUrl:"https://www.usaspending.gov/",coverage:"Official awards portal; no automatic donor-to-contract linkage"
  },
  {
    id:"assets",name:"Official holdings",icon:"◇",tag:"FINANCIAL INTERESTS",
    headline:"What financial interests do officials disclose?",
    summary:"Follow assets and trading disclosures alongside committee assignments and decisions. Holdings are not campaign donations.",
    stages:[["OFFICIAL","Named public filer"],["DISCLOSURE","Assets or transactions"],["EXPOSURE","Company or industry"],["NEXT QUESTION","Related public action"]],
    known:"Public financial disclosures can identify reportable holdings or transactions subject to their filing rules.",
    gap:"A disclosed interest does not itself establish insider trading, a conflict finding or a changed policy outcome.",
    internal:"public-trading.html",internalLabel:"Review public trading records",
    source:"Senate disclosure",sourceUrl:"https://www.senate.gov/legislative/Public_Disclosure/financial-disclosure.htm",coverage:"Separate financial disclosures, not election contribution records"
  }
];
const el=(tag,cls,txt)=>{
 const x=document.createElement(tag);
 if(cls)x.className=cls;
 if(txt!==undefined)x.textContent=txt;
 return x;
};
const link=(href,txt,cls,external)=>{
 const x=el("a",cls,txt);x.href=href;
 if(external){x.target="_blank";x.rel="noopener noreferrer";}
 return x;
};
function mount(host){
 if(!host||host.querySelector(".pmx"))return;
 host.classList.add("vs6-topic--pmx");
 const wrap=el("div","pmx");wrap.setAttribute("aria-label","Explore the political money investigation");
 const guide=el("div","pmx-intro");
 guide.append(el("span","pmx-kicker","SIX WAYS TO FOLLOW INFLUENCE"));
 guide.append(el("h2","pmx-h2","The money trail is bigger than a donation."));
 guide.append(el("p","pmx-sub","Pick a trail. See the records we can check—and where the evidence stops."));
 wrap.append(guide);
 const selector=el("div","pmx-pathways");selector.setAttribute("role","group");selector.setAttribute("aria-label","Choose a political money pathway");
 const buttons=new Map();
 for(const t of pathways){
  const b=el("button","pmx-path");
  b.type="button";b.dataset.pathway=t.id;b.setAttribute("aria-pressed",String(t.id==="campaign"));
  b.append(el("span","pmx-path-icon",t.icon),el("span","pmx-path-name",t.name));
  buttons.set(t.id,b);selector.append(b);
 }
 wrap.append(selector);
 const chapter=el("div","pmx-chapter");chapter.setAttribute("aria-live","polite");chapter.setAttribute("aria-atomic","true");
 const kicker=el("span","pmx-tag");
 const title=el("h3","pmx-title");
 const summary=el("p","pmx-explain");
 const route=el("div","pmx-route");route.setAttribute("aria-label","Conceptual research path");
 const caption=el("p","pmx-caption","Concept map only. Arrows are research questions, not verified end-to-end payments.");
 const split=el("div","pmx-evidence");
 const yes=el("div","pmx-fact");const no=el("div","pmx-gap");
 yes.append(el("span","pmx-state pmx-state--filed","● DOCUMENTED IN RECORDS"));
 no.append(el("span","pmx-state pmx-state--gap","◌ STILL TO ESTABLISH"));
 const yesBody=el("p");const noBody=el("p");yes.append(yesBody);no.append(noBody);split.append(yes,no);
 const actions=el("div","pmx-actions");
 const deep=link("#","Explore records →","pmx-mainlink");
 const original=link("#","Original filing source ↗","pmx-sourcelink",true);
 actions.append(deep,original);
 const status=el("small","pmx-coverage");
 chapter.append(kicker,title,summary,route,caption,split,actions,status);wrap.append(chapter);
 const resources=el("div","pmx-bridge");
 resources.append(el("div","pmx-bridge-copy","The next question: did policy, contracts or prices change?"));
 const links=el("div","pmx-bridge-links");
 links.append(
  link("business-influence.html","Corporate influence →"),
  link("my-life.html#why","Impact where you live →"),
  link("reform-lab.html","What could change? →")
 );
 resources.append(links);wrap.append(resources);
 const disclosure=el("details","pmx-method");
 disclosure.append(el("summary",null,"How do we distinguish influence from proof?"));
 disclosure.append(el("p",null,"Check each original filing, the legal identities of both parties, the amount, the date, the decision record and plausible alternative explanations. A donation, lobbying report or contract is evidence of that record—not by itself evidence that money bought an outcome."));
 wrap.append(disclosure);
 function select(id){
  const t=pathways.find(x=>x.id===id)||pathways[0];
  for(const [name,b] of buttons)b.setAttribute("aria-pressed",String(t.id===name));
  kicker.textContent=t.tag;title.textContent=t.headline;summary.textContent=t.summary;
  route.replaceChildren();
  for(const [i,stage] of t.stages.entries()){
   const node=el("div","pmx-node"+(i===t.stages.length-1?" pmx-node--question":""));
   node.append(el("small",null,stage[0]),el("strong",null,stage[1]));
   route.append(node);
   if(i<t.stages.length-1)route.append(el("span","pmx-route-arrow","→"));
  }
  yesBody.textContent=t.known;noBody.textContent=t.gap;
  deep.href=t.internal;deep.textContent=t.internalLabel+" →";
  original.href=t.sourceUrl;original.textContent=t.source+" ↗";
  status.textContent="Data coverage: "+t.coverage+".";
 }
 selector.addEventListener("click",event=>{
  const button=event.target.closest("button[data-pathway]");
  if(button&&selector.contains(button))select(button.dataset.pathway);
 });
 select("campaign");
 const cta=host.querySelector(".vs6-expand");
 if(cta)host.insertBefore(wrap,cta);else host.append(wrap);
}
window.PowerAtlasPoliticalMoney={mount};
})();
