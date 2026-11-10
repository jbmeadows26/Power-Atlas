/* Consumer Watch v2 — evidence-led visual stories; source-of-truth is the public JSON. */
(() => {
  "use strict";
  const $ = id => document.getElementById(id);
  const root = document.body;
  const SOURCE = root.dataset.feed || "https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/main/data/consumer-practices/cases-v1.json";
  const SCHEMA = "power-atlas.consumer-practices.v1";
  const clean = value => String(value ?? "").replace(/[&<>"']/g, ch => ({
    "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;"
  }[ch]));
  const safeUrl = url => typeof url === "string" && /^https:\/\//i.test(url) ? clean(url) : "#";
  const link = (url, title, cls = "") =>
    '<a class="'+cls+'" href="'+safeUrl(url)+'" target="_blank" rel="noopener noreferrer">'+clean(title)+' <span aria-hidden="true">↗</span></a>';
  const STATUS = {
    terms: {short:"Published terms",plain:"Terms documented · No violation established",tone:"info"},
    lawsuit: {short:"Regulator lawsuit",plain:"Allegations · Not adjudicated",tone:"pending"},
    proposed: {short:"Proposed settlement",plain:"Agreement announced · Finality may vary",tone:"proposed"},
    settlement: {short:"Settlement / refunds",plain:"Settlement or refund action · May not admit liability",tone:"settled"}
  };
  // Each visual beat is an editorial shorthand supported by the specific
  // primary source and case narrative; the detailed source record remains linked.
  const STORIES = [
    {id:"tmobile",icon:"📱",short:"Phone upgrades",headline:"The upgrades compete for the same perks.",
     stages:[["THE OFFER","Up to $1,200 off an iPhone with 3 Picks"],["THE SMALL PRINT","Two-line T-Mix More has 4 account-shared Picks"],["THE REVEAL","Two 3-Pick deals would need 6 — 2 more than available"]],special:"Terms example, not a regulator deception finding. Offers and eligibility can change."},
    {id:"progress",icon:"🏠",short:"Renting a home",headline:"The rent you see may not be the rent you pay.",
     stages:[["THE HEADLINE","A home is advertised at a monthly rent"],["THE ALLEGATION","The FTC says mandatory fees weren't in the headline rent"],["THE IMPACT","Comparing homes on base rent alone can understate costs"]],special:"FTC/state proposed settlement; no final approval implied."},
    {id:"amazon",icon:"🔁",short:"Subscriptions",headline:"Starting a subscription is easier than stopping one.",
     stages:[["THE PROMISE","Sign up for a convenient membership"],["THE ALLEGATION","The FTC challenged enrollment consent and cancellation obstacles"],["THE OUTCOME","A $2.5B settlement, not a measure of every member's losses"]],special:"Settlement documented; does not describe every current enrollment."},
    {id:"dollar-general",icon:"🧾",short:"At checkout",headline:"The price tag and the register don't agree.",
     stages:[["ON THE SHELF","A product displays a shelf or advertised price"],["AT THE REGISTER","The FTC and states allege some checkout prices were higher"],["THE QUESTION","Could you spot the difference on each receipt?"]],special:"FTC/state lawsuit remains allegations, not a finding of liability."},
    {id:"adobe",icon:"📅",short:"Annual contracts",headline:"A monthly price can hide a yearly commitment.",
     stages:[["THE HEADLINE","A subscription price is displayed per month"],["THE CATCH ALLEGED","An annual contract with early-exit fees is not clear enough"],["THE IMPACT","Canceling early may cost more than expected"]],special:"FTC/DOJ lawsuit; current plan terms require fresh checking."},
    {id:"hopper",icon:"✈️",short:"Booking travel",headline:"The extras can sneak into the total.",
     stages:[["THE OFFER","Travel booking with a no-hidden-fees message"],["THE ALLEGATION","Preselected extras and price-freeze benefits were challenged"],["THE OUTCOME","FTC settlement order; check the all-in charge"]],special:"Court-entered order; the $35M settlement is not an estimate of each user's loss."}
  ];
  const ICONS = {
    "Telecommunications":"📱","Online shopping":"🛍️","Housing":"🏠","Digital subscriptions":"🔁",
    "Retail":"🧾","Delivery and transport":"🛵","Live events":"🎟️","Health products":"👓",
    "Business and restaurants":"🍽️","Auto dealerships":"🚗","Financial and bill payment":"💳",
    "Travel booking":"✈️"
  };
  let data = null, chosen = STORIES[0].id, activePattern = "", shown = [];
  const lookup = id => data?.cases?.find(c => c.id === id);
  const statusHtml = c => {
    const s = STATUS[c.status] || {short:"Source status unknown",plain:"Review original source",tone:"info"};
    return '<span class="cw-status cw-status--'+s.tone+'" title="'+clean(s.plain)+'">'+clean(s.short)+'</span>';
  };
  const caseDate = date => /^\d{4}-\d{2}-\d{2}$/.test(date) ? new Date(date+"T12:00:00").toLocaleDateString("en-US",{month:"short",year:"numeric"}) : "Undated";
  function renderStoryButtons() {
    $("pcStoryButtons").innerHTML = STORIES.filter(s=>lookup(s.id)).map(s =>
      '<button type="button" class="cw-tab '+(s.id===chosen?"is-active":"")+'" data-story="'+clean(s.id)+'" aria-pressed="'+(s.id===chosen)+'"><span class="cw-tab-icon" aria-hidden="true">'+s.icon+'</span><span>'+clean(s.short)+'</span></button>'
    ).join("");
  }
  function renderStory() {
    const s = STORIES.find(x=>x.id===chosen) || STORIES[0], c = lookup(s.id);
    if (!c) return;
    const title = $("pcStoryTitle"), badges = $("pcStoryMeta");
    title.textContent = s.headline;
    badges.innerHTML = '<span class="cw-companyname">'+clean(c.name)+'</span>'+statusHtml(c);
    $("pcStoryStages").innerHTML=s.stages.map((a,i)=>
      '<div class="cw-beat cw-beat--'+i+'"><span class="cw-beat-num">0'+(i+1)+'</span><div><span class="cw-beat-label">'+clean(a[0])+'</span><strong>'+clean(a[1])+'</strong></div></div>'
    ).join('<div class="cw-beat-arrow" aria-hidden="true">↓</div>');
    $("pcStoryNote").textContent = s.special;
    $("pcStorySource").innerHTML = link(c.source.url,"Read the original evidence","cw-primary-link");
    $("pcStoryLink").innerHTML = c.relatedPage ?
      '<a href="'+clean(c.relatedPage)+'" class="cw-secondary-link">Explore the phone deal math →</a>' :
      '<a href="#case-explorer" class="cw-secondary-link" data-showcase="'+clean(c.id)+'">Open the full case file →</a>';
    renderStoryButtons();
  }
  function renderPatternMap() {
    const counts = new Map();
    data.cases.forEach(c=>counts.set(c.tactic,(counts.get(c.tactic)||0)+1));
    const desc = {
      "hidden mandatory fees":"Fees added later",
      "cancellation trap":"Hard to cancel",
      "bait price":"Bait pricing",
      "service and contract trap":"Contract traps",
      "promotion limits":"Restricted offers",
      "checkout price mismatch":"Checkout mismatches",
      "service mismatch":"Service changes",
      "early-exit penalty":"Exit penalties",
      "misleading intermediary":"Bill-payment lookalikes",
      "refund not honored":"Refund disputes"
    };
    const all = [...counts.entries()].sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0])), max=Math.max(...all.map(x=>x[1]),1);
    const explore = $("pcExplorePattern");
    explore.disabled = all.length===0;
    if(all.length){explore.dataset.pattern=all[0][0]; explore.setAttribute("aria-label","Explore "+(desc[all[0][0]]||all[0][0])+" cases");}
    $("pcPatternGrid").innerHTML = all.map(([t,n])=>
      '<button type="button" class="cw-pattern '+(activePattern===t?"is-active":"")+'" data-pattern="'+clean(t)+'" aria-pressed="'+(activePattern===t)+'" aria-label="'+clean((desc[t]||t)+", "+n+" cases. Filter case files.")+'">'+
      '<span class="cw-pattern-name">'+clean(desc[t]||t)+'</span><span class="cw-track"><span class="cw-fill" style="width:'+(100*n/max)+'%"></span></span><strong>'+n+'</strong></button>'
    ).join("");
  }
  function card(c) {
    const amount = c.amount?'<span class="cw-figure">Enforcement or refund figure: '+clean(c.amount)+'</span>':"";
    return '<article class="cw-case" data-id="'+clean(c.id)+'">'+
      '<div class="cw-case-top"><span class="cw-case-avatar" aria-hidden="true">'+(ICONS[c.industry]||"📄")+'</span><span class="cw-case-number">CASE FILE · '+clean(caseDate(c.eventDate))+'</span></div>'+
      '<h3>'+clean(c.name)+'</h3><p class="cw-case-issue">'+clean(c.headline)+'</p>'+
      '<div class="cw-case-badges"><span class="cw-pill">'+clean(c.industry)+'</span>'+statusHtml(c)+'</div>'+
      '<details class="cw-detail"><summary>Open the evidence file <span aria-hidden="true">＋</span></summary>'+
      '<div class="cw-detail-body"><p><b>What regulators or company terms say</b>'+clean(c.claim)+'</p>'+
      '<p><b>Why it matters</b>'+clean(c.mechanism)+'</p>'+
      '<p><b>Evidence boundary</b>'+clean(c.implication)+'</p>'+
      '<p><b>One practical step</b>'+clean(c.action)+'</p>'+amount+
      '<div class="cw-detail-links">'+link(c.source.url,"Original official source","cw-primary-link")+
      (c.relatedPage?'<a href="'+clean(c.relatedPage)+'" class="cw-secondary-link">Visual deep dive →</a>':"")+'</div></div></details>'+
      '</article>';
  }
  function renderCases(){
    const q=$("pcSearch").value.trim().toLowerCase(),industry=$("pcIndustry").value,status=$("pcEvidence").value;
    shown = data.cases.filter(c =>
      (industry==="all"||c.industry===industry) && (status==="all"||c.status===status) &&
      (!activePattern || activePattern===c.tactic) &&
      (!q || [c.name,c.headline,c.claim,c.industry,c.tactic,c.mechanism].join(" ").toLowerCase().includes(q))
    );
    $("pcCases").innerHTML = shown.length?shown.map(card).join("") :
      '<div class="cw-empty"><strong>No case files match.</strong><p>Try clearing the search or changing a filter.</p></div>';
    $("pcCount").textContent=shown.length+" of "+data.cases.length+" case files";
    $("pcFilterBadge").textContent=activePattern ? "PATTERN: "+activePattern.toUpperCase() : "ALL DOCUMENTED PATTERNS";
    $("pcFilterBadge").hidden=!activePattern;
    renderPatternMap();
  }
  function setPattern(tactic){
    activePattern = activePattern===tactic ? "" : tactic;
    renderCases();
    $("case-explorer").scrollIntoView({behavior:"smooth",block:"start"});
  }
  function clearFilters(){
    $("pcSearch").value="";
    $("pcIndustry").value="all";
    $("pcEvidence").value="all";
    activePattern="";
    renderCases();
  }
  function setupCounts(){
    const counts=data.cases.reduce((a,c)=>(a[c.status]=(a[c.status]||0)+1,a),{});
    $("pcTotal").textContent=data.cases.length;
    $("pcIndustries").textContent=new Set(data.cases.map(c=>c.industry)).size;
    $("pcEnforcement").textContent=data.cases.filter(c=>c.status!=="terms").length;
    const bar=$("pcStatusOverview");
    bar.innerHTML=Object.keys(STATUS).map(k=>{
      const n=counts[k]||0;
      return '<div class="cw-evidence-item"><span class="cw-evidence-count">'+n+'</span><span class="cw-evidence-label">'+clean(STATUS[k].short)+'</span><span class="cw-evidence-rule"><i class="cw-evidence-color cw-evidence-color--'+k+'" style="width:'+(100*n/data.cases.length)+'%"></i></span></div>';
    }).join("");
    $("pcIndustry").innerHTML='<option value="all">All industries</option>'+
      [...new Set(data.cases.map(c=>c.industry))].sort().map(t=>'<option value="'+clean(t)+'">'+clean(t)+'</option>').join("");
    $("pcAsOf").textContent=data.asOf;
    if(Array.isArray(data.consumerActions)){
      $("pcActionList").innerHTML=data.consumerActions.slice(0,4).map((x,i)=>
        '<article class="cw-action"><span class="cw-action-number">0'+(i+1)+'</span><div><h3>'+clean(x.name)+'</h3><p>'+clean(x.detail)+'</p>'+link(x.url,"Official guidance")+'</div></article>'
      ).join("");
    }
  }
  function bind(){
    $("pcStoryButtons").addEventListener("click",event=>{
      const btn=event.target.closest("[data-story]");if(!btn)return;
      chosen=btn.dataset.story;renderStory();
    });
    $("pcPatternGrid").addEventListener("click",event=>{
      const btn=event.target.closest("[data-pattern]");if(btn)setPattern(btn.dataset.pattern);
    });
    $("pcExplorePattern").addEventListener("click",event=>{
      const tactic=event.currentTarget.dataset.pattern;
      if(tactic) { activePattern=""; setPattern(tactic); }
    });
    $("pcSearch").addEventListener("input",renderCases);
    ["pcIndustry","pcEvidence"].forEach(id=>$(id).addEventListener("change",renderCases));
    $("pcReset").addEventListener("click",clearFilters);
    document.addEventListener("click",event=>{
      const target=event.target.closest("[data-showcase]");if(!target)return;
      const caseId=target.dataset.showcase;
      clearFilters();
      window.setTimeout(()=>{
        const el=document.querySelector('.cw-case[data-id="'+caseId+'"] details');
        if(el){el.open=true;el.scrollIntoView({block:"center",behavior:"smooth"});}
      },80);
    });
  }
  async function init(){
    bind();
    try{
      const r=await fetch(SOURCE,{cache:"no-store"});
      if(!r.ok)throw Error("evidence feed unavailable");
      const d=await r.json();
      if(d.schema!==SCHEMA || !Array.isArray(d.cases) || d.cases.length===0 || !d.statuses)
        throw Error("unexpected evidence schema");
      data=d;
      if(!lookup(chosen)){const first=STORIES.find(s=>lookup(s.id));if(first)chosen=first.id;}
      setupCounts();renderStory();renderCases();
      $("pcDataState").textContent="SOURCE CONNECTED · "+d.asOf;
    }catch(e){
      $("pcDataState").textContent="SOURCE UNAVAILABLE";
      $("pcCount").textContent="Evidence could not be loaded";
      $("pcStoryTitle").textContent="Evidence feed unavailable";
      $("pcStoryStages").innerHTML='<div class="cw-empty">We don\'t show conclusions without their supporting records.</div>';
      $("pcStorySource").innerHTML="";
      $("pcStoryLink").innerHTML="";
      $("pcStoryNote").textContent="";
      $("pcCases").innerHTML='<div class="cw-empty"><strong>Evidence unavailable</strong><p>No unsourced company findings are displayed. '+link("https://github.com/jbmeadows26/Power-Atlas/blob/main/data/consumer-practices/cases-v1.json","Read the source dataset")+'</p></div>';
      $("pcPatternGrid").innerHTML='<p>Pattern counts will appear when source data loads.</p>';
    }
  }
  init();
})();