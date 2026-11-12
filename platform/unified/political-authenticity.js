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
 '<a href="https://www.census.gov/programs-surveys/acs/news/data-releases/2025/release.html" target="_blank" rel="noopener">2025 ACS release</a> · '+
 '<a href="https://github.com/jbmeadows26/Power-Atlas/tree/main/data/research/political-authenticity" target="_blank" rel="noopener">Source datasets and methods</a></p></div>';
panel.innerHTML += '<div class="card" style="margin-top:16px"><h3>Official 2025 House roll-call archive</h3>'+
  '<p class="sub">Primary-source XML votes for a bounded 2025 House roll-call window. Procedural Aye/No is normalized for search; Speaker election candidate selections are preserved separately. This is not a study of constituent preferences.</p>'+
  '<button id="paHouseLoad" type="button">Load official voting records</button>'+
  '<div class="filters" style="margin-top:12px"><input id="paHouseQuery" aria-label="Search roll number, bill, question or Bioguide ID" placeholder="Roll number, question, Bioguide ID…" /></div>'+
  '<p class="note" id="paHouseStatus">The voting archive is loaded only on request to conserve mobile data.</p>'+
  '<div class="list" id="paHouseList"></div></div>';
panel.innerHTML += '<div class="card" style="margin-top:16px"><div class="eyebrow">Financial disclosures / Source-backed research</div>'+
 '<h3>What lawmakers hold and trade</h3>'+
 '<p class="sub">Annual holdings and securities transactions are separate records. Public filings describe ranges, not exact personal wealth or investment gains.</p>'+
 '<div id="paFinanceStatus" class="note">Loading financial disclosure source coverage…</div>'+
 '<div id="paFinanceMetrics" class="metrics"></div>'+
 '<h3>Where the disclosed S&amp;P 500 holdings sit</h3><p class="note">2025 annual reports; source-derived percentages use midpoints of reported value bands, not exact dollars.</p>'+
 '<div id="paFinanceSectors"></div>'+
 '<p class="note" id="paFinanceCaveats"></p>'+
 '<p class="note"><a href="https://palanor.com/congress-trades/holdings" target="_blank" rel="noopener noreferrer">2025 annual holdings source</a> · '+
 '<a href="https://github.com/LuxAlgo/market-trackers-data" target="_blank" rel="noopener noreferrer">CC0 transaction source</a> · '+
 '<a href="https://disclosures-clerk.house.gov/FinancialDisclosure" target="_blank" rel="noopener noreferrer">House Clerk filings</a> · '+
 '<a href="https://www.ethics.senate.gov/public/index.cfm/financialdisclosure" target="_blank" rel="noopener noreferrer">Senate disclosure rules</a></p></div>';
first.parentNode.appendChild(panel);
var root='https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/main/data/research/political-authenticity/';
var loaded=false;
function text(id,value){var el=document.getElementById(id);if(el)el.textContent=value}
function metric(value,label){var div=document.createElement('div');div.className='metric';var b=document.createElement('b');b.textContent=value;var p=document.createElement('div');p.textContent=label;div.appendChild(b);div.appendChild(p);return div}
function get(file){return fetch(root+file,{cache:'no-store'}).then(function(r){if(!r.ok)throw Error('HTTP '+r.status);return r.json()})}
function render(){
  if(loaded)return;
  loaded=true;
  Promise.all([get('acs-2025-age-representation-comparison.json'),get('coverage.json'),get('anes-2024-efficacy-aggregates.json')]).then(function(all){
    var a=all[0],c=all[1],q=all[2];
    if(a.schema!=='power-atlas.political-authenticity.acs2025-age-representation-comparison.v1'||c.rosterTotal<500||q.questions.length!==2)throw Error('Unexpected source schema');
    var area=document.getElementById('paMetrics');area.textContent='';
    area.appendChild(metric(String(a.votingHouseMembersAge25to34)+' / '+String(a.votingHouseMembers),'Voting House members aged 25–34 ('+a.memberSnapshotDate+')'));
    area.appendChild(metric((100*a.populationAge25to34ShareOf25plus).toFixed(2)+'%','2025 ACS voting-district residents aged 25+ who are 25–34'));
    area.appendChild(metric(a.memberMinusResidentPercentagePoints.toFixed(2)+' pp','Descriptive age difference; 2025 residents vs October 2026 members; eligibility differs'));
    q.questions.forEach(function(x){area.appendChild(metric((100*x.agreeShareValid).toFixed(1)+'%','Unweighted ANES valid-response agreement: '+x.variable))});
    text('paStatus','2025 ACS data loaded for '+a.districts+' voting districts. '+a.votingHouseMembers+' occupied seats as of '+a.memberSnapshotDate+'. Birthdate verification incomplete; member wealth and controlled responsiveness remain unmeasured.');
    text('paLimits','RQ1: ANES item-level aggregates are measured but have no valid respondent-to-member join. RQ2: no human-coded communications or fielded factorial experiment. RQ3: roll-call data alone does not measure income-specific constituency preferences. IDI: synthetic calculations only; no real legislator score. No causal claim is established by this panel.');
  }).catch(function(e){loaded=false;text('paStatus','Source feed not available ('+e.message+'). Use the linked source datasets.');text('paLimits','Do not infer missing evidence as zero or a negative finding.');});
}
var officialRolls=null,officialRollBusy=false;
function renderHouseRolls(){
  var list=document.getElementById('paHouseList');
  if(!officialRolls){list.textContent='';return}
  var q=document.getElementById('paHouseQuery').value.trim().toLowerCase();
  var rows=officialRolls.filter(function(r){
    return !q || [r.rollCall,r.question,r.description,r.date,r.result].join(' ').toLowerCase().includes(q)||
      Object.prototype.hasOwnProperty.call(r.votes||{},q.toUpperCase());
  });
  text('paHouseStatus',rows.length+' of '+officialRolls.length+' source-verified roll calls in the bounded 2025 research archive. Search is not a claim of a complete Congress-wide voting history.');
  list.innerHTML=rows.slice(0,75).map(function(r){
    var counts=r.originalVoteLabelCounts||{},voteLabel=Object.keys(counts).sort().map(function(k){return k+': '+counts[k]}).join(' · ');
    var selected=q.match(/^[A-Z][0-9]{6}$/i)?(r.votes||{})[q.toUpperCase()]:null;
    var root='https://clerk.house.gov/evs/2025/roll'+String(r.rollCall).padStart(3,'0')+'.xml';
    return '<article class="card"><div class="meta"><span class="tag">Roll '+r.rollCall+'</span><span class="tag warn">'+(r.voteKind==='speaker_candidate_selection'?'Speaker choice':'Recorded roll call')+'</span></div>'+
      '<h3>'+String(r.question||'Official House question').replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})+'</h3>'+
      '<p>'+String(r.description||'').replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})+'</p><p>'+String(r.date||'')+' · '+String(r.result||'')+' · '+r.memberVotes+' member records</p>'+
      '<p class="note">Original Clerk labels: '+voteLabel.replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})+'</p>'+
      (selected?'<p><b>Selected Bioguide ID vote:</b> '+String(selected).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})+'</p>':'')+
      '<a class="source" href="'+root+'" target="_blank" rel="noopener noreferrer">Original House Clerk roll XML ↗</a></article>';
  }).join('') || '<p>No matching official roll calls are present in this bounded archive.</p>';
}
document.getElementById('paHouseQuery').addEventListener('input',renderHouseRolls);
document.getElementById('paHouseLoad').addEventListener('click',function(){
  if(officialRolls){renderHouseRolls();return}
  if(officialRollBusy)return;
  officialRollBusy=true;
  text('paHouseStatus','Loading bounded primary-source House voting archive...');
  get('house-rollcalls-2025.json').then(function(d){
    if(d.schema!=='power-atlas.house-official-rollcalls.v1'||!Array.isArray(d.records))throw Error('Vote source schema mismatch');
    officialRolls=d.records;
    renderHouseRolls();
  }).catch(function(e){text('paHouseStatus','Official roll-call archive could not be loaded: '+e.message)})
    .finally(function(){officialRollBusy=false});
});
var financeLoaded=false;
function loadFinance(){
  if(financeLoaded)return;
  financeLoaded=true;
  Promise.all([
    get('congress-holdings-2025-source-coverage.json'),
    get('congress-trades-source-audit-2026-11-05.json')
  ]).then(function(docs){
    var holdings=docs[0],trades=docs[1],area=document.getElementById('paFinanceMetrics');
    if(holdings.schema!=='power-atlas.political-authenticity.congress-holdings-coverage.v1'||
      trades.schema!=='power-atlas.political-authenticity.financial-activity-source-audit.v1')throw Error('Financial research schema mismatch');
    area.textContent='';
    area.appendChild(metric(String(holdings.membersWithSp500DirectSharesOrOptions)+' / '+String(holdings.readableMemberReports),
      '2025 reports with disclosed S&P 500 shares or options — readable reports only'));
    area.appendChild(metric((100*holdings.holderShareAmongReadableReports).toFixed(1)+'%',
      'Share of electronically read 2025 member reports; not all assets or all members'));
    area.appendChild(metric(String(holdings.paperScannedReportsUnparsed),
      '2025 scanned/paper reports not machine-read by holdings source'));
    area.appendChild(metric(String(trades.sample.transactionRows)+' / '+String(trades.sample.uniqueBioguideIDs),
      'Transaction rows / Senate filers in a STALE September 2026 daily delta'));
    var sectors=document.getElementById('paFinanceSectors');sectors.textContent='';
    holdings.sectorSummaries.slice(0,5).forEach(function(x){
      var row=document.createElement('div');row.className='coverage';
      var label=document.createElement('div');
      label.textContent=x.name+' — '+Number(x.midpointSharePct).toFixed(1)+'% of S&P 500 holding-band midpoints';
      var bar=document.createElement('div');bar.className='bar';
      var fill=document.createElement('div');fill.className='fill';
      fill.style.width=Math.max(0,Math.min(100,Number(x.midpointSharePct)))+'%';
      bar.appendChild(fill);row.appendChild(label);row.appendChild(bar);sectors.appendChild(row);
    });
    text('paFinanceStatus','2025 annual holdings: third-party aggregated evidence · Trading sample: '+trades.sourceManifestGeneratedAt.slice(0,10)+' (stale; NOT the latest filing universe).');
    text('paFinanceCaveats','These are NOT estimates of member net worth or proof of a conflict. S&P 500 shares/options exclude funds, bonds and private assets; multiple sectors may include the same member. The 58-row trade delta covers only 3 senators and cannot represent Congress. Spouse ownership, paper-report gaps and missing data are preserved.');
  }).catch(function(e){financeLoaded=false;text('paFinanceStatus','Financial evidence cannot be loaded: '+e.message);});
}
btn.addEventListener('click',function(){
 document.querySelectorAll('[data-tab]').forEach(function(x){x.setAttribute('aria-selected',String(x===btn))});
 document.querySelectorAll('[data-panel]').forEach(function(x){x.classList.toggle('active',x===panel)});
 render();
 loadFinance();
});
})();
