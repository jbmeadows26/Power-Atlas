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
let zip="",currentIssue="housing",currentQuestion="position",members=[],selected=null,lookupSerial=0,ambiguous=false;
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
 const msg="Subject: Question about "+topic.label+"\n\n"+salutation+"\n\n"+location+"I am contacting your office about "+topic.label+". "+questions[currentQuestion]+"\n\nThank you for your time.";
 const limited=msg.slice(0,500);
 $("message-preview").value=limited;
 $("message-count").textContent=limited.length+" / 500 characters";
 const dest=$("write-member");
 dest.href=selected?contactFor(selected):officeFallback;
 dest.textContent=selected?(selected.contact?"Open official contact form ↗":"Open official member website to contact ↗"):"Find an official contact form ↗";
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
 const house=members.filter(m=>m.chamber==="house"),multi=ambiguous||house.length>1;
 $("ambiguous-notice").hidden=!multi;
 for(const m of members){
  const card=make("article","ta-member");
  card.append(make("span","ta-member-role",roleLabel(m)+(m.chamber==="house"&&multi?" · possible district":"")));
  card.append(make("h3",null,displayName(m)));
  const sub=make("p","ta-member-meta",m.chamber==="house"?(multi?"One of "+house.length+" House members for this ZIP. Verify your address with House.gov.":"Matching House district from public directory."):"Senator for "+(m.state||"your state"));
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
 recipients.append(info);buildMessage();
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
async function locate(zipCode){
 const serial=++lookupSerial;zip=zipCode;status.textContent="Finding current congressional offices for ZIP "+zip+"…";
 result.replaceChildren();$("ambiguous-notice").hidden=true;
 const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),9000);
 try{
  let response;try{response=await fetch("https://repscontact.com/api/reps?zip="+encodeURIComponent(zip),{signal:controller.signal,mode:"cors",credentials:"omit",cache:"no-store"});}
  finally{clearTimeout(timeout)}
  if(!response.ok)throw Error("Lookup unavailable");
  const data=await response.json();
  if(serial!==lookupSerial)return;
  if(data.zip!==zip||!Array.isArray(data.representatives))throw Error("Unexpected directory response");
  members=data.representatives.map(normalize).filter(Boolean);
  if(!members.length||members.length>15)throw Error("No valid members");
  members=[...new Map(members.map(m=>[m.bioguide_id,m])).values()];
  members.sort((a,b)=>a.chamber===b.chamber?a.natural_name.localeCompare(b.natural_name):a.chamber==="senate"?-1:1);
  const house=members.filter(m=>m.chamber==="house");
  ambiguous=data.ambiguous===true||house.length>1;
  status.textContent=members.length+" current member"+(members.length===1?"":"s")+" found via independent directory (RepsContact). "+(ambiguous?"Your ZIP spans House districts; confirm the correct district through the official finder.":"Please verify with Congress.gov before contacting.");
  renderMembers();
 }catch(e){
  if(serial!==lookupSerial)return;
  members=[];ambiguous=false;renderMembers();
  status.textContent="Live member lookup is unavailable. Use official Congress.gov or House.gov directories; we do not guess member names.";
  const fallback=make("div","ta-fallback");
  fallback.append(link("Find my House member on House.gov ↗","https://www.house.gov/representatives/find-your-representative"));
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
const incoming=new URLSearchParams(location.search).get("zip");if(incoming&&/^\d{5}$/.test(incoming))$("zip").value=incoming;
buildMessage();
})();
