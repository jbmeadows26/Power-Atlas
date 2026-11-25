import './strategicRiskWatch.css';

// Manually source-reviewed on 2026-11-25. Publication dates are not incident dates.
// Deliberately separate from live alerts, anomaly scores and forecast probabilities.
const records = [
  {
    "id": "odni-2026-ata",
    "published": "2026-03-18",
    "publisher": "Office of the Director of National Intelligence",
    "title": "2026 Annual Threat Assessment: AI and national security",
    "url": "https://archive.dni.gov/index.php/newsroom/press-releases/press-releases-2026/4142-pr-03-26",
    "type": "Official intelligence assessment",
    "reliability": "High — official primary source",
    "confidence": "High that the assessment was issued; future impacts uncertain",
    "domain": "Defense, Security & Cyber",
    "finding": "The U.S. Intelligence Community assesses that AI will accelerate cyber threats and alter the security landscape. The release cites a 2025 AI-assisted extortion operation.",
    "limit": "An assessment and historical example, not a current incident or forecast of catastrophe.",
    "watch": "Official cyber advisories and independently confirmed service disruptions."
  },
  {
    "id": "iasr-2026",
    "published": "2026-02-03",
    "publisher": "International AI Safety Report",
    "title": "2026 international scientific assessment",
    "url": "https://internationalaisafetyreport.org/publication/2026-report-extended-summary-policymakers",
    "type": "Independent scientific synthesis",
    "reliability": "High — primary research synthesis",
    "confidence": "High for documented findings; uncertain for future real-world harm",
    "domain": "Defense, Security & Cyber / Societal Resilience & Health",
    "finding": "Researchers report evidence of AI-assisted cyber operations, growing concern about biological misuse and difficulties evaluating increasingly capable systems.",
    "limit": "Capability and evaluation findings do not establish that an attack or outbreak is imminent.",
    "watch": "Published safety evaluations, official public-health alerts and verified incident reporting."
  },
  {
    "id": "gates-2026-memo",
    "published": "2026-08-26",
    "publisher": "Bill Gates / Gates Notes",
    "title": "AI transition risk and governance memo",
    "url": "https://www.gatesnotes.com/a-turbulent-ai-era-and-critical-choices-to-make",
    "type": "Attributed expert judgment",
    "reliability": "Primary source for the speaker's views; not independent validation",
    "confidence": "High for attribution; unquantified for predictions",
    "domain": "Macroeconomics & Markets / Defense, Security & Cyber",
    "finding": "Gates warns of workforce disruption, malicious use of AI, concentration of power and potential loss of control, while advocating governance and beneficial applications.",
    "limit": "Personal assessment by an industry participant with disclosed AI-related relationships; not an official threat assessment.",
    "watch": "Labor-market indicators, independently verified AI incidents and enacted governance measures."
  },
  {
    "id": "gates-2026-interview",
    "published": "2026-09-27",
    "publisher": "The Guardian, reporting NBC interview",
    "title": "Gates warns of catastrophic potential from unchecked AI",
    "url": "https://www.theguardian.com/us-news/2026/sep/27/bill-gates-artificial-intelligence-kristen-welker",
    "type": "Reported interview / strategic context",
    "reliability": "Secondary reporting; direct NBC transcript not verified",
    "confidence": "Moderate for reported wording; no confidence estimate for scenario",
    "domain": "Defense, Security & Cyber",
    "finding": "Gates urged regulation and described a conditional scenario involving extremely severe casualties from AI misuse.",
    "limit": "No event date, probability, imminent threat or independent evidence that such an event is underway. Not independent corroboration of his August memo.",
    "watch": "Seek original interview transcript and independent risk assessments; do not escalate on repeated headlines."
  },
  {
    "id": "gates-2025-climate",
    "published": "2025-10-28",
    "publisher": "Bill Gates / Gates Notes",
    "title": "Counterevidence to claims of a doomsday prediction",
    "url": "https://www.gatesnotes.com/three-tough-truths-about-climate",
    "type": "Attributed expert judgment / context",
    "reliability": "Primary source for the speaker's views",
    "confidence": "High for attribution; not a comprehensive climate assessment",
    "domain": "Societal Resilience & Health / Energy & Resources",
    "finding": "Gates explicitly rejects the claim that climate change will end humanity while acknowledging serious impacts, especially on poorer populations.",
    "limit": "Historical context; not an all-hazards assessment or a new warning.",
    "watch": "Independent climate observations and official adaptation assessments."
  }
];
export default function StrategicRiskWatch(){
 return <section className="srw" aria-label="Strategic risk intelligence">
  <header><div className="srw-kicker">STRATEGIC OSINT / MANUALLY REVIEWED</div><h2>AI systemic risk watch</h2><p>Global strategic context · Reviewed 25 Nov 2026 · Not a live incident feed</p></header>
  <div className="srw-judgment"><strong>Assessment: monitor, not escalate</strong><p>Independent official and scientific sources support several risk mechanisms. No evidence in this collection establishes an imminent catastrophe, calibrated probability or confirmed new incident.</p></div>
  <div className="srw-grid">{records.map(r=><details className="srw-card" key={r.id}><summary><small>{r.type} · {r.published}</small><strong>{r.title}</strong><span>{r.publisher}</span><p>{r.finding}</p></summary><div className="srw-detail"><p><b>Domain:</b> {r.domain}</p><p><b>Source reliability:</b> {r.reliability}</p><p><b>Information confidence:</b> {r.confidence}</p><p><b>Limits:</b> {r.limit}</p><p><b>Collection requirement:</b> {r.watch}</p><a href={r.url} target="_blank" rel="noreferrer">Read source ↗</a></div></details>)}</div>
  <p className="srw-note">Escalation requires a separately dated, independently corroborated incident or measured threshold breach; duplicate reports and expert opinions do not increase an alert count. Collection requirements are not yet connected as automated feeds.</p>
 </section>;
}
