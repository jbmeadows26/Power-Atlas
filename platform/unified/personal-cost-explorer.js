/* Power Atlas: voluntary, client-only household cost scenarios.
   No user-entered values are sent to an endpoint or persisted. */
(function(){
"use strict";
var SOURCES={
 bls:"https://www.bls.gov/cpi/",
 food:"https://www.fna.usda.gov/research/cnpp/usda-food-plans/cost-food-monthly-reports",
 ftc:"https://www.ftc.gov/",
 mortgage:"https://www.consumerfinance.gov/consumer-tools/mortgages/shopping-for-a-mortgage/",
 energy:"https://www.energy.gov/energysaver",
 eia:"https://www.eia.gov/electricity/state/",
 health:"https://www.healthcare.gov/choose-a-plan/your-total-costs/",
 wage:"https://www.dol.gov/agencies/whd",
 education:"https://nces.ed.gov/ccd/schoolsearch/",
 transport:"https://www.transit.dot.gov/ntd",
 taxes:"https://www.irs.gov/filing",
 government:"https://www.usa.gov/state-local-governments",
 election:"https://www.fec.gov/data/"
};
function part(id,name,kind,driver,decisionMaker,choice,source,flexible){
 return {id:id,name:name,kind:kind,driver:driver,decisionMaker:decisionMaker,choice:choice,source:source,flexible:flexible};
}
var TOPICS={
 housing:{
 title:"Housing",intro:"Break the housing payment into what you actually pay. For an owner, separate principal and interest from escrow; renters can enter rent alone.",
 caution:"Do not count property taxes or insurance twice if your mortgage payment already includes escrow.",
 parts:[
 part("payment","Rent or mortgage principal + interest","Market & finance","Land availability, supply, demand, financing rates and landlord or lender terms.","Property owners, lenders and local land-use officials.","Compare renewal terms or fully priced housing / loan alternatives, including moving costs.","mortgage",false),
 part("tax","Property tax paid separately","Public policy","Local assessed value, tax rates and exemptions; the precise bill requires parcel data.","Local assessors, taxing authorities and state lawmakers.","Check assessment, exemptions and appeal deadlines with your local assessor.","government",true),
 part("insurance","Home / renters insurance","Insurance market","Coverage, insured risk, underwriting and insurer pricing.","Insurers and state insurance regulators.","Compare equivalent deductibles and coverage, not just premiums.","bls",true),
 part("fees","HOA, maintenance and housing fees","Property & services","Maintenance, association decisions, repair rates and contract costs.","HOAs, contractors and property owners.","Compare service providers or review recurring fees without deferring needed repairs.","mortgage",true)
 ]},
 groceries:{
 title:"Groceries",intro:"Track what lands in the cart, not a generic national 'family basket'. Add fees only when you actually pay them.",
 caution:"Prices differ by product, package size, store, promotion, neighborhood and household needs. Compare the price per unit and usable quantity.",
 parts:[
 part("produce","Fruit and vegetables","Supply & retail pricing","Weather, seasons, distribution and retailer pricing or promotions.","Growers, wholesalers and grocery chains.","Compare seasonal or frozen equivalents by unit price.","food",true),
 part("protein","Meat, fish or other proteins","Supply & retail pricing","Feed and production costs, processing, transport and retailer competition.","Producers, processors and grocery chains.","Compare genuinely equivalent proteins and serving costs.","bls",true),
 part("staples","Bread, grains, dairy and pantry items","Supply & retail pricing","Agricultural inputs, manufacturing, packaging, private labels and retailer markups.","Manufacturers and retailers.","Compare store brands and actual unit prices.","food",true),
 part("extras","Drinks, snacks and prepared foods","Product & consumer choice","Brand premiums, packaging, advertising, processing and promotions.","Food brands and retailers.","Compare equivalent smaller baskets, preparation and branded versus store options.","ftc",true),
 part("delivery","Delivery, service fees and memberships","Service pricing","Fulfillment labor, platform commissions, delivery and membership charges.","Delivery platforms and stores.","Compare pickup or in-store shopping, including your travel costs.","ftc",true)
 ]},
 energy:{
 title:"Utilities",intro:"Look at each service bill separately. What you pay depends on your actual consumption, plan and local provider, not the national price index.",
 caution:"Do not add utilities already included in rent. Check fixed charges and unit rates before trying a lower-usage scenario.",
 parts:[
 part("electric","Electricity","Rate & consumption","kWh used, supply costs, regulated delivery charges and applicable taxes.","Utilities, energy suppliers and regulators.","Review kWh and rate; estimate only realistic efficiency or plan changes.","eia",true),
 part("heat","Natural gas, heating oil or other fuel","Fuel & consumption","Fuel input prices, delivery charges, weather and building efficiency.","Fuel suppliers, utilities and regulators.","Compare efficiency measures and eligible rate plans safely.","energy",true),
 part("water","Water and sewer","Infrastructure & rates","Metered usage, fixed system costs, local infrastructure and municipal rates.","Local water utilities and governing boards.","Check leaks, billing tiers and assistance programs.","government",true),
 part("internet","Broadband and phone connectivity","Competition & contracts","Local network availability, advertised packages and promotional expirations.","Telecom carriers and regulators.","Compare total post-promotion costs and reliable available alternatives.","ftc",true)
 ]},
 health:{
 title:"Healthcare",intro:"Use your actual net premium and a monthly average of the care you expect to use. Compare the total cost of coverage, not premiums alone.",
 caution:"This is a budgeting scenario, not medical advice. Do not reduce necessary care or medicines to reach a target. Annual deductibles and out-of-pocket limits can substantially change actual costs.",
 parts:[
 part("premium","Insurance premium after subsidy","Insurance & policy","Plan design, employer contributions, subsidies, age and local plan offerings.","Insurers, employers and public benefit administrators.","Compare total annual costs, network coverage and eligibility.","health",true),
 part("care","Visits, copays and coinsurance","Provider & plan pricing","Negotiated provider rates, covered services, deductibles and network status.","Health plans, providers and regulators.","Verify in-network options and expected yearly care needs.","health",true),
 part("rx","Prescriptions and supplies","Manufacturer & benefit design","Manufacturer prices, formulary tiers, pharmacy contracts and copay rules.","Manufacturers, pharmacy benefit entities and health plans.","Ask a pharmacist or prescriber about covered equivalents; do not independently switch therapy.","health",true),
 part("other","Dental, vision and other out-of-pocket care","Coverage & services","Plan exclusions, provider pricing and visit frequency.","Plans and care providers.","Compare comparable coverage and fees for expected services.","health",true)
 ]},
 work:{
 title:"Jobs & pay",intro:"These are direct costs of earning income. Wages, salaries and employment prospects appear in the research below and are not invented as household 'expenses'.",
 caution:"If commuting and childcare are already counted under Getting around or Schools & children, leave those rows blank here to avoid double-counting.",
 parts:[
 part("travel","Unreimbursed work travel","Work conditions","Distance, scheduling, employer reimbursement and transport availability.","Employers and transportation providers.","Compare reimbursement, remote days or schedules where available.","wage",true),
 part("gear","Tools, uniforms and equipment","Employer practice","Job requirements, tool costs, employer policies and reimbursement.","Employers and suppliers.","Check reimbursement and equivalent required purchases.","wage",true),
 part("training","Training, licensing and dues","Public rules & work","Credentialing requirements, training fees and employer support.","Licensing authorities, educators and employers.","Check employer-paid development and legitimate no-fee options.","wage",true),
 part("other","Other job-related expense","Consumer choice","Workplace policies, materials and recurring costs.","Employer and chosen service providers.","Compare a documented alternative without assuming eligibility.","wage",true)
 ]},
 schools:{
 title:"Schools & children",intro:"Public education spending statistics do not equal what your household spends. Enter the actual childcare, after-school and other family expenses you pay.",
 caution:"Exclude childcare or transportation already included under Jobs & pay or Getting around.",
 parts:[
 part("childcare","Childcare and early learning","Labor & local supply","Care-worker wages, staffing ratios, capacity, subsidies and provider costs.","Care providers and state licensing / subsidy agencies.","Check eligibility for local childcare assistance and comparable licensed options.","education",true),
 part("after","After-school and holiday care","Capacity & services","Staffing, hours, fees and program availability.","Schools, nonprofits and private providers.","Compare school-based programs and hours against alternatives.","education",true),
 part("supplies","Supplies, technology and school fees","School policy & retail","School requirements, vendor pricing and district purchasing.","Schools, districts and retailers.","Check school-provided supplies and fee-waiver programs.","education",true),
 part("activities","Clubs, tutoring and activities","Services & choices","Program availability, instructor costs, fees and transport needs.","Program providers and schools.","Compare free school, library and community options where suitable.","education",true)
 ]},
 transport:{
 title:"Getting around",intro:"Compare the complete cost of getting where you need to go. A lower monthly fare may not outweigh time, access or lost reliability.",
 caution:"Do not count car costs or transit already counted as work expenses. Alternatives must preserve accessibility, essential trips and safety.",
 parts:[
 part("vehicle","Vehicle payment or lease","Finance & manufacturer pricing","Vehicle price, financing rate, dealer terms and contract duration.","Manufacturers, dealers and lenders.","Compare total financing costs, not just a lower monthly payment.","bls",true),
 part("fuel","Fuel or charging","Fuel & consumption","Energy prices, miles driven, vehicle efficiency and charging tariffs.","Energy suppliers, retailers and tax authorities.","Compare trip consolidation, fuel unit costs and real charging access.","bls",true),
 part("insure","Vehicle insurance","Insurance market","Driving history, coverage, local claims, state rules and insurer pricing.","Insurers and state insurance regulators.","Compare like-for-like coverage, limits and deductibles.","bls",true),
 part("upkeep","Maintenance, parking and tolls","Services & infrastructure","Repairs, labor rates, parking supply, tolls and local policy.","Repair businesses and local authorities.","Check preventive maintenance and suitable route/parking alternatives.","bls",true),
 part("transit","Public transit or rideshare fares","Public funding & platform","Fare structures, service networks, wages and platform pricing.","Transit authorities and transport platforms.","Compare passes and realistic route coverage.","transport",true)
 ]},
 "public-services":{
 title:"Taxes & local services",intro:"Taxes are paid under different jurisdictions and programs. This worksheet is a payment tracker—not a calculation of your legal tax liability or the value of services received.",
 caution:"Enter monthly equivalents. Exclude property taxes already counted in Housing, and avoid treating sales taxes embedded in purchases as a second expense.",
 parts:[
 part("property","Property taxes paid separately","Local budgets & assessments","Tax base, assessments, public spending and exemptions.","Local assessors and elected budget authorities.","Verify assessments and available relief directly.","government",true),
 part("income","Income taxes withheld or paid","Tax law & income","Taxable income, brackets, deductions and federal / state law.","Congress, state lawmakers and tax agencies.","Check official credits and withholding without assuming eligibility.","taxes",true),
 part("sales","Sales and excise taxes tracked separately","Consumption & tax rules","Rates, taxable purchases, exemptions and excise schedules.","State and local lawmakers.","Review legitimate exemptions; do not double-count amounts within purchases.","taxes",true),
 part("fees","Local permits, trash and service charges","Local service policy","Fees, service contracts, utility funding and local ordinances.","City / county administrations.","Check official billing rules, assistance and waivers.","government",true)
 ]},
 representation:{
 title:"Your voice",intro:"Political influence is not a household invoice. Assigning a dollar figure to how a donor or legislator affects your wallet without specific causal evidence would be misleading.",
 caution:"Instead, connect the verified decisions and disclosure records to your chosen issue. Distinguish documented relationships from claims about their effects.",
 parts:[]
 }
};
var root=null,topic="housing",values=Object.create(null);
var money=new Intl.NumberFormat("en-US",{style:"currency",currency:"USD",maximumFractionDigits:2});
function esc(v){return String(v==null?"":v).replace(/[&<>"']/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]})}
function fmt(n){return money.format(Math.round(n*100)/100)}
function number(v){if(v===null||v===undefined||String(v).trim()==="")return null;var n=Number(v);return Number.isFinite(n)&&n>=0&&n<=1000000?n:null}
function state(){if(!values[topic])values[topic]=Object.create(null);return values[topic]}
function rowValue(p,type){var x=state()[p.id]||{};return x[type]===undefined?"":x[type]}
function render(){
 root=document.getElementById("personalCostExplorer");if(!root)return;
 var cfg=TOPICS[topic]||TOPICS.housing,body=root.querySelector("#ceContent");
 root.querySelector("#ceTopic").textContent=cfg.title;
 root.querySelector("#ceIntro").textContent=cfg.intro;
 if(!cfg.parts.length){
  body.innerHTML='<div class="ce-voice"><strong>Accountability is measurable; a personal dollar amount is not yet proven.</strong><p>'+esc(cfg.caution)+'</p><div class="ce-actions"><a href="#corporatePaths">Follow verified ownership and decision records</a><a href="https://www.fec.gov/data/" target="_blank" rel="noopener noreferrer">Inspect disclosed political money</a><a href="#how">Explore nonpartisan civic options</a></div></div>';
  return;
 }
 body.innerHTML='<div class="ce-topline"><div class="ce-stats"><div><small>Your entered monthly cost</small><strong id="ceCurrent">—</strong></div><div><small>Compared scenario</small><strong id="ceScenario">—</strong></div><div><small>Possible annual difference</small><strong id="ceDifference">—</strong></div></div><button type="button" id="ceClear" class="secondary">Clear this category</button></div>'+
 '<p class="ce-helper">Amounts are optional. Enter a current monthly amount, then type a different option into the adjacent field to see the arithmetic. Blank alternative = unchanged. <strong>These are your assumptions, not quoted local prices or guaranteed savings.</strong></p>'+
 '<div class="ce-table-head"><span>Expense & price drivers</span><span>Current / month</span><span>Alternative / month</span></div>'+
 '<div class="ce-rows">'+cfg.parts.map(function(p){
  return '<article class="ce-line" data-ce-row="'+esc(p.id)+'"><div class="ce-line-main"><span class="ce-driver-type">'+esc(p.kind)+'</span><strong>'+esc(p.name)+'</strong><small>Who has influence: '+esc(p.decisionMaker)+'</small><div class="ce-share" aria-hidden="true"><span data-ce-share="'+esc(p.id)+'"></span></div><details><summary>Why this costs money · what can change</summary><p>'+esc(p.driver)+'</p><p><strong>A choice to investigate:</strong> '+esc(p.choice)+'</p><a href="'+esc(SOURCES[p.source])+'" target="_blank" rel="noopener noreferrer">Related official source ↗</a><p class="ce-caution">This source describes a mechanism or broad benchmark; it does not prove a local company or politician caused your bill.</p></details></div><label class="ce-price"><span class="ce-mobile-label">Current / month</span><span class="ce-dollar">$</span><input type="number" min="0" max="1000000" step="0.01" inputmode="decimal" data-ce-kind="current" data-ce-id="'+esc(p.id)+'" aria-label="'+esc(p.name)+' current monthly dollars" placeholder="—" value="'+esc(rowValue(p,"current"))+'"></label><label class="ce-price"><span class="ce-mobile-label">Alternative / month</span><span class="ce-dollar">$</span><input type="number" min="0" max="1000000" step="0.01" inputmode="decimal" data-ce-kind="scenario" data-ce-id="'+esc(p.id)+'" aria-label="'+esc(p.name)+' alternative monthly dollars" placeholder="—" value="'+esc(rowValue(p,"scenario"))+'"></label></article>'
 }).join("")+'</div>'+
 '<div class="ce-foot"><p id="cePriority" aria-live="polite">Enter your costs to see the largest component and where comparing options could matter.</p><p class="ce-warning">'+esc(cfg.caution)+'</p><div class="ce-actions"><a href="#corporatePaths">Who owns businesses in this category?</a><a href="#sourceMeasured">See measured geographic evidence</a><a href="#how">Find assistance and ways to act</a></div></div>'+
 '<p class="ce-privacy"><strong>Private by default:</strong> amounts stay in this browser tab only, are not uploaded, and disappear when the page is refreshed. No dollar figure is inferred from your ZIP code.</p>';
 update();
}
function update(){
 if(!root)return;var cfg=TOPICS[topic];if(!cfg||!cfg.parts.length)return;
 var sum=0,alternative=0,entered=0,compared=0,rank=[];
 cfg.parts.forEach(function(p){
  var s=state()[p.id]||{},a=number(s.current),b=number(s.scenario);
  if(a!==null){entered++;sum+=a;alternative+=b===null?a:b;if(b!==null)compared++;rank.push({id:p.id,label:p.name,amount:a,choice:p.choice})}
 });
 var current=root.querySelector("#ceCurrent"),scenario=root.querySelector("#ceScenario"),difference=root.querySelector("#ceDifference"),priority=root.querySelector("#cePriority");
 current.textContent=entered?fmt(sum):"—";scenario.textContent=entered?fmt(alternative):"—";
 var delta=sum-alternative;
 difference.textContent=compared?(delta>=0?fmt(delta*12)+" less":fmt(-delta*12)+" more"):"—";
 difference.classList.toggle("ce-over",compared>0&&delta<0);
 priority.textContent=entered?(rank.sort(function(a,b){return b.amount-a.amount})[0].label+" is your largest entered cost. Compare an actual offer or realistic change before treating any difference as savings."): "Enter your costs to see the largest component and where comparing options could matter.";
 cfg.parts.forEach(function(p){
  var a=number((state()[p.id]||{}).current),bar=root.querySelector('[data-ce-share="'+p.id+'"]');
  if(bar)bar.style.width=entered&&sum>0&&a!==null?(Math.max(0,Math.min(100,100*a/sum))).toFixed(2)+"%":"0%";
 });
}
function input(e){
 var t=e.target;if(!t.matches("input[data-ce-id][data-ce-kind]"))return;
 var cfg=TOPICS[topic],id=t.getAttribute("data-ce-id"),kind=t.getAttribute("data-ce-kind");
 if(!cfg.parts.some(function(p){return p.id===id}))return;
 if(!state()[id])state()[id]={};
 state()[id][kind]=t.value;update();
}
function setTopic(id){if(!TOPICS[id])return;topic=id;render()}
function init(){
 root=document.getElementById("personalCostExplorer");if(!root)return;
 topic=TOPICS[location.hash.slice(1)]?location.hash.slice(1):"housing";
 root.addEventListener("input",input);
 root.addEventListener("click",function(e){
  if(e.target.closest("#ceClear")){values[topic]=Object.create(null);render();}
 });
 setTopic(topic);
}
window.PowerAtlasCostExplorer={setTopic:setTopic};
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init);else init();
})();