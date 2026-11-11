/* Power Atlas — distinct social-issue cards. Global themes are not ZIP-level measurements. */
(function(){
"use strict";
const sources={
  un:"https://www.un.org/en/global-issues",
  social:"https://desapublications.un.org/publications/world-social-report-2025-new-policy-consensus-accelerate-social-progress",
  ilo:"https://www.ilo.org/",
  oecd:"https://www.oecd.org/en/topics/sub-issues/trust-in-government.html",
  who:"https://www.who.int/",
  unesco:"https://www.unesco.org/en/education",
  rights:"https://www.ohchr.org/en",
  unicef:"https://www.unicef.org/",
  unhcr:"https://www.unhcr.org/global-trends",
  ipcc:"https://www.ipcc.ch/report/ar6/syr/",
  imf:"https://www.imf.org/en/Publications/FM",
  iea:"https://www.iea.org/",
  fao:"https://www.fao.org/",
  ftc:"https://www.ftc.gov/news-events/topics/protecting-consumer-privacy-security",
  unodc:"https://www.unodc.org/"
};
/* [slug,heading,domain,icon,short introduction,details,closest existing cost/civic track,original source,source name].
   These 20 entries exclude the 9 existing local-life cards. Related tracks are explicitly
   adjacent evidence, NOT measurements of the broader topic or proof of cause. */
const topics=[
["mobility","Upward mobility","ECONOMIC SECURITY","↗","Can hard work still improve your standard of living?","Compare wages and the price of housing, childcare, education and care. Rules, costs and access differ by location and generation.","housing","social","UN · World Social Report"],
["poverty","Poverty & insecure work","ECONOMIC SECURITY","◍","One setback can undo years of progress.","Look at low wages, informal employment, unstable work and gaps in social protection. Global poverty measures cannot be treated as local ZIP estimates.","work","social","UN · World Social Report"],
["wealth","Wealth & concentrated power","ECONOMIC SECURITY","◆","Who owns the assets—and who holds the leverage?","Examine unequal ownership, market power, tax advantages and the channels connecting wealth with policymaking. Unequal outcomes alone do not prove misconduct.","representation","social","UN · World Social Report"],
["ai-work","AI & workforce disruption","ECONOMIC SECURITY","⌘","What happens when work changes faster than opportunity?","Track automation, entry-level pathways, wages, job quality, retraining and where productivity gains flow. Separate forecasts from observed displacement.","work","ilo","ILO · Labor research"],
["institutions","Institutional trust & accountability","DEMOCRACY & RIGHTS","▥","What happens when people stop trusting the referees?","Explore accountability, institutional performance, corruption risks and democratic safeguards. Evidence of a failure is not proof all institutions have failed.","representation","oecd","OECD · Trust research"],
["information","Disinformation & polarization","DEMOCRACY & RIGHTS","≋","Can people still agree on what is true?","Examine information quality, platform incentives, political polarization and independent verification. Different viewpoints are not automatically misinformation.","representation","un","UN · Global Issues"],
["rights","Civil rights & equal treatment","DEMOCRACY & RIGHTS","⚖","Do the rules protect everyone equally?","Explore racial, ethnic, gender and other discrimination, voting access, fair treatment, trafficking and forced labor with legal and geographic context.","representation","rights","UN · Human Rights"],
["mental","Mental health & addiction","HEALTH & COMMUNITY","♡","Care is only useful when people can reach it.","Look at mental-health strain, substance-use disorders, addiction treatment, stigma and affordability, including youth-specific risks.","health","who","WHO · Mental health and health systems"],
["isolation","Loneliness & civic connection","HEALTH & COMMUNITY","◎","What changes when community ties weaken?","Study isolation, friendship, civic participation and belonging across generations. Avoid assuming a single technology or group caused the decline.","public-services","social","UN · Social cohesion research"],
["demography","Aging, fertility & family life","HEALTH & COMMUNITY","◇","Can families and public systems adapt to demographic change?","Track fertility, aging, care needs, pension pressures, family formation and policy trade-offs. Immigration, retirement and productivity are different levers.","schools","un","UN · Population and social issues"],
["childhood","Childhood & the attention economy","TECHNOLOGY & SOCIETY","◉","Who protects children online and offline?","Explore cyberbullying, exploitative design, attention, youth mental health and education. Distinguish associations from established causal effects.","schools","unicef","UNICEF · Child wellbeing"],
["privacy","Privacy & surveillance","TECHNOLOGY & SOCIETY","▣","Who benefits from knowing everything about you?","Trace data brokers, consumer tracking, surveillance technologies and protections. Separate lawful collection, alleged misuse and documented violations.","representation","ftc","FTC · Privacy and data security"],
["climate","Climate & environmental justice","PLANET & RESOURCES","☀","Who bears the heaviest costs of a changing climate?","Show heat, floods, drought, pollution exposure, adaptation and uneven climate vulnerability. Local risk requires local evidence.","energy","ipcc","IPCC · Climate assessment"],
["resources","Food, water & resource security","PLANET & RESOURCES","◒","What happens when essentials become less reliable?","Examine hunger, agricultural disruption, clean-water access, food supply and resource scarcity. Household grocery bills are a related but different measure.","groceries","fao","FAO · Food security"],
["migration","Migration & integration","GLOBAL STABILITY","↝","Can receiving communities and newcomers thrive together?","Explore labor-market integration, services, housing capacity, rights and social cohesion. Distinguish voluntary migration from forced displacement.","housing","un","UN · International migration"],
["conflict","War, violence & displacement","GLOBAL STABILITY","⚑","What happens when safety and home disappear?","Track conflict, humanitarian access, forced displacement and spillovers into prices, infrastructure, public health and schooling. Use dated UNHCR definitions.","public-services","unhcr","UNHCR · Global Trends"],
["safety","Community safety & the rule of law","DEMOCRACY & RIGHTS","⬡","Do people feel safe—and are rules fairly enforced?","Explore crime, drug markets, public-space conditions, trafficking and equal access to justice. Perception, reported incidents and proven trends must remain separate.","public-services","unodc","UNODC · Crime and justice"],
["industry","Energy transition & industrial capacity","PLANET & RESOURCES","⚡","Can we build a cleaner, more resilient economy?","Examine grids, energy affordability, domestic manufacturing, critical infrastructure and decarbonization trade-offs.","energy","iea","IEA · Energy analysis"],
["debt","Public debt & social protection","ECONOMIC SECURITY","▤","Who pays for today's commitments tomorrow?","Compare debt servicing, taxes, retirement systems and public-service trade-offs. Spending pressure is not itself evidence of insolvency.","public-services","imf","IMF · Fiscal Monitor"],
["geopolitics","Great-power competition & supply chains","GLOBAL STABILITY","⌁","Why do distant rivalries affect prices at home?","Follow trade policy, semiconductors, critical minerals, shipping routes and strategic dependencies. Distinguish risks from realized disruptions.","transport","un","UN · Global Issues"]
];
function el(tag,klass,value){const node=document.createElement(tag);if(klass)node.className=klass;if(value!==undefined)node.textContent=value;return node;}
const existingIds=new Set(["housing","groceries","energy","health","work","schools","transport","public-services","representation"]);
if(new Set(topics.map(t=>t[0])).size!==topics.length||topics.some(t=>!existingIds.has(t[6])||!sources[t[7]])){console.error("Power Atlas issue catalog validation failed");return;}
/* All twenty additional topics belong in the exact SAME nine-topic grid under
   "What matters most right now?". Each remains explorable without inventing
   ZIP-level evidence or overwriting the nine source-backed local topic panels. */
function render(){
 const grid=document.getElementById("issueGrid");
 if(!grid)return;
 // Keep the nine canonical ZIP-connected cards. Replace only our own cards.
 grid.querySelectorAll(":scope > .pa-social-card").forEach(node=>node.remove());
 const fragment=document.createDocumentFragment();
 topics.forEach(t=>{
   const card=el("details","pa-social-card");card.dataset.socialTopic=t[0];
   const summary=el("summary","pa-social-summary");
   const icon=el("span","issue-icon pa-social-icon",t[3]);icon.setAttribute("aria-hidden","true");
   const copy=el("span","pa-social-copy");
   copy.append(el("strong",null,t[1]),el("small",null,"Explore why →"));
   summary.append(icon,copy);
   const body=el("div","pa-social-body");
   body.append(el("span","pa-social-group",t[2]),el("h4",null,t[4]),el("p",null,t[5]),el("span","pa-social-evidence-note","Global/national context · not a ZIP-level statistic"));
   const actions=el("div","pa-social-actions");
   const related=el("button","pa-social-related","Explore related local evidence");
   related.type="button";
   related.addEventListener("click",()=>{
     const choice=document.querySelector('#issueGrid button[data-topic="'+t[6]+'"]');
     if(choice)choice.click();
   });
   const source=el("a","pa-social-source","Original source ↗");
   source.href=sources[t[7]];source.target="_blank";source.rel="noopener noreferrer";
   source.title=t[8];source.setAttribute("aria-label","Open "+t[8]+" (new tab)");
   actions.append(related,source);body.append(actions);card.append(summary,body);
   card.addEventListener("toggle",()=>{
     // Only one expanded card in the unified grid; easier to scan on mobile.
     if(card.open&&card.isConnected)grid.querySelectorAll(".pa-social-card[open]").forEach(other=>{if(other!==card)other.open=false;});
   });
   fragment.append(card);
 });
 grid.append(fragment);
}
window.PowerAtlasSocialIssueCatalog=Object.freeze({count:topics.length,slugs:topics.map(t=>t[0]),render});
render();
})();