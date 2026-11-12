/* Live source-linked Political Promises research view.
 * Reads archived official-source data products from the public GitHub main
 * branch and never labels selected provisional pledges as a fulfillment rate
 * or observational regressions as causal effects. No external JS libraries.
 */
(function(){
  'use strict';
  const BASE='https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/main/data/';
  const URLS={
    cases:BASE+'promises/research-feed.json',
    sentenceIndex:BASE+'promises/primary-2020-sentence-inventory/index.json',
    associations:BASE+'fiscal/state-timeseries/governor-election-fiscal-associations-2012-2024.json',
    fiscal:BASE+'fiscal/state-timeseries/aggregate-capital-2012-2024.json'
  };
  const $=id=>document.getElementById(id);
  const NS='http://www.w3.org/2000/svg';
  function num(n,d){return Number(n).toLocaleString(undefined,{minimumFractionDigits:d,maximumFractionDigits:d});}
  function text(id,v){const n=$(id);if(n)n.textContent=String(v);}
  function source(path){return 'https://github.com/jbmeadows26/Power-Atlas/blob/main/'+path;}
  async function fetchJSON(url){
    const response=await fetch(url,{cache:'no-store'});
    if(!response.ok)throw new Error('Source HTTP '+response.status);
    return response.json();
  }
  function addCell(row,content,heading){
    const n=document.createElement(heading?'th':'td');
    n.textContent=String(content);
    n.style.cssText='padding:9px 12px;border-bottom:1px solid #e1e7eb;white-space:nowrap;';
    row.appendChild(n);
  }
  function renderTable(models){
    const dest=$('promiseModelRows');
    if(!dest)return;
    dest.replaceChildren();
    const labels={
      all_fy_unadjusted:'All years · fixed effects',
      all_fy_lagged_macro:'All years · lagged macro',
      all_fy_macro_plus_contemporaneous_transfers_sensitivity:'Transfers sensitivity',
      pre_2022_unadjusted:'2012–2021 · fixed effects',
      pre_2022_lagged_macro:'2012–2021 · lagged macro',
      exclude_pandemic_fy2020_2021_macro:'Exclude 2020–21'
    };
    models.forEach(m=>{
      const election=m.coefficients.electionFiscalYear;
      const pre=m.coefficients.preElectionFiscalYear;
      const tr=document.createElement('tr');
      addCell(tr,labels[m.name]||m.name);
      addCell(tr,m.nObservedStateYears.toLocaleString());
      addCell(tr,(election.associationInPercentagePoints>=0?'+':'')+num(election.associationInPercentagePoints,3)+' pp');
      addCell(tr,'['+num(election.ci95[0],3)+', '+num(election.ci95[1],3)+']');
      addCell(tr,(pre.associationInPercentagePoints>=0?'+':'')+num(pre.associationInPercentagePoints,3)+' pp');
      addCell(tr,'['+num(pre.ci95[0],3)+', '+num(pre.ci95[1],3)+']');
      dest.appendChild(tr);
    });
  }
  function chart(models){
    const host=$('promiseCoefficientChart');
    if(!host)return;
    host.replaceChildren();
    const svg=document.createElementNS(NS,'svg');
    const w=780,h=54+models.length*57,l=135,r=26,top=38,bottom=35;
    const xmin=-.25,xmax=.75;
    const xp=n=>l+(n-xmin)/(xmax-xmin)*(w-l-r);
    svg.setAttribute('viewBox','0 0 '+w+' '+h);
    svg.setAttribute('aria-label','Election-year coefficient and 95% confidence interval for six observational models');
    svg.setAttribute('role','img');
    svg.style.cssText='display:block;width:100%;height:auto;min-width:450px;';
    const line=(x1,y1,x2,y2,stroke,width)=>{
      const e=document.createElementNS(NS,'line');
      for(const [k,v] of Object.entries({x1,y1,x2,y2,stroke,'stroke-width':width}))e.setAttribute(k,v);
      svg.appendChild(e);
    };
    const label=(x,y,value,anchor,size)=>{
      const e=document.createElementNS(NS,'text');
      e.setAttribute('x',x);e.setAttribute('y',y);e.setAttribute('text-anchor',anchor);
      e.setAttribute('font-size',size);e.setAttribute('fill','#486075');
      e.textContent=value;svg.appendChild(e);
    };
    [-.2,0,.2,.4,.6].forEach(v=>{
      const x=xp(v);line(x,top-17,x,h-bottom,'#dde6ee',1);
      label(x,h-13,(v>0?'+':'')+v.toFixed(1)+' pp','middle',12);
    });
    const abbreviations=['All, FE','All, macro','Transfers','Pre-2022, FE','Pre-2022, macro','No pandemic'];
    models.forEach((m,i)=>{
      const e=m.coefficients.electionFiscalYear, y=top+14+i*57;
      label(l-12,y+5,abbreviations[i]||m.name,'end',12);
      const a=xp(e.ci95[0]),b=xp(e.ci95[1]),x=xp(e.associationInPercentagePoints);
      line(a,y,b,y,'#287d89',3);line(a,y-6,a,y+6,'#287d89',2);line(b,y-6,b,y+6,'#287d89',2);
      const dot=document.createElementNS(NS,'circle');
      dot.setAttribute('cx',x);dot.setAttribute('cy',y);dot.setAttribute('r',5);
      dot.setAttribute('fill','#116c72');svg.appendChild(dot);
      const t=document.createElementNS(NS,'title');
      t.textContent=m.name+': '+num(e.associationInPercentagePoints,3)+' pp; 95% CI ['+num(e.ci95[0],3)+', '+num(e.ci95[1],3)+']';
      dot.appendChild(t);
    });
    host.appendChild(svg);
  }
  let running=false,finished=false;
  async function load(){
    if(running||finished)return;
    running=true;
    text('promiseStatus','Fetching live research evidence from the Power Atlas GitHub main branch…');
    const urls=[URLS.cases,URLS.sentenceIndex,URLS.associations,URLS.fiscal];
    try{
      const [pledges,docs,study,fiscal]=await Promise.all(urls.map(fetchJSON));
      if(pledges.schema!=='power-atlas.promise-research-feed.v1'||
         docs.schema!=='power-atlas.campaign-source-sentence-index-summary.v1'||
         study.schema!=='power-atlas.observed-state-election-associations.v1'||
         fiscal.schema!=='power-atlas.census-state-finance-aggregates.v1')throw new Error('Unexpected research feed version');
      if(pledges.inference.promiseFulfillmentRate!==null||
         study.causalEffect!==null||study.politicalIntentInference!==null)throw new Error('Research feed violates independence/causality safety contract');
      text('promiseCaseCount',pledges.coverage.scoredProvisionalCases);
      text('promiseReviewCount',docs.sourceSentenceTotal.toLocaleString());
      text('promiseStateYears',fiscal.coverage.stateYearObservations.toLocaleString());
      text('promiseModelCount',study.models.length);
      renderTable(study.models);chart(study.models);
      text('promiseStatus','Connected: '+docs.documentsIndexed+' primary election documents, '+docs.futureTenseCueTotal.toLocaleString()+' heuristic future-tense cues, '+study.models.length+' observed-data regression variants. Last retrieved '+new Date().toLocaleString()+'.');
      text('promisePledgeNotice','All '+pledges.coverage.scoredProvisionalCases+' scored examples are provisional, hand-selected case studies; '+pledges.coverage.unscoredCandidateQueue+' other candidates are unreviewed. No population fulfillment denominator or independent two-coder adjudication exists. A future-tense cue is not a verified pledge.');
      finished=true;
    }catch(e){
      text('promiseStatus','Live research evidence unavailable ('+e.message+'). The verified source links remain below; no unsupported result will be shown.');
    }finally{running=false;}
  }
  const tab=document.querySelector('[data-tab="campaign-promises"]');
  if(tab)tab.addEventListener('click',load);
  if(document.querySelector('[data-panel="campaign-promises"].active'))load();
})();
