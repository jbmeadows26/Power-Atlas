/* Interactive market-power stories use the same dated evidence register as the full explorer. */
(()=>{"use strict";
const root=document.getElementById("market-power-pathways");
if(!root)return;
const choices=[
 {id:"pbms",short:"Medicine",headline:"Three gatekeepers between you and your prescriptions",actors:[["Express Scripts","The Cigna Group"],["CVS Caremark","CVS Health"],["OptumRx","UnitedHealth Group"]],actorLabel:"Documented operating business → parent",lever:"Drug formularies, rebates and pharmacy networks",outcome:"Potential out-of-pocket costs, independent-pharmacy access and plan choices",next:"Look at the PBM behind your plan and compare in-network pharmacy options.",actorSource:"https://www.kff.org/other-health/what-to-know-about-pharmacy-benefit-managers-pbms-and-federal-efforts-at-regulation/"},
 {id:"beef",short:"Groceries",headline:"Four giant meatpackers negotiate with ranchers",actors:[["Cargill","Major processor"],["Tyson Foods","Major processor"],["JBS USA","Major processor"],["National Beef","Major processor"]],actorLabel:"Named large processors, not individual company market shares",lever:"Fewer rival buyers for finished cattle",outcome:"Potential pressure on rancher payments; retail beef price impacts require separate evidence",next:"Follow the supply chain. Do not treat the producer concentration ratio as a grocery markup.",actorSource:"https://www.ers.usda.gov/amber-waves/2024/january/concentration-in-u-s-meatpacking-industry-and-how-it-affects-competition-and-cattle-prices"},
 {id:"hospitals",short:"Healthcare",headline:"Hospital markets can leave patients with few alternatives",actors:[["Local hospital","Provider"],["Health system","Ownership / affiliation"],["Insurer","Negotiates coverage"]],actorLabel:"Illustrative relationship; actual owners depend on location",lever:"Negotiating leverage and referral networks in local hospital markets",outcome:"Potentially higher negotiated prices and fewer nearby options; not a household surcharge",next:"Check local system ownership and your insurer’s in-network choices.",actorSource:"https://www.gao.gov/products/gao-25-107450"},
 {id:"jobs",short:"Paychecks",headline:"Fewer employers can weaken bargaining power",actors:[["Worker","Job seeker"],["Local employers","Same occupation and area"],["Competing job offers","Bargaining alternatives"]],actorLabel:"Illustrative labor-market structure; no single national owner",lever:"Recruitment competition, noncompetes and local labor demand",outcome:"Possible wage pressure; measured concentration does not establish an individual wage loss",next:"Compare employers for your occupation and commuting area rather than national company shares.",actorSource:"https://www.bls.gov/cew/"},
 {id:"search",short:"Online",headline:"The search gatekeeper also controls a key doorway to customers",actors:[["Google Search","Operating service"],["Alphabet","Corporate parent"],["Publishers & advertisers","Business users"]],actorLabel:"Documented operating service and corporate parent",lever:"Default placement and distribution agreements",outcome:"Effects on competing search engines, advertisers and access; not a verified personal fee",next:"Compare alternative services and read the court finding separately from ongoing remedies.",actorSource:"https://www.justice.gov/atr/case/us-and-plaintiff-states-v-google-llc-2020"}
];
const $=s=>root.querySelector(s);
const E=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n};
const button=(txt,cls)=>{const e=E("button",cls,txt);e.type="button";return e};
let all=new Map();let selected="pbms";
function evidenceName(kind){return kind==="finding"?"Court finding":kind==="allegation"?"Allegation / proceeding":kind==="context"?"Regulated structure":"Measured research"}
function render(){
 const a=choices.find(c=>c.id===selected),c=all.get(selected);if(!a||!c)return;
 for(const b of root.querySelectorAll("[data-mpx-id]"))b.setAttribute("aria-pressed",String(b.dataset.mpxId===selected));
 const metric=$("#mpxMeasure"),detail=$("#mpxDetail"),extra=$("#mpxExtra");metric.replaceChildren();detail.replaceChildren();extra.replaceChildren();
 const eyebrow=E("span","mpx-kicker",c.topic+" · "+c.period);metric.append(eyebrow);
 if(typeof c.metric==="number"){
  const ring=E("div","mpx-ring");const amount=(c.unit==="~%"?"~":c.unit===">%"?">":"")+c.metric+"%";ring.style.setProperty("--progress",Math.min(100,Math.max(0,c.metric))+"%");
  ring.append(E("span",null,amount));ring.setAttribute("role","img");ring.setAttribute("aria-label",amount+" "+c.metricLabel);metric.append(ring);
 }else metric.append(E("div","mpx-ring", "See case"));
 metric.append(E("h3",null,c.metricLabel));metric.append(E("p",null,"Defined market: "+c.scope));metric.append(E("span","mpx-source-badge",evidenceName(c.kind)+" · Dated measure"));
 detail.append(E("span","mpx-kicker","WHO IS BEHIND IT?"),E("h3",null,a.headline));
 const ownership=E("div","mpx-ownership");for(const [brand,parent] of a.actors){const card=E("div","mpx-node");card.append(E("small",null,"Name / relationship"),E("strong",null,brand),E("span","mpx-arrow","↓"),E("span",null,parent));ownership.append(card)}detail.append(ownership);
 detail.append(E("p","mpx-scope",a.actorLabel));
 const flow=E("div","mpx-flow");
 for(const [label,txt] of [["01 / LEVER",a.lever],["02 / IMPACT TO TEST",a.outcome],["03 / YOUR NEXT STEP",a.next]]){const card=E("div");card.append(E("b",null,label),E("p",null,txt));flow.append(card)}detail.append(flow);
 const proof=E("div","mpx-proof"),kind=E("span","mpx-pill",evidenceName(c.kind));kind.dataset.kind=c.kind;proof.append(kind,E("small",null,"Evidence does not itself establish a national consumer price surcharge."));detail.append(proof);
 const actions=E("div","mpx-actions"),open=E("a",null,"Explore full case →"),original=E("a",null,"Read original evidence ↗");open.href="market-power.html?case="+encodeURIComponent(c.id)+"#explore";original.href=c.source;original.target="_blank";original.rel="noopener noreferrer";actions.append(open,original);detail.append(actions);
 const source=E("p","mpx-scope","Relationship evidence: "),sourceLink=E("a",null,"Check operator / parent and context ↗");sourceLink.href=a.actorSource;sourceLink.target="_blank";sourceLink.rel="noopener noreferrer";source.append(sourceLink);detail.append(source);
 const items=[["WHO MAY BENEFIT",c.benefits],["WHO MAY PAY",c.costs],["WHAT IS NOT ESTABLISHED","No case here converts a concentration ratio into a verified percent of your bill. Compare the place, product, date and independent causes first."]];
 for(const [head,body] of items){let box=E("article");box.append(E("b",null,head),E("p",null,body));extra.append(box)}
}
const tabs=$("#mpxTabs");choices.forEach(c=>{const b=button(c.short);b.dataset.mpxId=c.id;b.setAttribute("aria-pressed","false");b.addEventListener("click",()=>{selected=c.id;render()});tabs.append(b)});
fetch("market-power.json",{cache:"no-store"}).then(r=>{if(!r.ok)throw Error("Unavailable");return r.json()}).then(data=>{if(data.schema!=="power-atlas.market-power.v1"||!Array.isArray(data.cases))throw Error("Invalid evidence");all=new Map(data.cases.map(x=>[x.id,x]));render()}).catch(()=>{const m=$("#mpxDetail");m.textContent="The evidence register is temporarily unavailable. The original case links remain in the explorer below.";$("#mpxMeasure").textContent="Data temporarily unavailable."});
})();
