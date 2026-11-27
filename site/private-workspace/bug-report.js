/* Private workspace feedback: no automatic capture, storage or transmission. */
(function(){
 "use strict";
 const mount=document.getElementById("private-feedback");
 if(!mount)return;
 const make=(tag,text)=>{const e=document.createElement(tag);if(text)e.textContent=text;return e;};
 const launch=make("button","Report a bug");launch.type="button";
 const dialog=make("dialog");dialog.setAttribute("aria-labelledby","private-feedback-title");
 const title=make("h2","Report a bug");title.id="private-feedback-title";
 const note=make("p","Describe the issue without names, account details, supplier data or document contents. The report stays on this device unless you choose to share it.");
 const label=make("label","Issue description");const details=make("textarea");details.id="private-feedback-details";details.maxLength=2000;details.rows=5;label.htmlFor=details.id;
 const actions=make("div");actions.className="private-feedback-actions";
 const copy=make("button","Copy report"),download=make("button","Download report"),close=make("button","Close");
 for(const x of [copy,download,close]){x.type="button";actions.append(x);}
 const status=make("p");status.setAttribute("role","status");
 dialog.append(title,note,label,details,actions,status);mount.append(launch,dialog);
 const report=()=>["Workspace bug report","Page: "+location.origin+location.pathname,"","Description:",details.value.trim()].join("\n");
 launch.addEventListener("click",()=>{dialog.showModal();details.focus();});
 close.addEventListener("click",()=>dialog.close());
 dialog.addEventListener("close",()=>{details.value="";status.textContent="";launch.focus();});
 copy.addEventListener("click",async()=>{if(!details.value.trim()){status.textContent="Enter a description first.";return;}try{await navigator.clipboard.writeText(report());status.textContent="Copied locally. Review before sharing.";}catch{status.textContent="Clipboard unavailable. Use Download report.";}});
 download.addEventListener("click",()=>{if(!details.value.trim()){status.textContent="Enter a description first.";return;}const url=URL.createObjectURL(new Blob([report()],{type:"text/plain;charset=utf-8"})),a=make("a");a.href=url;a.download="workspace-bug-report.txt";a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);status.textContent="Prepared local report. Review before sharing.";});
})();
