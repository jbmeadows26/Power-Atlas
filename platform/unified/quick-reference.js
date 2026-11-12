/* Power Atlas quick-reference browser: source pointers only, no record downloads. */
(() => {
  "use strict";
  const root = document.getElementById("quickReference");
  if (!root) return;
  const search = document.getElementById("quickReferenceSearch");
  const gate = document.getElementById("quickReferenceGate");
  const results = document.getElementById("quickReferenceResults");
  const status = document.getElementById("quickReferenceStatus");
  const asOf = document.getElementById("quickReferenceAsOf");
  const sourceIndex = "./data/source-reference-index-v1.json";
  const labels = {
    verified_committee_financial_transfers: "Federal political money",
    state_campaign_finance: "State campaign finance",
    state_certified_election_canvasses: "Certified election results",
    official_state_rollcalls: "Legislative votes",
    nationwide_lower_court_case_lifecycle: "Court dockets and decisions"
  };
  let sources = [];

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function safeHttps(raw) {
    try {
      const parsed = new URL(raw);
      if (parsed.protocol !== "https:" || parsed.username || parsed.password) return null;
      return parsed.href;
    } catch {
      return null;
    }
  }

  function render() {
    const q = search.value.trim().toLowerCase();
    const selectedGate = gate.value;
    const matches = sources.filter(s => {
      const text = [s.id, s.publisher, s.coverageCaveat, ...(s.linkedGateIDs || []), ...(s.linkedGateIDs || []).map(id => labels[id] || "")].join(" ").toLowerCase();
      return (!selectedGate || s.linkedGateIDs.includes(selectedGate)) && (!q || text.includes(q));
    });
    status.textContent = matches.length + " reference " + (matches.length === 1 ? "source" : "sources") +
      " · Link verified in the source register; underlying records are not yet verified by this lookup.";
    results.replaceChildren();
    if (!matches.length) {
      results.append(element("p", "compact", "No matching links. Try another term or show all source areas."));
      return;
    }
    for (const s of matches) {
      const card = element("article", "quick-card");
      const small = element("span", "quick-type", (s.authority === "official" ? "Official source" : "Public secondary archive") +
        " · " + (s.linkedGateIDs || []).map(id => labels[id] || id.replaceAll("_", " ")).join(" / "));
      const header = element("h3", null, s.publisher);
      const coverage = element("p", null, s.coverageCaveat);
      const linkRow = element("div", "quick-link-row");
      const url = safeHttps(s.officialReferenceURL);
      if (url) {
        const link = element("a", "quick-visit", "Open source ↗");
        link.href = url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        linkRow.append(link);
      }
      const note = element("small", "quick-status", "Source page identified · no records downloaded");
      card.append(small, header, coverage, linkRow, note);
      results.append(card);
    }
  }

  search.addEventListener("input", render);
  gate.addEventListener("change", render);
  (async () => {
    try {
      const response = await fetch(sourceIndex, { cache: "no-store" });
      if (!response.ok) throw new Error("Source catalog returned HTTP " + response.status);
      const data = await response.json();
      if (data.schema !== "power-atlas.source-reference-index.v1" ||
          data.activeMode !== "reference" || !Array.isArray(data.sources)) {
        throw new Error("Source catalog does not match approved reference-only schema");
      }
      sources = data.sources.filter(s => s && typeof s.id === "string" &&
        typeof s.publisher === "string" && Array.isArray(s.linkedGateIDs) &&
        safeHttps(s.officialReferenceURL));
      const ids = new Set(sources.flatMap(s => s.linkedGateIDs));
      for (const id of [...ids].sort((a, b) => (labels[a] || a).localeCompare(labels[b] || b))) {
        const option = document.createElement("option");
        option.value = id;
        option.textContent = labels[id] || id.replaceAll("_", " ");
        gate.append(option);
      }
      asOf.textContent = "Index checked " + data.asOf + " · Source availability can change.";
      render();
    } catch {
      status.textContent = "The quick-reference catalog is temporarily unavailable.";
      results.replaceChildren();
      const p = element("p", "compact", "View the source register in GitHub while this page is unavailable.");
      const link = element("a", null, "Open reference registry ↗");
      link.href = "https://github.com/jbmeadows26/Power-Atlas/blob/main/platform/unified/data/source-reference-index-v1.json";
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      p.append(" ", link);
      results.append(p);
    }
  })();
})();
