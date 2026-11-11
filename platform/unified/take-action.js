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
position:"What is your position on this issue, and what public evidence or legislation informs it?",
action:"What steps has your office taken on this issue, and where can I verify that record?",
oversight:"What oversight or public review is underway, and how can constituents follow its progress?"
};
let zip="",currentIssue="housing",currentQuestion="position",members=[],selected=null,lookupSerial=0;
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
 const msg="Subject: Constituent question about "+topic.label+"\n\n"+salutation+"\n\n"+location+"I am contacting your office about "+topic.label+". "+questions[currentQuestion]+"\n\nThank you for your time.";
 const limited=msg.slice(0,500);
 $("message-preview").value=limited;
 $("message-count").textContent=limited.length+" / 500 characters";
 const dest=$("write-member");
 dest.href=selected?contactFor(selected):officeFallback;
 dest.textContent=selected?("Open "+(selected.chamber==="senate"?"senator":"representative")+"’s official contact page ↗"):"Find an official contact form ↗";
 const phone=selected&&/^\+?[0-9()\-\s]{10,25}$/.test(selected.phone||"")?selected.phone:"(202) 224-3121";
 $("call-member").href=selected&&/^\+?[0-9()\-\s]{10,25}$/.test(selected.phone||"")?"tel:"+selected.phone.replace(/[^+0-9]/g,""):switchboard;
 $("call-member").textContent=selected&&phone!=="(202) 224-3121"?"Call "+displayName(selected)+"’s office · "+phone:"Call U.S. Capitol switchboard · (202) 224-3121";
}
function setRecipient(m){
 selected=m;recipients.querySelectorAll("button").forEach(b=>b.setAttribute("aria-pressed",String(b.dataset.member===m.bioguide_id)));
 buildMessage();
}
function renderMembers(){
 result.replaceChildren();recipients.replaceChildren();selected=null;
 if(members.length===0){const p=make("p","ta-empty","Member data is not available. Use the official congressional finder above to locate your offices.");result.append(p);recipients.append(make("p",null,"Use the official directory above, then copy a prepared message."));buildMessage();return;}
 const house=members.filter(m=>m.chamber==="house"),multi=house.length>1;
 $("ambiguous-notice").hidden=!multi;
 for(const m of members){
  const card=make("article","ta-member");
  card.append(make("span","ta-member-role",roleLabel(m)+(m.chamber==="house"&&multi?" · possible district":"")));
  card.append(make("h3",null,displayName(m)));
  const sub=make("p","ta-member-meta",m.chamber==="house"?(multi?"One of "+house.length+" House members for this ZIP. Verify your address with House.gov.":"Matching House district from public directory."):"Senator for "+(m.state||"your state"));
  card.append(sub);
  card.append(link("Official contact ↗",contactFor(m)));
  if(m.chamber==="house")card.append(link("Verify district on House.gov ↗",houseLookup(zip)));
  if(m.phone)card.append(link("Call office ↗","tel:"+String(m.phone).replace(/[^+0-9]/g,"")));
  result.append(card);
  const button=make("button",null,(m.chamber==="senate"?"Sen. ":"Rep. ")+displayName(m));
  button.type="button";button.dataset.member=m.bioguide_id;button.setAttribute("aria-pressed","false");
  button.addEventListener("click",()=>setRecipient(m));recipients.append(button);
 }
 const info=make("p","ta-small","Choose the member whose office you intend to contact. Power Atlas never sends the message for you.");
 recipients.append(info);buildMessage();
}
function normalize(raw,chamber,state){
 if(!raw||typeof raw!=="object"||!/^[A-Z][0-9]{6}$/.test(raw.bioguide_id||"")||!raw.name)return null;
 return{bioguide_id:raw.bioguide_id,name:String(raw.name),natural_name:String(raw.natural_name||"").slice(0,100),chamber,state,contact:null,website:null,phone:null,last_name:null};
}
function getRosterMember(p){
 if(!p||!Array.isArray(p.terms))return null;
 const now=new Date().toISOString().slice(0,10);
 return p.terms.find(t=>t&&t.start<=now&&t.end>now&&/^(rep|sen)$/.test(t.type));
}
async function enrichContacts(serial){
 // Legislator records are an optional public convenience source; official directories remain definitive.
 try{
  const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),7500);
  let response;
  try{response=await fetch("https://unitedstates.github.io/congress-legislators/legislators-current.json",{signal:controller.signal})}finally{clearTimeout(timeout)}
  if(!response.ok)throw Error("Roster temporarily unavailable");
  const people=await response.json();
  if(serial!==lookupSerial||!Array.isArray(people))return;
  const byId=new Map(people.map(p=>[p.id?.bioguide,p]));
  for(const m of members){
   const p=byId.get(m.bioguide_id),term=getRosterMember(p);
   if(!term||((m.chamber==="house"&&term.type!=="rep")||(m.chamber==="senate"&&term.type!=="sen")))continue;
   m.contact=isHttps(term.contact_form,true);
   m.website=isHttps(term.url,true);
   m.phone=term.phone||null;
   m.last_name=p.name?.last||null;
  }
  renderMembers();
 }catch{/* Keep House ZIP and Senate state official lookup links intact. */}
}
async function locate(zipCode){
 const serial=++lookupSerial;zip=zipCode;status.textContent="Looking up current congressional offices for ZIP "+zip+"…";result.replaceChildren();$("ambiguous-notice").hidden=true;
 const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),9000);
 try{
  let response;try{response=await fetch("https://openamerica.io/api/zip-lookup/"+encodeURIComponent(zip)+"/",{signal:controller.signal,cache:"no-store"})}finally{clearTimeout(timeout)}
  if(!response.ok)throw Error("Lookup unavailable");
  const data=await response.json();
  if(serial!==lookupSerial)return;
  if(data.ok!==true||data.zip!==zip||!Array.isArray(data.representatives)||!Array.isArray(data.senators))throw Error("Incomplete lookup");
  const state=String(data.state||"").toUpperCase();
  const house=(data.representatives||[]).map(p=>normalize(p,"house",state)).filter(Boolean);
  const senate=(data.senators||[]).map(p=>normalize(p,"senate",state)).filter(Boolean);
  members=[...house,...senate].filter((m,i,a)=>a.findIndex(x=>x.bioguide_id===m.bioguide_id)===i);
  if(!members.length)throw Error("No current members returned");
  status.textContent=house.length>1?"We found "+house.length+" possible House districts and "+senate.length+" senators. Confirm your House district before sending.":"We found "+house.length+" House representative and "+senate.length+" senators. Check official links before sending.";
  renderMembers();
  enrichContacts(serial);
 }catch(e){
  if(serial!==lookupSerial)return;
  clearTimeout(timeout);members=[];renderMembers();
  status.textContent="Live lookup could not confirm member identities. Use these government sources instead—no guessed results are shown.";
  const fallback=make("div","ta-fallback");
  fallback.append(link("Find my House member (ZIP prefilled) ↗",houseLookup(zip)));
  fallback.append(link("Find my members on Congress.gov ↗",officeFallback));
  result.append(fallback);
 }
}
$("lookup-form").addEventListener("submit",e=>{
 e.preventDefault();const input=$("zip");const code=input.value.trim();
 if(!/^\d{5}$/.test(code)){status.textContent="Enter exactly five digits for a U.S. ZIP code.";input.setAttribute("aria-invalid","true");input.focus();return;}
 input.removeAttribute("aria-invalid");locate(code);
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
$("copy-message").addEventListener("click",async()=>{
 const text=$("message-preview").value;
 try{await navigator.clipboard.writeText(text);$("copy-message").textContent="Copied ✓";setTimeout(()=>$("copy-message").textContent="Copy message",1600);}
 catch{const t=$("message-preview");t.focus();t.select();$("copy-message").textContent="Select text & copy";}
});
buildMessage();
})();
