(()=>{"use strict";
const URL="https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/main/data/service-accountability/service-access-v1.json";
const $=id=>document.getElementById(id);
const esc=x=>String(x??"").replace(/[&<>"']/g,ch=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]));
const number=n=>Number(n).toLocaleString("en-US");
const link=(href,label)=>'<a href="'+esc(href)+'" target="_blank" rel="noopener noreferrer">'+esc(label)+' ↗</a>';
const box=(n,title,subtitle)=>'<article class="sa-kpi"><div class="sa-big">'+esc(n)+'</div><strong>'+esc(title)+'</strong><small>'+esc(subtitle)+'</small></article>';
const line=(label,value,desc)=>'<div class="sa-line"><span>'+esc(label)+'</span><strong>'+esc(value)+'</strong><small>'+esc(desc)+'</small></div>';
const fmtGbp=n=>"£"+Number(n).toFixed(1)+"m";

const surveyBar=(label,value)=>'<div class="sa-bar-group"><div class="sa-bar-head"><span>'+esc(label)+'</span><strong>'+esc(value)+'%</strong></div><div class="sa-bar-track" role="img" aria-label="'+esc(label+': '+value+' percent of surveyed service leaders')+'"><span class="sa-bar-fill" style="width:'+Math.max(0,Math.min(100,Number(value)))+'%"></span></div></div>';
const staffPair=(label,prev,curr)=>{
 const max=Math.max(1,Number(prev),Number(curr));
 const series=(year,n,cls)=>'<div class="sa-bar-group"><div class="sa-bar-head"><span>'+esc(year)+'</span><strong>'+esc(number(n))+'</strong></div><div class="sa-bar-track" role="img" aria-label="'+esc(label+', '+year+': '+number(n))+'"><span class="sa-bar-fill '+cls+'" style="width:'+(100*Number(n)/max).toFixed(2)+'%"></span></div></div>';
 return '<div class="sa-group-heading">'+esc(label)+'</div>'+series('2024',prev,'')+series('2025',curr,'sa-bar-lime');
};

let record=null;
const problemNotes={
 "General customer service":"The firsthand caller said the general menu redirected toward SMS/self-service rather than offering an explicit representative route. This is a reported customer experience, not independently observed call evidence.",
 "Lost baggage":"The caller reported the same problem while exploring baggage options. Whether a separate staffed baggage channel is available has not been established.",
 "Wheelchair assistance":"The caller reported no representative option under wheelchair-assistance choices. Separate U.S. airport CRO obligations must be tested during airline operating hours; no violation is established."
};
function render(data){
 const c=data.case, g=c.companyDisclosure, s=data.sample, b=data.labor;
 $("saTop").innerHTML=
  box(s.organizationsWithAIAttributedAgentCutsPercent+"%","Surveyed organizations reporting AI-related agent reductions","Gartner · "+number(s.sampleSize)+" service leaders · July–August 2026")+
  box(s.meanWorkforceReductionAmongCuttersPercent+"%","Average workforce reduction among those reporting AI cuts","Conditional subgroup only—not the entire sample")+
  box(b.projectedChangePercent+"%","Projected U.S. customer-service employment change",b.baseYear+"–"+b.projectedYear+" · BLS projection, not realized AI layoffs");
 $("saSurveyChart").innerHTML=
  surveyBar("AI-related human agent cuts",s.organizationsWithAIAttributedAgentCutsPercent)+
  surveyBar("Rehired after earlier cuts",s.rehiredAfterPriorReductionsPercent)+
  surveyBar("Planning to rehire",s.planToRehireNext18MonthsPercent);
 $("saScope").textContent=data.scope;
 $("saSurvey").textContent="Also: "+s.rehiredAfterPriorReductionsPercent+"% reported rehiring previously cut staff and "+s.planToRehireNext18MonthsPercent+"% planned to rehire. "+s.footnote;
 $("saWork").innerHTML=
   line(b.baseYear+" employment",number(b.baseEmployment),"BLS national occupational estimate")+
   line(b.projectedYear+" employment",number(b.projectedEmployment),"BLS projection, not a current count")+
   line("Projected annual openings",number(b.expectedAnnualOpenings),"Mainly replacement demand");
 $("saContact").innerHTML='<strong>'+esc(c.published.phone)+'</strong><span>'+esc(c.published.availability)+'</span>'+link(c.published.source,"Virgin Atlantic source page");
 $("saReport").textContent=c.reported.description;
 const moneyRows=[
  ["Year-end employees",number(g.totalHeadcount2024),number(g.totalHeadcount2025)],
  ["Reservations / sales / retail FTE",number(g.reservationsSalesRetailFte2024),number(g.reservationsSalesRetailFte2025)],
  ["Companywide FTE",number(g.totalGroupFte2024),number(g.totalGroupFte2025)],
  ["Statutory loss",fmtGbp(g.statutoryLossGbpM2024),fmtGbp(g.statutoryLossGbpM2025)],
  ["Aggregate directors' remuneration",fmtGbp(g.directorsRemunerationGbpM2024),fmtGbp(g.directorsRemunerationGbpM2025)]
 ];
 $("saFinancial").innerHTML=moneyRows.map(r=>'<tr><th scope="row">'+esc(r[0])+'</th><td>'+esc(r[1])+'</td><td>'+esc(r[2])+'</td></tr>').join("");
 $("saWorkforceChart").innerHTML=
  staffPair("Year-end employees",g.totalHeadcount2024,g.totalHeadcount2025)+
  staffPair("Reservations / sales / retail FTE",g.reservationsSalesRetailFte2024,g.reservationsSalesRetailFte2025);
 $("saFinanceNotes").textContent=g.limitations+" "+g.directorContext;
 $("saOwner").textContent=g.ownerDisclosure;
 $("saAnnual").innerHTML=link(g.source,"2025 annual report (primary source)");
 $("saChecks").innerHTML=c.audit.map(a=>'<article class="sa-audit"><span class="sa-tag">Pending verification</span><h3>'+esc(a.question)+'</h3><p>'+esc(a.method)+'</p><small>'+esc(a.status)+'</small></article>').join("");
 $("saUnknown").innerHTML=c.notEstablished.map(x=>"<li>"+esc(x)+"</li>").join("");
 $("saPaths").innerHTML=data.pathways.map(p=>'<article class="sa-path"><h3>'+esc(p.title)+'</h3><p>'+esc(p.description)+'</p>'+link(p.url,"Official resource")+'</article>').join("");
 $("saSources").innerHTML=[
  {title:"Virgin Atlantic official customer contacts",url:c.published.source},
  {title:"Virgin Atlantic annual report 2025, Note 7",url:g.source},
  {title:"Gartner survey · 5 November 2026",url:s.source},
  {title:"BLS occupational employment projections",url:b.source},
  {title:"U.S. DOT on airline CRO availability",url:c.legal.rightsSource},
  {title:"U.S. DOT passenger complaint process",url:c.legal.complaintSource}
 ].map(p=>'<li>'+link(p.url,p.title)+'</li>').join("");
 $("saRules").innerHTML=data.methodology.measures.map(t=>'<li>'+esc(t)+'</li>').join("");
 $("saCaseStatus").textContent=c.established+" "+c.reported.evidenceLevel+".";
 $("saAsOf").textContent="Source review: "+data.asOf;
 $("saLegal").textContent=c.legal.summary;
 $("saDisclosure").textContent=data.methodology.noCompositeScore;
 $("saQuestions").addEventListener("change",e=>{$("saProblem").textContent=problemNotes[e.target.value]||"";});
 $("saQuestions").value="General customer service";
 $("saProblem").textContent=problemNotes[$("saQuestions").value];
 $("saStatus").textContent="Source-backed evidence loaded; live IVR and individual service outcomes remain unverified.";
}
(async()=>{
 try{
  const response=await fetch(URL,{cache:"no-store"});
  if(!response.ok)throw Error("research source HTTP "+response.status);
  const data=await response.json();
  if(data.schema!=="power-atlas.service-accountability.v1"||!data.case||!data.sample||!data.labor)throw Error("unexpected evidence schema");
  record=data;
  render(data);
 }catch(e){
  $("saStatus").textContent="The evidence feed is unavailable ("+e.message+"). See the official sources below; no missing company measurements have been invented.";
  $("saSources").innerHTML=
   "<li>"+link("https://www.virginatlantic.com/en-US/contact-us","Official Virgin Atlantic contacts")+"</li>"+
   "<li>"+link("https://corporate.virginatlantic.com/content/dam/corporate/annual-reports/Virgin-Atlantic-Annual-Report-2025.pdf","Virgin Atlantic annual report")+"</li>"+
   "<li>"+link("https://www.transportation.gov/airconsumer/complaint-process","DOT consumer complaint guidance")+"</li>";
 }
})();
})();
