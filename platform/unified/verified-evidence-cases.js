/* Show narrowly checked original evidence, without turning it into full-gap closure. */
(() => {
  "use strict";
  const root = document.getElementById("verifiedEvidence");
  if (!root) return;
  const summary = document.getElementById("verifiedEvidenceSummary");
  const cards = document.getElementById("verifiedEvidenceCards");
  const src = "https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/main/data/health/";
  function el(tag, className, value) {
    const result = document.createElement(tag);
    if (className) result.className = className;
    if (value != null) result.textContent = value;
    return result;
  }
  function officialUrl(raw) {
    try {
      const x = new URL(raw);
      return x.protocol === "https:" && !x.username && !x.password ? x.href : null;
    } catch { return null; }
  }
  (async () => {
    try {
      const [progressResponse, casesResponse] = await Promise.all([
        fetch(src + "reference-gap-progress-v1.json", {cache:"no-store"}),
        fetch(src + "reference-first-evidence-cases-v1.json", {cache:"no-store"})
      ]);
      if (!progressResponse.ok || !casesResponse.ok) throw new Error("Evidence records unavailable");
      const [progress, receipt] = await Promise.all([progressResponse.json(), casesResponse.json()]);
      if (progress.schema !== "power-atlas.reference-gap-progress.v1" ||
          receipt.schema !== "power-atlas.bounded-evidence-checks.v1" ||
          progress.scope.fullGapClosures !== 0 || !Array.isArray(receipt.cases)) {
        throw new Error("Unexpected evidence progress schema");
      }
      summary.textContent = progress.scope.localGapCount + " local + " +
        progress.scope.nationalBlockingGateCount + " national gaps remain open · " +
        progress.scope.boundedEvidenceCasesReviewed + " bounded evidence checks reviewed";
      cards.replaceChildren();
      for (const item of receipt.cases) {
        if (item.originalGapClosureAllowed !== false) continue;
        const article = el("article", "gapcard");
        const label = el("div", "type", item.area.replaceAll("_", " ") + " · checked original evidence");
        const title = el("h3", null, item.boundedConclusion);
        const foot = el("p", "sourceType", "Narrow evidence check · does not close the full research gap");
        const details = el("details");
        const trigger = el("summary", null, "Inspect original sources and limitations");
        const list = el("ul");
        for (const source of item.sourceDocuments || []) {
          const href = officialUrl(source.url);
          if (!href) continue;
          const li = el("li");
          const a = el("a", null, source.authority + " · " + source.role.replaceAll("_", " "));
          a.href = href;
          a.target = "_blank";
          a.rel = "noopener noreferrer";
          li.append(a);
          list.append(li);
        }
        for (const limit of (item.limits || []).slice(0, 4)) {
          const li = el("li", "sourceType", limit);
          list.append(li);
        }
        details.append(trigger, list);
        article.append(label, title, foot, details);
        cards.append(article);
      }
    } catch {
      summary.textContent = "Detailed evidence progress is temporarily unavailable.";
      cards.replaceChildren();
      const note = el("p", "compact", "Inspect the original evidence ledger in GitHub.");
      const a = el("a", null, "Open dated evidence checks ↗");
      a.href = "https://github.com/jbmeadows26/Power-Atlas/blob/main/data/health/reference-first-evidence-cases-v1.json";
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      note.append(" ", a);
      cards.append(note);
    }
  })();
})();
