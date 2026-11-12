/* Power Atlas — account-free bug reports captured as PostHog API survey responses.
 * Project configuration comes from Vercel environment variables, never Git.
 * No IP, ZIP, URL query string, email, session replay or screenshot is submitted.
 */
"use strict";

const SURVEY_ID = "01a1cd1f-de06-0000-eda7-520ae05958d0";
const QUESTIONS = [
  ["0917d93c-0752-4e45-adfb-d540822f2fc0", "Type of issue", "category"],
  ["87af5194-d112-4dfb-b153-f982f5352bc5", "Short summary", "summary"],
  ["01b9446f-f2b3-4097-bd83-49af2e269fec", "What happened?", "details"],
  ["19208466-9871-41f2-9953-69df3c5cc02b", "What did you expect? (optional)", "expected"],
  ["ae86d64b-e7f0-4243-8ff5-a97edc64896a", "How can we reproduce it? (optional)", "steps"],
];
const CATEGORIES = new Set([
  "Broken button, navigation or page",
  "Incorrect or missing data",
  "Chart or visualization problem",
  "Accessibility issue",
  "Other",
]);
const MAX_BYTES = 11000;

function fail(res, code, message) {
  res.status(code).json({ ok: false, message });
}
function cleanText(value, max) {
  return typeof value === "string" ? value.trim().slice(0, max + 1) : "";
}
function pagePath(value) {
  if (typeof value !== "string" || value.length > 200) return "";
  // Accept only paths. Never log or transmit query strings, hashes or full URLs.
  return /^\/[a-zA-Z0-9_./-]{0,190}$/.test(value) && !value.includes("..") ? value : "";
}
async function capture(host, token, event, distinctId, submissionId, properties) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 9000);
  try {
    const response = await fetch(host + "/i/v0/e/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        api_key: token,
        event,
        distinct_id: distinctId,
        properties: { ...properties, $lib: "power-atlas-bug-report", $lib_version: "1" },
      }),
      signal: controller.signal,
    });
    if (!response.ok) throw new Error("Capture rejected");
  } finally {
    clearTimeout(timeout);
  }
}
module.exports = async function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");
  res.setHeader("X-Content-Type-Options", "nosniff");
  if (req.method !== "POST") return fail(res, 405, "Use POST.");
  // Only the website's own JavaScript is allowed to POST from a browser.
  const origin = String(req.headers.origin || "");
  const hostHeader = String(req.headers["x-forwarded-host"] || req.headers.host || "");
  if (origin) {
    let submittedHost;
    try { submittedHost = new URL(origin).host; } catch (_) { return fail(res, 403, "Invalid origin."); }
    if (submittedHost !== hostHeader) return fail(res, 403, "Cross-site reports are not allowed.");
  }
  const body = typeof req.body === "string" ? (() => { try { return JSON.parse(req.body); } catch (_) { return null; } })() : req.body;
  if (!body || typeof body !== "object" || Array.isArray(body) ||
      JSON.stringify(body).length > MAX_BYTES) return fail(res, 400, "Invalid or oversized report.");
  if (typeof body.submissionId !== "string" ||
      !/^[0-9a-f]{8}-[0-9a-f-]{27,40}$/i.test(body.submissionId)) return fail(res, 400, "Invalid submission ID.");
  if (body.website !== undefined && body.website !== "") return fail(res, 400, "Invalid report.");
  const path = pagePath(body.page);
  if (!path) return fail(res, 400, "Invalid page address.");

  const action = body.action;
  if (!["shown", "dismissed", "sent"].includes(action)) return fail(res, 400, "Invalid report action.");
  const token = process.env.POSTHOG_PUBLIC_TOKEN || "";
  const host = process.env.POSTHOG_API_HOST || "";
  if (!/^phc_[a-zA-Z0-9_-]{10,}$/.test(token) ||
      !/^https:\/\/(us|eu)\.i\.posthog\.com$/.test(host))
    return fail(res, 503, "Bug reporting is temporarily unavailable. Please copy your report.");

  const submissionId = body.submissionId;
  const distinctId = "pa-report-" + submissionId;
  const base = { $survey_id: SURVEY_ID, pa_page: path, pa_surface: "power-atlas" };

  let event;
  let props;
  if (action === "shown") {
    event = "survey shown";
    props = { ...base, $set: { $survey_last_seen_date: new Date().toISOString() } };
  } else if (action === "dismissed") {
    event = "survey dismissed";
    props = { ...base, $set: { ["$survey_dismissed/" + SURVEY_ID]: true } };
  } else {
    const data = {
      category: cleanText(body.category, 90),
      summary: cleanText(body.summary, 140),
      details: cleanText(body.details, 4000),
      expected: cleanText(body.expected, 2000),
      steps: cleanText(body.steps, 2000),
    };
    if (!CATEGORIES.has(data.category) || data.summary.length < 5 || data.summary.length > 140 ||
        data.details.length < 10 || data.details.length > 4000 ||
        data.expected.length > 2000 || data.steps.length > 2000) {
      return fail(res, 400, "Please complete the required fields.");
    }
    event = "survey sent";
    props = {
      ...base,
      $survey_submission_id: submissionId,
      $survey_completed: true,
      $survey_questions: QUESTIONS.map(([id, question]) => ({ id, question })),
      $set: { ["$survey_responded/" + SURVEY_ID]: true },
    };
    for (const [id, , key] of QUESTIONS) {
      if (data[key]) props["$survey_response_" + id] = data[key];
    }
  }
  try {
    await capture(host, token, event, distinctId, submissionId, props);
    res.status(200).json({ ok: true, received: action === "sent" });
  } catch (_) {
    return fail(res, 502, "The reporting service could not confirm receipt. Please retry or copy your report.");
  }
};
