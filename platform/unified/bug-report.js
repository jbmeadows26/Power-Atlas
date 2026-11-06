/* Power Atlas: accessible, no-cost bug reporting on every research page. */
(function () {
  "use strict";
  if (document.getElementById("pa-bug-widget")) return;

  var host = document.createElement("div");
  host.id = "pa-bug-widget";
  document.body.appendChild(host);
  var ui = host.attachShadow({ mode: "open" });
  ui.innerHTML = `
    <style>
      :host { all: initial; font-family: Inter, system-ui, -apple-system, "Segoe UI", sans-serif; }
      *, *::before, *::after { box-sizing: border-box; }
      [hidden] { display: none !important; }
      button, input, select, textarea { font: inherit; }
      button { cursor: pointer; }
      #open {
        position: fixed; right: 18px; bottom: max(18px, env(safe-area-inset-bottom, 0px) + 12px);
        z-index: 2147483000; padding: 11px 17px; border-radius: 999px;
        border: 1px solid #5aa7b6; background: #103b50; color: #fff;
        box-shadow: 0 4px 18px #0005; font-size: 14px; font-weight: 700;
        display: inline-flex; gap: 9px; align-items: center; min-height: 44px;
      }
      #open:hover, #open:focus-visible { background: #155b70; }
      #shade {
        position: fixed; inset: 0; z-index: 2147483001; background: #071321b8;
        display: flex; align-items: center; justify-content: center; padding: 16px;
      }
      #dialog {
        width: min(100%, 520px); max-height: min(92dvh, 800px); overflow-y: auto;
        background: #fff; color: #162c3d; border: 1px solid #a0bac4; border-radius: 16px;
        box-shadow: 0 20px 70px #0008; padding: 24px; line-height: 1.45;
      }
      .top { display: flex; gap: 12px; justify-content: space-between; align-items: flex-start; }
      h2 { font-size: 23px; margin: 0; line-height: 1.2; }
      .sub { font-size: 13px; color: #526975; margin: 9px 0 17px; }
      .close { flex: none; background: transparent; border: 0; font-size: 25px; line-height: 1; color: #334e5d; padding: 4px 8px; }
      label { display: block; font-size: 13px; font-weight: 700; margin: 12px 0 5px; }
      input, select, textarea { display: block; width: 100%; border-radius: 8px; border: 1px solid #94aeb9; padding: 10px 11px; background: #fff; color: #142c3d; font-size: 14px; }
      textarea { min-height: 94px; resize: vertical; }
      input:focus-visible, select:focus-visible, textarea:focus-visible, button:focus-visible { outline: 3px solid #3cadd0; outline-offset: 2px; }
      .actions { display: flex; flex-wrap: wrap; gap: 9px; margin-top: 18px; }
      .primary { background: #126779; color: #fff; border: 1px solid #126779; padding: 11px 15px; border-radius: 9px; font-size: 14px; font-weight: 700; }
      .secondary { background: #eff5f6; color: #244153; border: 1px solid #b4cbd1; padding: 11px 15px; border-radius: 9px; font-size: 14px; font-weight: 700; }
      .foot { font-size: 12px; color: #526975; margin: 13px 0 0; }
      .status { min-height: 18px; font-size: 13px; color: #176a51; margin-top: 8px; }
      @media (max-width: 520px) {
        #open { right: 12px; bottom: max(12px, env(safe-area-inset-bottom, 0px) + 8px); width: 46px; height: 46px; min-height: 46px; padding: 0; border-radius: 50%; gap: 0; justify-content: center; }
        #open .bug-icon { font-size: 20px; line-height: 1; }
        #open .bug-label { position: absolute; width: 1px; height: 1px; padding: 0; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }
        #shade { padding: 10px; align-items: flex-end; }
        #dialog { width: 100%; padding: 19px; border-radius: 16px 16px 10px 10px; max-height: 89dvh; }
      }
      @media (prefers-reduced-motion: reduce) { * { scroll-behavior: auto !important; } }
    </style>
    <button id="open" type="button" aria-haspopup="dialog" aria-controls="dialog" aria-label="Report a bug" title="Report a bug">
      <span class="bug-icon" aria-hidden="true">⚑</span> <span class="bug-label">Report a bug</span>
    </button>
    <div id="shade" hidden>
      <section id="dialog" role="dialog" aria-modal="true" aria-labelledby="heading" aria-describedby="intro" tabindex="-1">
        <div class="top">
          <h2 id="heading">Report a bug</h2>
          <button id="close" type="button" class="close" aria-label="Close bug report">×</button>
        </div>
        <p id="intro" class="sub">Tell us what went wrong. We'll include this page's address so the issue is easier to reproduce.</p>
        <form id="form">
          <label for="category">Type of issue</label>
          <select id="category" name="category">
            <option>Broken button, navigation or page</option>
            <option>Incorrect or missing data</option>
            <option>Chart or visualization problem</option>
            <option>Accessibility issue</option>
            <option>Other</option>
          </select>
          <label for="summary">Short summary *</label>
          <input id="summary" name="summary" type="text" maxlength="140" minlength="5" placeholder="e.g. Compare filters disappear after clicking" required>
          <label for="details">What happened? *</label>
          <textarea id="details" name="details" maxlength="4000" minlength="10" placeholder="Describe what you saw, including any error message." required></textarea>
          <label for="expected">What did you expect? (optional)</label>
          <textarea id="expected" name="expected" maxlength="2000" rows="2" style="min-height:70px" placeholder="What should have happened instead?"></textarea>
          <label for="steps">How can we reproduce it? (optional)</label>
          <textarea id="steps" name="steps" maxlength="2000" rows="2" style="min-height:70px" placeholder="1. Open ...  2. Tap ..."></textarea>
          <div class="actions">
            <button class="primary" type="submit">Continue to GitHub</button>
            <button id="copy" type="button" class="secondary">Copy report</button>
          </div>
          <p class="foot">GitHub sign-in is required to submit. Your report is <strong>not sent</strong> until you review and submit it there. You can add screenshots on GitHub. Reports are public: don't include private information.</p>
          <div id="status" role="status" aria-live="polite" class="status"></div>
        </form>
      </section>
    </div>
  `;
  var $ = function (selector) { return ui.querySelector(selector); };
  var shade = $("#shade");
  var launch = $("#open");
  var form = $("#form");
  var status = $("#status");
  var lastFocus = null;

  function openDialog() {
    lastFocus = document.activeElement;
    shade.hidden = false;
    launch.setAttribute("aria-expanded", "true");
    $("#summary").focus();
  }
  function closeDialog() {
    shade.hidden = true;
    launch.setAttribute("aria-expanded", "false");
    status.textContent = "";
    if (lastFocus && typeof lastFocus.focus === "function") lastFocus.focus();
    else launch.focus();
  }
  function reportText() {
    var val = function (id) { return $("#" + id).value.trim(); };
    // Never include URL query parameters (potential personal information).
    var pageUrl = window.location.origin + window.location.pathname;
    return [
      "## Page", pageUrl,
      "", "## Issue type", val("category"),
      "", "## What happened", val("details") || "(Not provided)",
      "", "## Expected behavior", val("expected") || "(Not provided)",
      "", "## Steps to reproduce", val("steps") || "(Not provided)",
      "", "## Additional context", "Submitted from the Power Atlas on-page bug report form."
    ].join("\n");
  }
  function issueUrl() {
    var title = "[Bug] " + $("#summary").value.trim();
    return "https://github.com/jbmeadows26/Power-Atlas/issues/new?title=" +
      encodeURIComponent(title) + "&body=" + encodeURIComponent(reportText());
  }
  launch.addEventListener("click", openDialog);
  $("#close").addEventListener("click", closeDialog);
  shade.addEventListener("click", function (event) {
    if (event.target === shade) closeDialog();
  });
  ui.addEventListener("keydown", function (event) {
    if (shade.hidden) return;
    if (event.key === "Escape") { event.preventDefault(); closeDialog(); return; }
    if (event.key !== "Tab") return;
    var focusable = Array.from(shade.querySelectorAll("button:not([disabled]), input, textarea, select"))
      .filter(function (element) { return !element.hidden; });
    if (!focusable.length) return;
    var first = focusable[0], last = focusable[focusable.length - 1];
    if (event.shiftKey && ui.activeElement === first) { event.preventDefault(); last.focus(); }
    else if (!event.shiftKey && ui.activeElement === last) { event.preventDefault(); first.focus(); }
  });
  form.addEventListener("submit", function (event) {
    event.preventDefault();
    if (!form.reportValidity()) return;
    // Deliberately open a user-confirmed GitHub issue instead of silently claiming submission.
    window.location.assign(issueUrl());
  });
  $("#copy").addEventListener("click", function () {
    if (!form.reportValidity()) return;
    var content = "[Bug] " + $("#summary").value.trim() + "\n\n" + reportText();
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(content).then(function () {
        status.textContent = "Report copied. You can paste it into a message.";
      }).catch(function () {
        status.textContent = "Copy was blocked by the browser. You can continue through GitHub.";
      });
    } else {
      status.textContent = "Clipboard is unavailable. You can continue through GitHub.";
    }
  });
})();
