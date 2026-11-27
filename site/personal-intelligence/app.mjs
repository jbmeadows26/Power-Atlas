import {paths,sourcePath,analyze,publicContext,safeLink,money} from "./engine.mjs";
const $=id=>document.getElementById(id), feed={}, errors={}; let refreshing=false, config=null, session=null;
const fields=["county","household","gross","net","expenses","lines","drives","employed"];
function profile(){let p={};for(const id of fields){const x=$(id).value;if(x==="")continue;p[id]=["gross","net","expenses","lines"].includes(id)?Number(x):["drives","employed"].includes(id)?x==="yes":x;}return p;}
function restore(p){for(const id of fields){const x=p?.[id];$(id).value=x===true?"yes":x===false?"no":x??"";}render();}
let category="All",filter="Priority";
const actual=n=>typeof n==="number"&&Number.isFinite(n)&&n>=0;
const show=(id,value)=>{$(id).textContent=value;};
function node(tag,cls,value){const el=document.createElement(tag);el.className=cls;if(value!==undefined)el.textContent=value;return el;}
function card(x){
 const article=node("article",""),el=node("details","card");el.dataset.key=x.key||"profile";
 const summary=node("summary",""),symbol=node("span","topic-icon",({affordability:"⌂",telecom:"◉",shortage:"↗",finance:"▥",warning:"!",profile:"$"})[x.key]||"✓");
 symbol.setAttribute("aria-hidden","true");const body=node("div","");body.append(node("small","label",x.status),node("h3","",x.title),node("strong","value",x.value));summary.append(symbol,body,node("span","chevron","›"));el.append(summary);
 const detail=node("div","detail");detail.append(node("p","",x.detail),node("small","",x.date?"Observation: "+x.date:"Based on your entered data"));
 const u=safeLink(x.source);if(u){const a=node("a","","Publisher source");a.href=u;a.rel="noopener noreferrer";detail.append(document.createElement("br"),a);}
 if(paths[x.key]){const a=node("a","","Platform record");a.href=sourcePath(x.key);a.rel="noopener noreferrer";detail.append(a);}
 el.append(detail);article.append(el);return article;
}
function empty(id,message,profileLink=false){const el=node("div","empty",message);if(profileLink){const a=node("a","","Complete your profile ›");a.href="#profile";el.append(document.createElement("br"),a);}$(id).replaceChildren(el);}
function route(){const requested=location.hash.slice(1);const current=["home","decisions","scenarios","profile","sources"].includes(requested)?requested:"home";for(const section of document.querySelectorAll("[data-screen]"))section.hidden=section.dataset.screen!==current;for(const a of document.querySelectorAll("nav a")){if(a.getAttribute("href")==="#"+current)a.setAttribute("aria-current","page");else a.removeAttribute("aria-current");}window.scrollTo(0,0);}
function scenario(){const p=profile(),n=p.net,e=p.expenses,alt=$("alternative").value===""?null:Number($("alternative").value);
 show("scenario-income",actual(n)?money(n):"—");show("scenario-expenses",actual(e)?money(e):"—");const base=actual(n)&&actual(e),valid=base&&actual(alt);
 show("scenario-current",base?money(n-e):"—");show("scenario-new",valid?money(n-alt):"—");show("scenario-delta",valid?money(e-alt):"—");show("scenario-year",valid?money((e-alt)*12):"—");
 show("scenario-note",valid?"Conditional calculation using your entered amounts. Annualized assumes the same monthly difference for 12 months; no quote or savings has been independently verified.":"Awaiting actual inputs. A comparison is conditional, not a verified savings claim.");
}
function render(){
 const p=profile(),ctx=publicContext(feed),decisions=analyze(feed,p),hasCash=actual(p.net)&&actual(p.expenses),pct=hasCash&&p.net>0?(p.net-p.expenses)/p.net*100:null;
 show("income-val",actual(p.net)?money(p.net):"—");show("expense-val",actual(p.expenses)?money(p.expenses):"—");show("cash-margin",pct===null?"—":Math.round(pct)+"%");
 const scale=Math.max(actual(p.net)?p.net:0,actual(p.expenses)?p.expenses:0,1);$("income-meter").value=actual(p.net)?100*p.net/scale:0;$("expense-meter").value=actual(p.expenses)?100*p.expenses/scale:0;
 const completeness=Math.round(Object.keys(p).length/fields.length*100);show("complete-val",completeness+"%");$("complete-meter").value=completeness;
 show("picture-note",hasCash?"Cash margin uses your entered income and expenses; not a credit or risk score.": "Add your actual income and expenses to calculate cash margin. No financial score has been inferred.");
 const elevated=ctx.find(x=>x.key==="warning");show("risks-val",elevated?elevated.value:"—");show("decisions-val",Object.keys(p).length?String(decisions.length):"—");show("updates-val",Object.keys(feed).length?String(ctx.length):"—");
 $("context").replaceChildren(...ctx.map(card));if(!ctx.length)empty("context","No source-dated records available.");
 $("decisions-list").replaceChildren(...decisions.map(card));if(!decisions.length)empty("decisions-list","No supported personal finding yet. Add actual information or wait for a matching feed.",true);
 const keys={Finances:["profile","finance"],Household:["affordability","profile"],Shopping:["telecom"],Career:["finance"],Global:["shortage","warning"]};
 const matches=x=>category==="All"||keys[category]?.includes(x.key);
 let rows=[],message="";
 if(filter==="Priority"){rows=decisions.filter(matches);if(!rows.length){rows=ctx.filter(matches).slice(0,4);message="No personalized finding yet. These are public developments, not personal recommendations.";}}
 else if(filter==="Updates")rows=ctx.filter(matches);
 else if(filter==="Risks"){rows=decisions.filter(x=>x.key==="shortage"||(x.key==="profile"&&hasCash&&p.expenses>p.net)).filter(matches);if(!rows.length)message="No supported personal risk finding for this selection. This is not an assurance that no risks exist.";}
 else message="No verified personal savings or opportunity amount is supported by the current data. Compare your actual quotes in Scenarios.";
 $("home-feed").replaceChildren();if(message){const item=node("div","empty",message);if(filter==="Priority"){const a=node("a","","Add your circumstances ›");a.href="#profile";item.append(document.createElement("br"),a);}if(filter==="Opportunities"){const a=node("a","","Compare actual costs ›");a.href="#scenarios";item.append(document.createElement("br"),a);}$("home-feed").append(item);}for(const row of rows)$("home-feed").append(card(row));if(!rows.length&&!message)empty("home-feed","No matching dated records available.");
 const list=$("sources-list");list.replaceChildren();for(const k of Object.keys(paths)){const p=node("p",""),a=node("a","",k);a.href=sourcePath(k);p.append(a,document.createTextNode(" · "+(feed[k]?"Retrieved; observation dates shown in Decisions":errors[k]||"Awaiting retrieval")));list.append(p);}
 scenario();
}
for(const button of document.querySelectorAll("[data-category],[data-filter]"))button.onclick=()=>{const key=button.hasAttribute("data-category")?"category":"filter";if(key==="category")category=button.dataset.category;else filter=button.dataset.filter;for(const b of document.querySelectorAll("[data-"+key+"]"))b.setAttribute("aria-pressed",String(b===button));render();};
$("alternative").oninput=scenario;
window.addEventListener("hashchange",route);
show("today",new Intl.DateTimeFormat("en-US",{weekday:"long",month:"long",day:"numeric"}).format(new Date()));
route();
async function refresh(){if(refreshing)return;refreshing=true;$("refresh").disabled=true;$("feed-status").textContent="Refreshing public platform records…";await Promise.all(Object.entries(paths).map(async ([k,path])=>{delete feed[k];delete errors[k];try{const r=await fetch("https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/main/"+path,{cache:"no-store",signal:AbortSignal.timeout(15000),referrerPolicy:"no-referrer"});if(!r.ok)throw Error("HTTP "+r.status);const d=await r.json();if(!d||typeof d!=="object"||Array.isArray(d))throw Error("Invalid record");feed[k]=d;}catch(e){errors[k]="Unavailable";}}));$("feed-status").textContent=Object.keys(feed).length+" of "+Object.keys(paths).length+" public records retrieved · "+new Date().toLocaleString()+". Source vintages vary.";$("refresh").disabled=false;refreshing=false;render();}
$("profile-form").onsubmit=e=>{e.preventDefault();render();location.hash="decisions";};$("clear").onclick=()=>{$("alternative").value="";$("alternative-source").value="";restore({});};$("refresh").onclick=refresh;$("export").onclick=()=>{const b=new Blob([JSON.stringify(profile(),null,2)],{type:"application/json"}),a=document.createElement("a");a.href=URL.createObjectURL(b);a.download="personal-profile.json";a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);};
function status(msg){$("auth-status").textContent=msg;}
function authUI(){for(const k of ["email","password","login","signup"])$(k).disabled=!config||!!session;for(const k of ["logout","save","load","delete","monitoring","stop-monitor","watch-refresh"])$(k).disabled=!session;if(!session){$("monitoring").checked=false;resetWatch("Sign-in and consent are required. No private monitoring is active for guests.");}}
async function api(path,opts={}){if(!config)throw Error("Not configured");const r=await fetch(config.url+path,{...opts,cache:"no-store",headers:{"apikey":config.publishableKey,"Content-Type":"application/json",...(session?{Authorization:"Bearer "+session.access_token}:{}),...opts.headers}});if(!r.ok){if(r.status===401&&session){session=null;restore({});authUI();}throw Error("Request failed ("+r.status+")");}return r.status===204?null:r.text().then(t=>t?JSON.parse(t):null);}
async function auth(signup){if(!config||session)return;const email=$("email").value.trim(),password=$("password").value;if(!$("auth-form").reportValidity())return;$("password").value="";try{const r=await api(signup?"/auth/v1/signup":"/auth/v1/token?grant_type=password",{method:"POST",body:JSON.stringify({email,password})});if(r?.access_token&&r?.user?.id){session=r;status("Signed in. Save or load your private profile explicitly.");refreshWatch();}else status("Check your email to confirm your account, then sign in.");}catch(e){status(e.message);}authUI();}
$("auth-form").onsubmit=e=>{e.preventDefault();auth(false);};$("signup").onclick=()=>auth(true);$("logout").onclick=async()=>{try{await api("/auth/v1/logout",{method:"POST"});status("Signed out.");}catch{status("Local session cleared; server sign-out could not be confirmed.");}finally{session=null;restore({});$("email").value="";authUI();}};
$("save").onclick=async()=>{if(!$("profile-form").reportValidity())return;try{await api("/rest/v1/pi_profiles?on_conflict=user_id",{method:"POST",headers:{Prefer:"resolution=merge-duplicates,return=minimal"},body:JSON.stringify({user_id:session.user.id,profile:profile(),monitoring:$("monitoring").checked})});status("Private profile saved.");refreshWatch();}catch(e){status(e.message);}};
$("load").onclick=async()=>{try{const r=await api("/rest/v1/pi_profiles?select=profile,monitoring&user_id=eq."+encodeURIComponent(session.user.id));if(r?.length){restore(r[0].profile);$("monitoring").checked=r[0].monitoring===true;status("Private profile loaded.");refreshWatch();}else status("No saved profile.");}catch(e){status(e.message);}};
$("delete").onclick=async()=>{if(!confirm("Delete your saved profile?"))return;try{await api("/rest/v1/pi_profiles?user_id=eq."+encodeURIComponent(session.user.id),{method:"DELETE"});restore({});$("monitoring").checked=false;resetWatch("Saved profile and its monitoring results deleted.");status("Saved profile deleted.");}catch(e){status(e.message);}};
function resetWatch(message){$("watch-list").replaceChildren();$("watch-status").textContent=message;}
async function refreshWatch(){
 if(!session){resetWatch("Sign-in and consent are required. No private monitoring is active for guests.");return;}
 const current=session.user.id;
 resetWatch("Checking private monitoring…");
 try{
  const rows=await api("/rest/v1/pi_watch_results?select=checked_at,findings,feed_status&user_id=eq."+encodeURIComponent(current));
  if(session?.user?.id!==current)return;
  const r=rows?.[0];if(!r){resetWatch("No current monitoring results. Save an opted-in profile to enable hourly matching.");return;}
  const when=Date.parse(r.checked_at);if(!Number.isFinite(when)||Date.now()-when>7200000||when>Date.now()+60000){resetWatch("Monitoring result is stale or unverified. Await a new backend run.");return;}
  const checks=Object.values(r.feed_status||{}),retrieved=checks.filter(s=>s==="retrieved").length;
  $("watch-status").textContent="Last checked "+new Date(when).toLocaleString()+" · "+retrieved+" of "+checks.length+" source records retrieved. ";
  const items=(Array.isArray(r.findings)?r.findings:[]).filter(x=>x&&typeof x.title==="string"&&typeof x.detail==="string"&&typeof x.value==="number"&&Number.isFinite(x.value)&&typeof x.date==="string"&&safeLink(x.source));
  if(!items.length)$("watch-status").textContent+="No evidence-supported match for your saved circumstances.";
  $("watch-list").replaceChildren(...items.map(x=>card({...x,status:"Private monitoring · rule-based",value:String(x.value)+" "+x.unit})));
 }catch{resetWatch("Private monitoring unavailable. No findings have been assumed.");}
}
$("watch-refresh").onclick=refreshWatch;
$("stop-monitor").onclick=async()=>{if(!session)return;try{await api("/rest/v1/pi_profiles?user_id=eq."+encodeURIComponent(session.user.id),{method:"PATCH",headers:{Prefer:"return=minimal"},body:JSON.stringify({monitoring:false})});$("monitoring").checked=false;resetWatch("Monitoring stopped. Previous results are no longer accessible.");status("Monitoring consent withdrawn.");}catch(e){status(e.message);}};
async function configure(){try{const r=await fetch("./auth-config.json",{cache:"no-store"});if(!r.ok)return;const c=await r.json();if(/^https:\/\/[a-z0-9]+\.supabase\.co$/.test(c.url)&&typeof c.publishableKey==="string"&&c.publishableKey.startsWith("sb_publishable_")){config=c;status("Account service configured. Sign in or create an account.");authUI();}}catch{}}
render();authUI();refresh();configure();setInterval(()=>{if(document.visibilityState==="visible"){refresh();if(session)refreshWatch();}},300000);
