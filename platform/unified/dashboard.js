/* Power Atlas one-stop dashboard. Every displayed research number is read from
   existing published JSON, never inferred from a ZIP or fabricated on failure. */
(() => {
"use strict";
const $ = id => document.getElementById(id);
const el = (tag, cls, value) => {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (value !== undefined && value !== null) n.textContent = String(value);
  return n;
};
const safeExternal = value => {
  try {
    const u = new URL(value, location.href);
    return u.protocol === "https:" && !u.username && !u.password ? u.href : null;
  } catch { return null; }
};
const link = (label, url, cls="") => {
  const href = safeExternal(url);
  if (!href) return null;
  const a = el("a", cls, label);
  a.href = href; a.rel = "noopener noreferrer"; a.target = "_blank";
  return a;
};
async function loadJSON(path, schema) {
  const response = await fetch(path, {cache:"no-store", credentials:"same-origin"});
  if (!response.ok) throw new Error("HTTP " + response.status);
  const value = await response.json();
  if (!value || value.schema !== schema) throw new Error("Unexpected source format");
  return value;
}
function errorMessage(root, text) {
  root.replaceChildren(el("p", "load-text", text));
}
const money = new Intl.NumberFormat("en-US", {style:"currency", currency:"USD", maximumFractionDigits:0});

/* The visitor's ZIP is opt-in and stored only in the local browser via the
   preexisting PowerAtlasZIP module. Never geolocate or invent local statistics. */
function initZip() {
  const control = $("locationControl"), form = $("zipEditor"), input = $("dashboardZip");
  const cancel = $("zipCancel"), name = $("locationName"), help = $("locationHelp"), status = $("zipStatus");
  const manager = window.PowerAtlasZIP;
  const valid = x => /^\d{5}$/.test(x || "");
  const get = () => {
    const fromApi = manager?.get?.();
    if (valid(fromApi)) return fromApi;
    try { const value = localStorage.getItem("power-atlas:visitor-zip:v1"); return valid(value) ? value : null; }
    catch { return null; }
  };
  function render() {
    const zip = get();
    name.textContent = zip ? "ZIP " + zip : "Your community";
    help.textContent = zip ? "Saved on this device · no precise location collected" : "Choose a ZIP once. We'll keep it on this device.";
    control.textContent = zip ? "Change ZIP " + zip : "Set my ZIP";
    if (zip && document.activeElement !== input) input.value = zip;
  }
  control.addEventListener("click", () => {
    const opening = form.hidden;
    form.hidden = !opening; control.setAttribute("aria-expanded", String(opening));
    if (opening) { input.value = get() || ""; input.focus(); }
  });
  cancel.addEventListener("click", () => { form.hidden = true; control.setAttribute("aria-expanded","false"); });
  input.addEventListener("input", () => { input.value = input.value.replace(/\D/g,"").slice(0,5); input.removeAttribute("aria-invalid"); });
  form.addEventListener("submit", event => {
    event.preventDefault();
    const value = input.value.trim();
    if (!valid(value)) {
      input.setAttribute("aria-invalid","true");
      status.textContent = "Enter exactly five digits for a ZIP code.";
      input.focus(); return;
    }
    let saved = false;
    if (manager?.save) saved = manager.save(value);
    else { try { localStorage.setItem("power-atlas:visitor-zip:v1",value); saved=true; } catch {} }
    if (!saved) {status.textContent = "This browser cannot save your ZIP. You can still explore the national data.";return;}
    status.textContent = "ZIP " + value + " saved on this device.";
    form.hidden=true;control.setAttribute("aria-expanded","false");render();
  });
  window.addEventListener("poweratlas:zip-preference",render);
  window.addEventListener("storage",render);
  render();
  if(new URLSearchParams(location.search).get("edit-zip")==="1")control.click();
}
function renderSpending(data) {
  const root = $("spendingBars");
  if (!data.baseline || !Array.isArray(data.categories) || data.categories.length < 1) throw Error("Missing spending data");
  const categories = data.categories.filter(item => Number.isFinite(item.annualUsd) && item.annualUsd > 0).slice(0,4);
  if (!categories.length) throw Error("No measured categories");
  const max = Math.max(...categories.map(item => item.annualUsd));
  root.replaceChildren();
  categories.forEach(item => {
    const card = el("div","spend-item");
    const head = el("div","spend-head");
    head.append(el("span",null,item.label),el("strong",null,money.format(item.annualUsd)));
    const track = el("div","spend-track");
    const bar = el("span");
    bar.style.width = (100 * item.annualUsd / max).toFixed(2) + "%";
    bar.setAttribute("role","img");
    bar.setAttribute("aria-label",item.label + ": " + money.format(item.annualUsd) + " per year");
    track.append(bar);
    card.append(head,track,el("small",null,(item.coverage || "").slice(0,170)));
    root.append(card);
  });
  $("spendingSubtitle").textContent = "2025 national average annual spending per BLS consumer unit";
  $("spendingNote").textContent = "National averages, not local ZIP rents or personal bills. Housing includes utilities; groceries are food-at-home only. These four selected categories do not constitute a complete household budget. Differences are not estimates of monopoly overcharges.";
  const source = safeExternal(data.baseline.sourceUrl);
  if (source) $("spendingSource").href = source;
}
function renderMarket(data) {
  if (!Array.isArray(data.cases)) throw Error("Missing market research");
  const selected = ["beef","pbms","hospitals"].map(id => data.cases.find(c => c.id === id)).filter(Boolean);
  if (!selected.length) throw Error("No published market findings");
  const root = $("marketFindings"); root.replaceChildren();
  selected.forEach(item => {
    const card = el("article","finding"), top=el("div","finding-top");
    const value = String(item.unit || "").startsWith("~") ? "~" + String(item.metric) + "%" : String(item.metric) + String(item.unit || "");
    top.append(el("b",null,item.name),el("span","finding-value",value));
    card.append(top,el("p",null,item.metricLabel));
    const note = el("small",null,item.scope + " · " + item.period);
    card.append(note);
    const source = link("Open original research ↗",item.source);
    if (source) card.append(source);
    root.append(card);
  });
  root.append(el("p","load-text","Each percentage has a different denominator; these are separate findings, not parts of one total."));
}
const topics = [
  {title:"Housing & rent",desc:"Local rents, affordability and housing decisions.",href:"my-life.html#what",cat:"costs",icon:"⌂"},
  {title:"The real cost of living",desc:"Compare benchmarks with daily costs.",href:"cost-gap.html",cat:"costs",icon:"▥"},
  {title:"Transportation & tolls",desc:"Fares, penalties and the cost of moving goods.",href:"my-life.html#what",cat:"costs",icon:"⇄"},
  {title:"Market concentration",desc:"Competition, mergers and pricing leverage.",href:"market-power.html",cat:"power",icon:"◈"},
  {title:"Corporate ownership",desc:"Follow connections behind businesses.",href:"corporate-ownership.html",cat:"power",icon:"◉"},
  {title:"Political funding",desc:"Dark money and campaign influence.",href:"dark-money.html",cat:"power",icon:"$"},
  {title:"Donor intelligence",desc:"Follow contribution records and donor networks.",href:"donor-intelligence.html",cat:"power",icon:"◎"},
  {title:"Money trails",desc:"Political and financial flows, with source checks.",href:"financial-flows.html",cat:"power",icon:"⇢"},
  {title:"Business influence",desc:"Public contracts, campaign networks and evidence limits.",href:"business-influence.html",cat:"power",icon:"◉"},
  {title:"Banking & bailouts",desc:"Crashes, rescues and institutional accountability.",href:"banking-power.html",cat:"power",icon:"▣"},
  {title:"Corporate consumer practices",desc:"Hidden costs, promotion rules and fine print.",href:"consumer-practices.html",cat:"costs",icon:"◐"},
  {title:"Telecom promotions",desc:"Phone-plan upgrade pricing and offers.",href:"telecom-promotions.html",cat:"costs",icon:"▱"},
  {title:"Class-action claims",desc:"Where to look for consumer settlements.",href:"class-actions.html",cat:"costs",icon:"§"},
  {title:"Jobs & service automation",desc:"Staff reductions and customer access.",href:"service-accountability.html",cat:"risk",icon:"⌘"},
  {title:"AI crash scenarios",desc:"Follow the possible knock-on effects.",href:"ai-crash.html",cat:"risk",icon:"◇"},
  {title:"AI financing risks",desc:"Financial dependencies and concentration.",href:"ai-financing-shock.html",cat:"risk",icon:"▤"},
  {title:"Economic fragility",desc:"Risks, leading signals and uncertainty.",href:"economic-fragility.html",cat:"risk",icon:"⌁"},
  {title:"Public integrity cases",desc:"Official cases, evidence and legal status.",href:"investigations.html",cat:"power",icon:"⚖"},
  {title:"Public officials' trading",desc:"Financial disclosures and trade records.",href:"public-trading.html",cat:"power",icon:"▦"},
  {title:"Voting access",desc:"Representation and participation.",href:"voting-access.html",cat:"power",icon:"▧"},
  {title:"Reform lab",desc:"Explore safeguards and reform proposals.",href:"reform-lab.html",cat:"power",icon:"✦"},
  {title:"Wealth advantage",desc:"Large-scale money and unequal rules.",href:"wealth-advantage.html",cat:"power",icon:"◫"},
  {title:"Money at scale",desc:"Make billions and trillions understandable.",href:"money-scale.html",cat:"power",icon:"∞"}
];
function initTopics() {
  const grid = $("topicGrid"), toggle = $("toggleTopics");
  let expanded = false, activeFilter = "all";
  function render(filter) {
    activeFilter=filter;
    const matching = topics.filter(t => filter === "all" || t.cat === filter);
    const visible = filter === "all" && !expanded ? matching.slice(0,8) : matching;
    toggle.hidden = filter !== "all" || matching.length <= 8;
    toggle.textContent = expanded ? "Show featured topics" : "Show all " + topics.length + " topics";
    grid.replaceChildren();
    visible.forEach(t => {
      const a=el("a","topic-card");a.href=t.href;
      const icon=el("span","topic-icon",t.icon);icon.setAttribute("aria-hidden","true");
      a.append(icon,el("h3",null,t.title),el("p",null,t.desc),el("span","topic-more","Explore ↗"));
      grid.append(a);
    });
  }
  document.querySelectorAll(".topic-filter").forEach(button => button.addEventListener("click",() => {
    expanded=false;
    document.querySelectorAll(".topic-filter").forEach(b=>{const active=b===button;b.classList.toggle("is-active",active);b.setAttribute("aria-pressed",String(active));});
    render(button.dataset.filter);
  }));
  toggle.addEventListener("click",()=>{expanded=!expanded;render(activeFilter);});
  render("all");
}
let cases = [], showingAll = false, caseAsOf = "";
function renderCases() {
  const term = $("caseSearch").value.trim().toLowerCase();
  const status = $("caseStatus").value;
  const matched = cases.filter(c => {
    const haystack = [c.title,c.region,c.category,c.summary,c.status,...(c.people||[]).map(p=>p.name)].join(" ").toLowerCase();
    return (!term || haystack.includes(term)) && (!status || c.status === status);
  });
  const visible = showingAll ? matched : matched.slice(0,6);
  const root = $("caseGrid");root.replaceChildren();
  for (const c of visible) {
    const card = el("article","case-card"),meta = el("div","case-meta");
    meta.append(el("span",null,c.region || "US"),el("span",null,c.category || "Public integrity"));
    const statusBadge = el("span","status-label",String(c.status||"Status not supplied").replaceAll("_"," "));
    meta.append(statusBadge);
    card.append(meta,el("h3",null,c.title),el("p",null,c.plain_language?.summary || c.summary || "See the source records for case details."));
    const links = el("div","case-links");
    const source = Array.isArray(c.sources) ? c.sources.map(s=>link("Official source ↗",s.url)).find(Boolean) : null;
    if (source) links.append(source);
    const deep = el("a",null,"Explore cases ↗");
    deep.href = "investigations.html";
    links.append(deep);
    card.append(links);root.append(card);
  }
  if (!visible.length) root.append(el("p","load-text","No matches. Try a different term or legal status."));
  const count = matched.length;
  $("caseResultsLabel").textContent = count + " of " + cases.length + " curated cases match · reviewed " + caseAsOf + " · non-exhaustive, not live court tracking.";
  const toggle = $("toggleCases");
  toggle.hidden = matched.length <= 6;
  toggle.textContent = showingAll ? "Show fewer cases" : "Show all " + matched.length + " cases";
}
async function initCases() {
  const root=$("caseGrid");
  try {
    const data=await loadJSON("investigations-data.json","power-atlas.public-integrity-case-index.v1");
    if (!Array.isArray(data.cases) || !data.totals || !/^\d{4}-\d{2}-\d{2}$/.test(data.as_of)) throw Error("Missing case index");
    cases = data.cases.filter(c=>c && typeof c.title === "string");
    caseAsOf = data.as_of;
    const stats = $("caseStats");
    stats.replaceChildren();
    [[cases.length,"Curated cases"],[data.totals.unique_named_people,"Named people"],[data.totals.source_links,"Source links"]].forEach(([value,label])=>{
      const cell=el("div");cell.append(el("strong",null,value),el("small",null,label));stats.append(cell);
    });
    stats.append(el("div","stat-disclaimer","Legal outcomes differ. A charge is not proof of guilt. Review date: " + caseAsOf + "."));
    const statuses=[...new Set(cases.map(c=>c.status).filter(s=>typeof s==="string"))].sort();
    statuses.forEach(value => {const option=el("option",null,value.replaceAll("_"," "));option.value=value;$("caseStatus").append(option);});
    renderCases();
  } catch {
    $("caseResultsLabel").textContent = "Case index unavailable.";
    errorMessage(root,"We couldn't load the reviewed case records. Please use the full investigations page.");
  }
}
function initCaseControls(){
  $("caseSearch").addEventListener("input",()=>{showingAll=false;renderCases();});
  $("caseStatus").addEventListener("change",()=>{showingAll=false;renderCases();});
  $("toggleCases").addEventListener("click",()=>{showingAll=!showingAll;renderCases();});
}
async function initReferences(){
  const root=$("sourceDirectory");
  try {
    const data=await loadJSON("data/source-reference-index-v1.json","power-atlas.source-reference-index.v1");
    if (data.activeMode!=="reference" || !Array.isArray(data.sources)) throw Error("Not reference mode");
    $("referenceCount").textContent = "· " + data.sources.length + " links · checked " + data.asOf;
    root.replaceChildren();
    data.sources.forEach(entry=>{
      const a=link("View source ↗",entry.officialReferenceURL);
      if (!a) return;
      const card=el("div","source-entry");
      card.append(el("b",null,entry.publisher),el("small",null,entry.coverageCaveat || "Coverage not provided"),a);
      root.append(card);
    });
  } catch {
    errorMessage(root,"Source directory unavailable. See the source audit for current records.");
  }
}
function initAction() {
  const issue=$("actionIssue"),button=$("actionButton");
  issue.addEventListener("change",()=>{
    if (!/^(housing|consumer|market|work|health|transport|money|voting)$/.test(issue.value))return;
    button.href="take-action.html?issue="+encodeURIComponent(issue.value)+"#find";
  });
}
function initNavigation(){
  const anchors=[...document.querySelectorAll(".side-nav a[href^='#']")];
  anchors.forEach(a=>a.addEventListener("click",()=>{
    anchors.forEach(s=>s.removeAttribute("aria-current"));
    a.setAttribute("aria-current","page");
  }));
}
initZip();initTopics();initCaseControls();initAction();initNavigation();
Promise.allSettled([
  loadJSON("household-market-bridge.json","power-atlas.market-power.household-bridge.v1").then(renderSpending).catch(()=>errorMessage($("spendingBars"),"National spending data is temporarily unavailable. View the BLS original source.")),
  loadJSON("market-power.json","power-atlas.market-power.v1").then(renderMarket).catch(()=>errorMessage($("marketFindings"),"Market research could not load. Use the Market Power investigation.")),
  initCases(),
  initReferences()
]);
})();