/* Consumer Class Actions visual story: strictly derived from reviewed case ledger. */
(function(){
"use strict";
function byId(id){return document.getElementById(id)}
function el(tag,className,txt){
  var node=document.createElement(tag);
  if(className)node.className=className;
  if(txt!==undefined)node.textContent=String(txt);
  return node;
}
function prettyDate(iso){
  if(!/^\d{4}-\d{2}-\d{2}$/.test(iso||""))return "Date not verified";
  return new Date(iso+"T12:00:00Z").toLocaleDateString("en-US",{month:"short",day:"numeric",year:"numeric",timeZone:"UTC"});
}
function render(data){
  if(!data||!Array.isArray(data.cases)||data.schema!=="power-atlas.consumer-class-actions.v1")return;
  var cases=data.cases.filter(function(c){return c && typeof c.company==="string" && typeof c.id==="string"});
  var open=cases.filter(function(c){return c.claimStatus==="open-as-of-review"});
  var notReported=cases.length-open.length;
  if(byId("caTotal"))byId("caTotal").textContent=String(cases.length);
  if(byId("caReportedOpen"))byId("caReportedOpen").textContent=String(open.length);
  if(byId("caOtherCount"))byId("caOtherCount").textContent=String(notReported);
  if(byId("caAsOf"))byId("caAsOf").textContent="Reviewed "+prettyDate(data.asOf);
  if(byId("caDonut"))byId("caDonut").style.setProperty("--ca-percent",String(cases.length?Math.round(open.length*100/cases.length):0));
  var list=byId("caDeadlineTimeline");
  if(!list)return;
  list.replaceChildren();
  if(!open.length){
    list.appendChild(el("p","ca-empty","No claim windows were confirmed as open at the last source review. Check official settlement notices for the latest status."));
    return;
  }
  open.slice().sort(function(a,b){return String(a.deadline||"9999").localeCompare(String(b.deadline||"9999"))})
      .forEach(function(c){
    var item=el("button","ca-deadline-row");
    item.type="button";
    item.setAttribute("aria-controls","caseList");
    item.setAttribute("aria-label","Find "+c.company+" case details, deadline "+prettyDate(c.deadline));
    var date=el("time","");
    date.dateTime=/^\d{4}-\d{2}-\d{2}$/.test(c.deadline||"")?c.deadline:"";
    var m=/^\d{4}-(\d{2})-(\d{2})$/.exec(c.deadline||"");
    if(m){
      date.appendChild(el("small","",new Date(c.deadline+"T12:00:00Z").toLocaleDateString("en-US",{month:"short",year:"numeric",timeZone:"UTC"})));
      date.appendChild(el("strong","",String(Number(m[2]))));
    }else{date.appendChild(el("strong","","—"));}
    var copy=el("div","");
    copy.appendChild(el("b","",c.company));
    copy.appendChild(el("span","",c.issue||"Class-action settlement"));
    item.appendChild(date);item.appendChild(copy);item.appendChild(el("span","ca-go","View case →"));
    item.addEventListener("click",function(){
      var input=byId("q"),industry=byId("industry"),claim=byId("claim");
      if(!input||!industry||!claim)return;
      industry.value="all";claim.value="all";input.value=c.company;
      input.dispatchEvent(new Event("input",{bubbles:true}));
      var region=byId("cases");
      if(region)region.scrollIntoView({behavior:window.matchMedia&&window.matchMedia("(prefers-reduced-motion:reduce)").matches?"auto":"smooth",block:"start"});
      input.focus({preventScroll:true});
    });
    list.appendChild(item);
  });
}
function onData(event){render(event.detail)}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",start,{once:true});
else start();
function start(){
  document.addEventListener("poweratlas:class-actions-loaded",onData);
  if(window.__powerAtlasClassActions)render(window.__powerAtlasClassActions);
}
})();
