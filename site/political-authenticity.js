(function(){
'use strict';
var nav=document.querySelector('nav[role="tablist"]');
var first=document.querySelector('[data-panel]');
if(!nav||!first)return;
var btn=document.createElement('button');
btn.type='button'; btn.dataset.tab='authenticity';
btn.textContent='Political Authenticity';btn.setAttribute('role','tab');btn.setAttribute('aria-selected','false');
nav.appendChild(btn);
var panel=document.createElement('section');
panel.className='panel';panel.dataset.panel='authenticity';panel.setAttribute('role','tabpanel');
panel.id='political-authenticity-panel';
panel.innerHTML='<div class="eyebrow">Power Atlas / Research</div>'+
 '<h2>Political authenticity & representation</h2>'+
 '<p class="sub">Evidence-linked descriptive findings, experimental status, and unmeasured fields. Demographic distance is not proof of political dishonesty.</p>'+
 '<div id="paStatus" class="alert">Loading public source records…</div>'+
 '<div id="paMetrics" class="metrics"></div>'+
 '<div class="card"><h3>Evidence boundaries</h3><div id="paLimits">Loading source qualifications.</div></div>'+
 '<div class="card" style="margin-top:16px"><h3>Original sources</h3>'+
 '<p><a href="https://sda.berkeley.edu/sdaweb/docs/anes2024full/DOC/hcbk0040.htm" target="_blank" rel="noopener">ANES 2024 published response frequencies</a> · '+
 '<a href="https://data.census.gov/table/ACSSE2024.K200104" target="_blank" rel="noopener">2024 Census age population</a> · '+
 '<a href="https://github.com/jbmeadows26/Power-Atlas/tree/main/data/research/political-authenticity" target="_blank" rel="noopener">Source datasets and methods</a></p></div>';
first.parentNode.appendChild(panel);
var root='https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/main/data/research/political-authenticity/';
var loaded=false;
function text(id,value){var el=document.getElementById(id);if(el)el.textContent=value}
function metric(value,label){var div=document.createElement('div');div.className='metric';var b=document.createElement('b');b.textContent=value;var p=document.createElement('div');p.textContent=label;div.appendChild(b);div.appendChild(p);return div}
function get(file){return fetch(root+file,{cache:'no-store'}).then(function(r){if(!r.ok)throw Error('HTTP '+r.status);return r.json()})}
function render(){
  if(loaded)return;
  loaded=true;
  Promise.all([get('age-comparison.json'),get('coverage.json'),get('anes-2024-efficacy-aggregates.json')]).then(function(all){
    var a=all[0],c=all[1],q=all[2];
    if(a.schema!=='power-atlas.political-authenticity-age-descriptive.v1'||c.rosterTotal<500||q.questions.length!==2)throw Error('Unexpected source schema');
    var area=document.getElementById('paMetrics');area.textContent='';
    area.appendChild(metric(String(a.houseVotingAge25to34Count)+' / '+String(a.houseVotingCount),'Voting House members aged 25–34 ('+a.legislatorSnapshotDate+')'));
    area.appendChild(metric((100*a.populationAge25to34Share).toFixed(2)+'%','2024 U.S. resident population aged 25+ who are 25–34'));
    area.appendChild(metric(a.houseMinusPopulation25to34PercentagePoints.toFixed(2)+' pp','Descriptive age difference; mismatched years and eligibility'));
    q.questions.forEach(function(x){area.appendChild(metric((100*x.agreeShareValid).toFixed(1)+'%','Unweighted ANES valid-response agreement: '+x.variable))});
    text('paStatus','Public source files loaded. Birth dates '+c.ageKnown+'/'+c.rosterTotal+' (secondary source); member wealth and policy-responsiveness estimates not yet collected.');
    text('paLimits','RQ1: ANES item-level aggregates are measured but have no valid respondent-to-member join. RQ2: no human-coded communications or fielded factorial experiment. RQ3: roll-call data alone does not measure income-specific constituency preferences. IDI: synthetic calculations only; no real legislator score. No causal claim is established by this panel.');
  }).catch(function(e){loaded=false;text('paStatus','Source feed not available ('+e.message+'). Use the linked source datasets.');text('paLimits','Do not infer missing evidence as zero or a negative finding.');});
}
btn.addEventListener('click',function(){
 document.querySelectorAll('[data-tab]').forEach(function(x){x.setAttribute('aria-selected',String(x===btn))});
 document.querySelectorAll('[data-panel]').forEach(function(x){x.classList.toggle('active',x===panel)});
 render();
});
})();
