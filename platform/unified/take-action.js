/* Power Atlas / Civic Action. No constituent messages or personal information are sent to Power Atlas.
   ZIP-only lookups use a public service with its own published rate limit and official-source fallback. */
(()=>{
"use strict";
const $=id=>document.getElementById(id);
const ZIP=/^\d{5}$/;
const bioguide=/^[A-Z]\d{6}$/;
const issues=[
 {id:"housing",icon:"⌂",title:"Housing",detail:"Rent, ownership, supply",page:"my-life.html#what",question:"What federal actions are you considering on housing affordability, transparency, and access?"},
 {id:"transport",icon:"▰",title:"Transportation",detail:"Tolls, fares, services",page:"my-life.html#what",question:"How are you evaluating transportation funding, toll burdens, and service quality for constituents?"},
 {id:"groceries",icon:"◉",title:"Groceries",detail:"Prices and competition",page:"my-life.html#benchmarkStory",question:"What evidence is informing your approach to grocery affordability and retail competition?"},
 {id:"health",icon:"✳",title:"Health care",detail:"Access and cost",page:"my-life.html#what",question:"What steps are you considering to improve health care affordability and access?"},
 {id:"fees",icon:"▤",title:"Consumer fees",detail:"Hidden costs and fine print",page:"consumer-practices.html",question:"What consumer protections do you support regarding unclear fees and misleading promotions?"},
 {id:"market",icon:"◈",title:"Market power",detail:"Competition and control",page:"market-power.html",question:"What oversight do you think is appropriate when market concentration harms competition?"},
 {id:"money",icon:"◎",title:"Political money",detail:"Donor transparency",page:"dark-money.html",question:"What transparency safeguards do you support for election spending and political donations?"},
 {id:"workforce",icon:"↗",title:"Automation",detail:"Work and human service",page:"service-accountability.html",question:"How are you assessing the employment and customer-access effects of corporate automation?"},
 {id:"economy",icon:"◌",title:"Economic risk",detail:"Household resilience",page:"economic-fragility.html",question:"What public evidence and plans guide your work on protecting households from economic shocks?"},
 {id:"claims",icon:"≡",title:"Class actions",detail:"Consumer legal rights",page:"class-actions.html",question:"What changes would improve clear, accessible information about consumer legal rights and claims?"}
];
const official={house:"https://www.house.gov/representatives/find-your-representative",senate:"https://www.senate.gov/senators/contact/",congress:"https://www.congress.gov/members/find-your-member"};
let zip="",topic=null,member=null,lookupAbort=null,sequence=0,latestMembers=[];
function safeOfficialSite(url,chamber){
 try{
  const u=new URL(url);
  if(u.protocol!=="https:")return null;
  const host=u.hostname.toLowerCase();
  if(chamber==="senate" && (host==="senate.gov"||host.endsWith(".senate.gov")))return u.href;
  if(chamber==="house" && (host==="house.gov"||host.endsWith(".house.gov")))return u.href;
  return null;
 }catch{return null;}
}
function niceName(entry){
 const n=String(entry.natural_name||entry.name||"Member of Congress").trim().slice(0,90);
 if(n.includes(",")&&!entry.natural_name){const split=n.split(",");return (split.slice(1).join(",").trim()+" "+split[0].trim()).trim();}
 return n;
}
function el(tag,cls,text){
 const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=text;return n;
}
function link(label,url){
 const a=el("a","",label);a.href=url;a.target="_blank";a.rel="noopener noreferrer";return a;
}
function renderIssues(){
 const grid=$("issues");
 issues.forEach(i=>{
  const btn=el("button","issue");btn.type="button";btn.dataset.issue=i.id;btn.setAttribute("aria-pressed","false");
  btn.append(el("span","symbol",i.icon),el("b","",i.title),el("small","",i.detail));
  btn.addEventListener("click",()=>selectIssue(i.id));
  grid.append(btn);
 });
}
function selectIssue(id){
 topic=issues.find(i=>i.id===id)||null;
 $("issues").querySelectorAll("button").forEach(b=>b.setAttribute("aria-pressed",String(b.dataset.issue===id)));
 $("selectedIssue").replaceChildren();
 if(topic){
  const header=el("strong","",topic.title+" · question to ask");
  const p=el("p","",topic.question);
  const a=link("Explore the evidence ↗",topic.page);
  a.target="_self";
  $("selectedIssue").append(header,p,a);
 }else $("selectedIssue").textContent="Select an issue above.";
 updatePreview();
}
function formatMessage(){
 if(!topic)return "";
 const intro=member?"Hello "+(member.chamber==="senate"?"Senator ":"Representative ")+member.name+",":"Hello,";
 const area=zip?" I live in ZIP "+zip+".":"";
 const personal=$("note").value.trim().replace(/\s+/g," ");
 const ending=" I would appreciate your position, relevant legislation, and any action your office is considering.";
 return intro+area+" I am writing about "+topic.title.toLowerCase()+". "+topic.question+ending+(personal?" My experience: "+personal:"");
}
function blockedNote(note){
 return /https?:\/\/|www\.|\b[\w.%+-]+@[\w.-]+\.[A-Za-z]{2,}\b|\b\+?1?[\s.(\-]*\d{3}[\s.)-]*\d{3}[\s.-]*\d{4}\b|\b\d{3}-\d{2}-\d{4}\b/i.test(note);
}
function updatePreview(){
 const note=$("note").value;
 $("remaining").textContent=note.length+" / 280";
 const blocked=blockedNote(note);
 $("previewText").textContent=blocked?"Please remove links, phone numbers, email addresses, and other identifying details from the note.":topic?formatMessage():"Select an issue to build a short, factual inquiry to your member of Congress.";
 $("copyMessage").disabled=!topic||blocked;
 $("messageStatus").textContent=blocked?"Your optional note contains contact information or a link. Remove it to enable copying.":topic?"Copy this message, then open your selected member's official website and choose Contact. You make the final submission.":"Choose a topic. Then copy your inquiry and paste it into the official member's contact form.";
 $("contactMember").href=member?.official|| (member?.chamber==="senate"?official.senate:member?.chamber==="house"?official.house:official.congress);
 $("contactMember").textContent=member&&member.official?"Open "+member.name+"'s official office ↗":member?"Find "+member.name+"'s official contact ↗":"Find official contact form ↗";
}
function selectMember(item,btn){
 member=item;
 document.querySelectorAll(".member-links button").forEach(b=>b.setAttribute("aria-pressed",String(b===btn)));
 updatePreview();
 $("messageStatus").textContent="Selected "+item.name+". Copy your message and send it through the office's own contact form. Power Atlas does not send it.";
}
async function fetchJSON(url,signal){
 const response=await fetch(url,{signal,credentials:"omit",headers:{"Accept":"application/json"}});
 if(!response.ok)throw new Error("Lookup not available ("+response.status+")");
 return response.json();
}
async function enrich(item,seq,signal){
 if(!bioguide.test(item.bioguide_id||""))return;
 try{
  const data=await fetchJSON("https://openamerica.io/legislator/"+encodeURIComponent(item.bioguide_id)+"/?format=json",signal);
  if(seq!==sequence||data.bioguide_id!==item.bioguide_id||data.current_member!==true)return;
  const officialSite=safeOfficialSite(data.official_website,item.chamber);
  if(officialSite){
   item.official=officialSite;
   if(member===item)updatePreview();
   const actions=item.card?.querySelector(".member-links");
   if(actions && !actions.querySelector(".official-member")){
    const a=link("Official office ↗",officialSite);a.className="official-member";actions.append(a);
   }
  }
 }catch{/* Official congressional finders remain visible as a reliable fallback. */}
}
function drawMember(entry,chamber,ambiguous,seq,signal){
 const item={name:niceName(entry),chamber,bioguide_id:String(entry.bioguide_id||""),official:null};
 const card=el("article","member-card"+(ambiguous?" warning":""));
 card.append(el("span","meta",chamber==="senate"?"U.S. Senator":"U.S. Representative"+(ambiguous?" · POSSIBLE MATCH":"")));
 card.append(el("h3","",item.name));
 const party=String(entry.party||"");if(["Democratic","Republican","Independent"].includes(party))card.append(el("span","meta",party));
 card.append(el("p","member-caveat",ambiguous?"This ZIP crosses House districts. Confirm your full address on House.gov before contacting.":"Use the official office's website or contact form to send a message."));
 const actions=el("div","member-links");
 const button=el("button","", "Choose office");button.type="button";button.setAttribute("aria-pressed","false");button.addEventListener("click",()=>selectMember(item,button));actions.append(button);
 actions.append(link(chamber==="senate"?"Senate contacts ↗":"Verify on House.gov ↗",chamber==="senate"?official.senate:official.house));
 card.append(actions);
 item.card=card;
 latestMembers.push(item);
 $("memberGrid").append(card);
 enrich(item,seq,signal);
}
function showFallback(message,state=""){
 $("memberGrid").replaceChildren();
 member=null;latestMembers=[];updatePreview();
 $("memberStatus").textContent=message;
 if(state)$("memberStatus").textContent+=" Your state: "+state+".";
}
async function findMembers(zipCode){
 const seq=++sequence;
 if(lookupAbort)lookupAbort.abort();
 lookupAbort=new AbortController();
 const controller=lookupAbort,signal=controller.signal;
 zip=zipCode; member=null;latestMembers=[];
 $("memberGrid").replaceChildren();
 $("memberStatus").textContent="Finding congressional offices for ZIP "+zipCode+"…";
 $("findButton").disabled=true;
 try{
  const data=await fetchJSON("https://openamerica.io/api/zip-lookup/"+encodeURIComponent(zipCode)+"/",signal);
  if(seq!==sequence)return;
  if(data.ok!==true||data.zip!==zipCode||!Array.isArray(data.senators)||!Array.isArray(data.representatives))throw new Error("Unexpected lookup response");
  const senators=data.senators.filter(x=>x&&bioguide.test(x.bioguide_id||"")).slice(0,2);
  const representatives=data.representatives.filter(x=>x&&bioguide.test(x.bioguide_id||"")).slice(0,10);
  if(!senators.length&&!representatives.length)throw new Error("No current members returned");
  $("memberStatus").textContent="ZIP "+zipCode+" · "+(data.state||"U.S.")+" · "+senators.length+" senator"+(senators.length===1?"":"s")+" · "+representatives.length+" House candidate"+(representatives.length===1?"":"s")+" (verify district)";
  const ambiguous=representatives.length>1;
  senators.forEach(x=>drawMember(x,"senate",false,seq,signal));
  representatives.forEach(x=>drawMember(x,"house",ambiguous,seq,signal));
  updatePreview();
 }catch(e){
  if(seq!==sequence||signal.aborted)return;
  showFallback("We couldn't verify your members automatically. Use the official House ZIP finder and Congress.gov address finder below; neither requires you to trust a guessed district.");
 }finally{
  if(seq===sequence)$("findButton").disabled=false;
 }
}
$("zipForm").addEventListener("submit",e=>{
 e.preventDefault();
 const entered=$("zip").value.trim();
 if(!ZIP.test(entered)){$("memberStatus").textContent="Enter a valid five-digit U.S. ZIP code.";return;}
 findMembers(entered);
});
$("note").addEventListener("input",updatePreview);
$("copyMessage").addEventListener("click",async()=>{
 if(!topic||blockedNote($("note").value))return;
 const message=formatMessage();
 try{
  if(navigator.clipboard&&window.isSecureContext)await navigator.clipboard.writeText(message);
  else {
   const temp=el("textarea");temp.value=message;temp.setAttribute("readonly","");temp.style.position="fixed";temp.style.opacity="0";document.body.append(temp);temp.select();
   const ok=document.execCommand("copy");temp.remove();if(!ok)throw new Error("Copy blocked");
  }
  $("messageStatus").textContent="Copied. Open the official office and paste your message into its contact form. Nothing was sent by Power Atlas.";
 }catch{$("messageStatus").textContent="Copy was blocked by the browser. Select and copy the text in the message preview manually.";}
});
renderIssues();
const params=new URLSearchParams(location.search);
const preselected=params.get("issue");if(issues.some(i=>i.id===preselected))selectIssue(preselected);
const presetZip=params.get("zip");
if(presetZip&&ZIP.test(presetZip)){$("zip").value=presetZip;findMembers(presetZip);}
else updatePreview();
})();
