/* Power Atlas Take Action — issue-constrained constituent contact handoff.
   No submissions or personal data are retained by this site. */
(()=>{
"use strict";
const $=id=>document.getElementById(id);
const issueData={
housing:{label:"housing affordability",summary:"Access to affordable housing and the public decisions that shape it.",source:"my-life.html#what"},
consumer:{label:"consumer protection",summary:"Hidden fees, misleading marketing and enforceable consumer protections.",source:"consumer-practices.html"},
market:{label:"market concentration",summary:"Competition, market power and effects on consumer choice.",source:"market-power.html"},
work:{label:"workforce automation and customer service",summary:"Workforce changes, service access and public accountability.",source:"service-accountability.html"},
health:{label:"healthcare affordability and access",summary:"The costs and accessibility of healthcare services.",source:"my-life.html#what"},
transport:{label:"transportation costs and oversight",summary:"Toll fees, fare increases and transparent infrastructure spending.",source:"my-life.html#what"},
money:{label:"political money transparency",summary:"Political spending disclosure and accountability.",source:"dark-money.html"},
voting:{label:"voting access and representation",summary:"Voting rules, democratic participation and fair representation.",source:"index.html"}
};
const questions={
position:"State your position clearly. Which bills, votes, or public evidence support it?",
action:"Identify concrete action you have taken, what comes next, and when constituents can verify progress. Cite bill numbers where applicable.",
oversight:"Identify the hearings, reports, or oversight actions addressing this issue, and the next steps or deadlines.",
meeting:"I request a meeting with you or the relevant staff member. Who handles scheduling, and how can I submit an evidence brief?"
};
let zip="",currentIssue="housing",currentQuestion="position",members=[],selected=null,lookupSerial=0,ambiguous=false,selectedChamber=null;
const officeFallback="https://www.congress.gov/members/find-your-member";
const switchboard="tel:+12022243121";
const status=$("lookup-status"),result=$("member-results"),recipients=$("recipient-options");
const isHttps=(url,govOnly=false)=>{
 try{const u=new URL(url);if(u.protocol!=="https:")return null;
 if(govOnly&&!/(^|\.)(house|senate)\.gov$/.test(u.hostname))return null;
 return u.href;}catch{return null}
};
const displayName=m=>m.natural_name||((m.name||"").includes(",")?(m.name.split(",").slice(1).join(",").trim()+" "+m.name.split(",")[0].trim()):m.name)||"Member of Congress";
const memberTitle=m=>(m.chamber==="senate"?"Senator":"Representative")+" "+displayName(m);
const roleLabel=m=>m.chamber==="senate"?"U.S. Senate":"U.S. House";
function make(tag,className,text){const element=document.createElement(tag);if(className)element.className=className;if(text!=null)element.textContent=text;return element;}
function link(text,href){const a=make("a",null,text);a.href=href;a.target="_blank";a.rel="noopener noreferrer";return a;}
function houseLookup(code){return /^\d{5}$/.test(code)?"https://ziplook.house.gov/htbin/findrep_house?ZIP="+code:"https://www.house.gov/representatives/find-your-representative";}
function senateLookup(state){return /^[A-Z]{2}$/.test(state)?"https://www.senate.gov/states/"+state+"/intro.htm":"https://www.senate.gov/senators/contact/";}
function contactFor(m){
 if(isHttps(m.contact,true))return m.contact;
 if(isHttps(m.website,true))return m.website;
 return m.chamber==="senate"?senateLookup(m.state):houseLookup(zip);
}
function buildMessage(){
 const topic=issueData[currentIssue];
 const salutation=selected?("Dear "+(selected.chamber==="senate"?"Senator ":"Representative ")+(selected.last_name||displayName(selected).split(" ").slice(-1)[0])+","):"Dear Member of Congress,";
 const location=zip?"I live in ZIP code "+zip+". ":"";
 const msg="Subject: Constituent accountability request: "+topic.label+"\n\n"+salutation+"\n\n"+location+"I am requesting specific answers on "+topic.label+". "+questions[currentQuestion]+" Please respond in writing with a concrete next step or the relevant public record.";
 const limited=msg.slice(0,500);
 $("message-preview").value=limited;
 $("message-count").textContent=limited.length+" / 500 characters";
 $("brief-preview").value=makeBrief();
 const dest=$("write-member");
 dest.href=selected?contactFor(selected):officeFallback;
 dest.textContent=selected?(selected.contact?"Open official contact form ↗":"Open official member website to contact ↗"):"Find an official contact form ↗";
 const phone=selected&&/^\+?[0-9()\-\s]{10,25}$/.test(selected.phone||"")?selected.phone:"(202) 224-3121";
 $("call-member").href=selected&&/^\+?[0-9()\-\s]{10,25}$/.test(selected.phone||"")?"tel:"+selected.phone.replace(/[^+0-9]/g,""):switchboard;
 $("call-member").textContent=selected&&phone!=="(202) 224-3121"?"Call "+displayName(selected)+"’s office · "+phone:"Call U.S. Capitol switchboard · (202) 224-3121";
}
/* Build a portable, user-controlled issue brief; this includes a research entry point,
   not an invented fact or a claim that the constituent sent anything. */
function makeBrief(){
 const topic=issueData[currentIssue];
 const researchLink=new URL(topic.source,location.href).href;
 const recipient=selected?memberTitle(selected):"The member of Congress I select";
 return "POWER ATLAS | CITIZEN INFLUENCE BRIEF\n"+
  "Issue: "+topic.label+"\n"+
  "Why it matters: "+topic.summary+"\n"+
  "Power Atlas research: "+researchLink+"\n"+
  "Office: "+recipient+"\n"+
  "Accountability request: "+questions[currentQuestion]+"\n"+
  "My follow-up plan: verify the underlying sources; contact the office; request a staff meeting where appropriate; record the reply and check any cited legislation or votes.\n"+
  "This is a starting brief, not evidence that an office received or agreed to a request.";
}
async function copyValue(value,button,label,previewId){
 try{
  await navigator.clipboard.writeText(value);
  button.textContent="Copied ✓";
  setTimeout(()=>button.textContent=label,1600);
 }catch{
  const preview=$(previewId);
  const disclosure=preview.closest("details");if(disclosure)disclosure.open=true;
  preview.focus();preview.select();
  button.textContent="Select text & copy";
 }
}
function setRecipient(m){
 selected=m;recipients.querySelectorAll("button").forEach(b=>b.setAttribute("aria-pressed",String(b.dataset.member===m.bioguide_id)));
 buildMessage();
}
function renderMembers(){
 result.replaceChildren();recipients.replaceChildren();selected=null;
 if(members.length===0){const p=make("p","ta-empty","Member data is not available. Use the official congressional finder above to locate your offices.");result.append(p);recipients.append(make("p",null,"Use the official directory above, then copy a prepared message."));buildMessage();return;}
 const house=members.filter(m=>m.chamber==="house"),multi=ambiguous||house.length>1;
 $("ambiguous-notice").hidden=house.length===0;
 for(const m of members){
  const card=make("article","ta-member");
  card.dataset.chamber=m.chamber;
  card.tabIndex=-1;
  card.append(make("span","ta-member-role",roleLabel(m)+(m.chamber==="house"&&multi?" · possible district":"")));
  card.append(make("h3",null,displayName(m)));
  const sub=make("p","ta-member-meta",m.chamber==="house"?(multi?"One of "+house.length+" House members for this ZIP. Verify your address with House.gov." :"Possible House member for ZIP. Confirm your full address with House.gov."):"Senator for "+(m.state||"your state"));
  card.append(sub);
  card.append(link(m.contact?"Official contact form ↗":m.website?"Official member website ↗":"Official finder ↗",contactFor(m)));
  if(m.chamber==="house")card.append(link("Verify district on House.gov ↗",houseLookup(zip)));
  if(m.phone)card.append(link("Call office ↗","tel:"+String(m.phone).replace(/[^+0-9]/g,"")));
  result.append(card);
  const button=make("button",null,(m.chamber==="senate"?"Sen. ":"Rep. ")+displayName(m));
  button.type="button";button.dataset.member=m.bioguide_id;button.setAttribute("aria-pressed","false");
  button.addEventListener("click",()=>setRecipient(m));recipients.append(button);
 }
 const info=make("p","ta-small","Choose the member whose office you intend to contact. Power Atlas never sends the message for you.");
 recipients.append(info);buildMessage();highlightMemberCards();
}
function normalize(raw){
 if(!raw||typeof raw!=="object"||!["sen","rep"].includes(raw.type))return null;
 const first=String(raw.first_name||"").trim(),last=String(raw.last_name||"").trim(),name=(first+" "+last).trim();
 const id=String(raw.bioguide_id||""),state=String(raw.state||"").toUpperCase();
 if(!name||!/^([A-Z][0-9]{6})$/.test(id)||!(/^[A-Z]{2}$/.test(state)))return null;
 return {bioguide_id:id,name:last+", "+first,natural_name:name,chamber:raw.type==="sen"?"senate":"house",
  state,district:Number.isInteger(raw.district)?raw.district:null,contact:isHttps(raw.contact_form,true),
  website:isHttps(raw.url,true),phone:String(raw.phone||"").slice(0,28),last_name:last};
}
/* Compare independent ZIP data against the House-derived match list.
   Never treat ZIP-only district assignment as proof of address-level representation. */
function normalizeOpenAmerica(raw,chamber,state){
 if(!raw||!/^([A-Z][0-9]{6})$/.test(String(raw.bioguide_id||""))||!raw.name)return null;
 const text=String(raw.name);
 const natural=String(raw.natural_name||"").trim()||(text.includes(",")?(text.split(",").slice(1).join(",").trim()+" "+text.split(",")[0].trim()):text);
 return{bioguide_id:raw.bioguide_id,name:text,natural_name:natural,chamber,state,
   district:null,contact:null,website:null,phone:null,last_name:text.includes(",")?text.split(",")[0].trim():natural.split(" ").slice(-1)[0]};
}
async function enrichMissingOffices(serial){
 const needed=members.filter(m=>!m.contact&&!m.website).slice(0,8);
 if(!needed.length)return;
 await Promise.all(needed.map(async m=>{
  try{
   const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),6500);
   let res;try{res=await fetch("https://openamerica.io/legislator/"+m.bioguide_id+"/?format=json",{signal:controller.signal,mode:"cors",credentials:"omit"});}finally{clearTimeout(timer)}
   if(!res.ok||serial!==lookupSerial)return;
   const data=await res.json();
   if(data.current_member===true){m.website=isHttps(data.official_website,true);}
  }catch{/* Government finder remains available for each candidate. */}
 }));
 if(serial!==lookupSerial)return;
 const previous=selected?.bioguide_id;
 renderMembers();
 const saved=members.find(m=>m.bioguide_id===previous);if(saved)setRecipient(saved);
}
async function locate(zipCode){
 const serial=++lookupSerial;zip=zipCode;status.textContent="Cross-checking congressional offices for ZIP "+zip+"…";
 result.replaceChildren();$("ambiguous-notice").hidden=true;
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),9500);
 let one,two;
 try{
  const requests=await Promise.allSettled([
   fetch("https://repscontact.com/api/reps?zip="+encodeURIComponent(zip),{signal:controller.signal,mode:"cors",credentials:"omit",cache:"no-store"}).then(r=>r.ok?r.json():Promise.reject(Error("RepsContact error"))),
   fetch("https://openamerica.io/api/zip-lookup/"+encodeURIComponent(zip)+"/",{signal:controller.signal,mode:"cors",credentials:"omit",cache:"no-store"}).then(r=>r.ok?r.json():Promise.reject(Error("Open America error")))
  ]);
  if(serial!==lookupSerial)return;
  one=requests[0].status==="fulfilled"?requests[0].value:null;
  two=requests[1].status==="fulfilled"?requests[1].value:null;
  const validOne=one&&one.zip===zip&&Array.isArray(one.representatives);
  const validTwo=two&&two.ok===true&&two.zip===zip&&/^[A-Z]{2}$/.test(two.state||"")&&Array.isArray(two.representatives)&&Array.isArray(two.senators);
  if(!validOne&&!validTwo)throw Error("Both member sources unavailable");
  const fromOne=validOne?one.representatives.map(normalize).filter(Boolean):[];
  const fromTwo=validTwo?[
   ...two.representatives.map(m=>normalizeOpenAmerica(m,"house",two.state)),
   ...two.senators.map(m=>normalizeOpenAmerica(m,"senate",two.state))
  ].filter(Boolean):[];
  const byId=new Map(fromTwo.map(m=>[m.bioguide_id,m]));
  for(const m of fromOne){
   const old=byId.get(m.bioguide_id);
   if(old){byId.set(m.bioguide_id,{...old,...m,website:m.website||old.website,contact:m.contact||old.contact,phone:m.phone||old.phone});}
   else byId.set(m.bioguide_id,m);
  }
  members=[...byId.values()];
  if(!members.length||members.length>25)throw Error("No trustworthy current members");
  members.sort((a,b)=>a.chamber===b.chamber?a.natural_name.localeCompare(b.natural_name):a.chamber==="senate"?-1:1);
  const house=members.filter(m=>m.chamber==="house");
  const houseOne=new Set(fromOne.filter(m=>m.chamber==="house").map(m=>m.bioguide_id));
  const houseTwo=new Set(fromTwo.filter(m=>m.chamber==="house").map(m=>m.bioguide_id));
  const conflict=!!(validOne&&validTwo&&(houseOne.size!==houseTwo.size||[...houseOne].some(id=>!houseTwo.has(id))));
  ambiguous=one?.ambiguous===true||house.length>1||conflict;
  status.textContent=(ambiguous?"ZIP "+zip+" has multiple possible House districts or inconsistent lookup coverage. ":"Showing "+house.length+" possible House member for ZIP "+zip+". ")+
    "Confirm your House district using the official address finder. "+(conflict?"Independent sources disagreed; all distinct candidates are displayed.":"");
  renderMembers();
  enrichMissingOffices(serial);
 }catch(e){
  if(serial!==lookupSerial)return;
  members=[];ambiguous=false;renderMembers();
  status.textContent="Live lookup could not verify members. Use the official House and Congress.gov tools; Power Atlas will not guess.";
  const fallback=make("div","ta-fallback");
  fallback.append(link("Official House ZIP lookup (ZIP prefilled) ↗",houseLookup(zip)));
  fallback.append(link("Find my members on Congress.gov ↗",officeFallback));
  result.append(fallback);
 }finally{clearTimeout(timer)}
}
/* Illustration chamber cards are actual routes into the ZIP member finder.
   No ZIP is inferred or sent until the visitor enters one and activates a control. */
function highlightMemberCards(){
 const cards=[...result.querySelectorAll(".ta-member")];
 cards.forEach(card=>card.classList.toggle("ta-member--selected-chamber",card.dataset.chamber===selectedChamber));
 return cards.filter(card=>card.dataset.chamber===selectedChamber);
}
function focusChosenChamber(chamber){
 if(selectedChamber!==chamber)return;
 const matches=highlightMemberCards();
 const reduced=window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;
 const behavior=reduced?"auto":"smooth";
 if(matches.length){
  matches[0].scrollIntoView({behavior,block:"center"});
  matches[0].focus({preventScroll:true});
 }else{
  document.querySelector(".ta-official-links")?.scrollIntoView({behavior,block:"center"});
 }
}
document.querySelectorAll(".ta-chamber-link").forEach(button=>button.addEventListener("click",()=>{
 const chamber=button.dataset.chamber;
 if(chamber!=="house"&&chamber!=="senate")return;
 selectedChamber=chamber;
 document.querySelectorAll(".ta-chamber-link").forEach(b=>b.setAttribute("aria-pressed",String(b===button)));
 const input=$("zip"),code=input.value.trim();
 const reduced=window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;
 if(!/^\d{5}$/.test(code)){
  status.textContent=chamber==="house"?"Enter your five-digit ZIP to find your U.S. House representative.":"Enter your five-digit ZIP to find your U.S. senators.";
  $("find").scrollIntoView({behavior:reduced?"auto":"smooth",block:"start"});
  input.focus({preventScroll:true});
  return;
 }
 if(zip===code&&members.some(m=>m.chamber===chamber)){focusChosenChamber(chamber);return;}
 $("find").scrollIntoView({behavior:reduced?"auto":"smooth",block:"start"});
 locate(code).then(()=>focusChosenChamber(chamber));
}));
$("lookup-form").addEventListener("submit",e=>{
 e.preventDefault();const input=$("zip");const code=input.value.trim();
 if(!/^\d{5}$/.test(code)){status.textContent="Enter exactly five digits for a U.S. ZIP code.";input.setAttribute("aria-invalid","true");input.focus();return;}
 input.removeAttribute("aria-invalid");locate(code).then(()=>{if(selectedChamber)focusChosenChamber(selectedChamber);});
});
$("zip").addEventListener("input",()=>{$("zip").value=$("zip").value.replace(/\D/g,"").slice(0,5);});
document.querySelectorAll("#issue-options button").forEach(button=>button.addEventListener("click",()=>{
 currentIssue=button.dataset.issue;
 document.querySelectorAll("#issue-options button").forEach(b=>b.setAttribute("aria-pressed",String(b===button)));
 $("issue-description").textContent=issueData[currentIssue].summary;
 $("issue-link").href=issueData[currentIssue].source;
 buildMessage();
}));
document.querySelectorAll("#question-options button").forEach(button=>button.addEventListener("click",()=>{
 currentQuestion=button.dataset.question;
 document.querySelectorAll("#question-options button").forEach(b=>b.setAttribute("aria-pressed",String(b===button)));
 buildMessage();
}));
$("copy-message").addEventListener("click",()=>copyValue($("message-preview").value,$("copy-message"),"Copy message","message-preview"));
$("copy-brief").addEventListener("click",()=>copyValue(makeBrief(),$("copy-brief"),"Copy my issue brief","brief-preview"));
const incoming=new URLSearchParams(location.search).get("zip");if(incoming&&/^\d{5}$/.test(incoming))$("zip").value=incoming;
buildMessage();
})();
