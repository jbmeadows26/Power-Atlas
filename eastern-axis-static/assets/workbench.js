(()=>{'use strict';
const $=id=>document.getElementById(id),esc=x=>String(x==null?'':x).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const validUrl=s=>{try{let u=new URL(s);return u.protocol==='https:'&& !u.username&&!u.password?u.href:null}catch{return null}};
const fmt=n=>Number(n||0).toLocaleString('en-US');const day=s=>{if(!s)return'Not recorded';let d=new Date(s);return Number.isNaN(d.getTime())?'Invalid timestamp':d.toLocaleString('en-US',{month:'short',day:'numeric',year:'numeric',hour:'2-digit',minute:'2-digit',timeZone:'UTC'})+' UTC'};
const label={ofac:'OFAC / Treasury',cisa:'CISA / NIST',fara:'DOJ FARA',doj:'Justice Department'};
let evidence=null,formal=null,tab='evidence',query='',origin='all',catalog=[],scope=null;
const savedScope=()=>{try{return localStorage.getItem('ea-country-focus-v1')||''}catch{return''}};
const scoped=()=>catalog.find(c=>c.iso===scope)||null;
function updateScope(){scope=savedScope();render();}
async function refresh(){const btn=$('wb-reload');if(btn)btn.disabled=true;$('wb-banner').textContent='Checking source status and formal publication gates…';
 const [a,b]=await Promise.allSettled([
  fetch('/api/evidence-workbench',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('collector '+r.status);return r.json()}),
  fetch('/api/collection-quality',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('formal review '+r.status);return r.json()})
 ]);
 evidence=a.status==='fulfilled'?a.value:null;formal=b.status==='fulfilled'?b.value:null;
 if(btn)btn.disabled=false;render();
}
function banner(){let parts=[];if(evidence)parts.push('Original collector online · checked '+day(evidence.generatedAt));else parts.push('Collector verification unavailable');if(formal)parts.push('Formal review registry online · '+fmt(formal.metrics?.records)+' records');else parts.push('Formal review registry unavailable');const el=$('wb-banner');el.classList.toggle('warning',!evidence||!formal);el.textContent=parts.join(' · ');}
function stat(k,n,sub){return '<article class="wb-stat"><small>'+esc(k)+'</small><strong>'+esc(n)+'</strong><p>'+esc(sub)+'</p></article>'}
function stats(){let m=evidence?.metrics||{},q=formal?.metrics||{};let items=[
 ['INDEXED SOURCE LEADS',evidence?fmt(m.indexedReferences):'—','Collector bounded sample'],
 ['FORMALLY REVIEWED',formal?fmt(q.reviewed)+' / '+fmt(q.records):'—','Human review required'],
 ['WARC RECORDS',evidence?fmt(m.warcRecords):'—','Managed storage, not Object Lock'],
 ['ZERO-MATCH CHECKS',evidence?fmt(m.zeroMatchChecks):'—','Negative findings logged'],
 ['PUBLISHED FINDINGS',formal?fmt(q.published):'—','Released by review gate']
 ];$('wb-stats').innerHTML=items.map(t=>stat(...t)).join('')}
function controls(){let scopeCountry=scoped();let headline=scopeCountry?'Country scope: '+scopeCountry.name+' ('+scopeCountry.alpha2+')':'Global / regional scope';
 let el=$('wb-controls');
 if(tab==='evidence')el.innerHTML='<input id="wb-search" aria-label="Search raw evidence" placeholder="Search source, title or record…" value="'+esc(query)+'"><select id="wb-source" aria-label="Filter source"><option value="all">All source families</option>'+['doj','cisa','fara','ofac'].map(s=>'<option value="'+s+'"'+(origin===s?' selected':'')+'>'+esc(label[s])+'</option>').join('')+'</select>';
 else el.innerHTML='<p class="wb-note">'+esc(headline)+' · Source health is global; country tagging is only applied to matching source references.</p>';
 $('wb-search')?.addEventListener('input',e=>{query=e.target.value;renderResults();});
 $('wb-source')?.addEventListener('change',e=>{origin=e.target.value;renderResults();});
}
function card(r){let link=validUrl(r.sourceUrl),corroborated=r.independentConfirmation===true;
 return '<article class="wb-card"><div class="wb-meta"><span>'+esc(label[r.sourceId]||r.sourceId)+' · '+esc(r.date)+'</span><span class="wb-pill">'+esc(r.reviewState||'unreviewed')+'</span></div><h3>'+esc(r.title)+'</h3><p>'+esc(r.summary)+'</p><div class="wb-field"><span>Country relationship</span><b>'+esc(r.countryCode?'Lexical '+r.countryCode+' mention':'Unattributed')+'</b></div><div class="wb-field"><span>Independent confirmation</span><b>'+(corroborated?'Reviewed':'Not established')+'</b></div><div class="wb-field"><span>Origin group</span><b>'+esc(r.originGroup||r.sourceId)+'</b></div><details><summary>Inspect source lineage and reference hash</summary><p>Shared normalized text: '+fmt(r.syndicationCopies)+' copies across '+fmt(r.distinctOriginGroups)+' publisher groups. Counts do not establish independence.</p><p class="wb-small">Reference SHA-256: <code>'+esc(r.referenceHash)+'</code></p><p class="wb-small">'+esc(r.geographicBasis)+'</p></details>'+(link?'<a href="'+esc(link)+'" target="_blank" rel="noopener noreferrer">Original public record ↗</a>':'')+'</article>';
}
function showEvidence(){if(!evidence){$('wb-results').innerHTML='<div class="wb-empty">Original collector unavailable; no source records or counts have been fabricated.</div>';return}
 const country=scoped();const a2=country?.alpha2||null;
 let rows=evidence.records.filter(r=>(!a2||r.countryCode===a2)&&(origin==='all'||r.sourceId===origin)&&[r.title,r.summary,r.sourceRecordId].join(' ').toLowerCase().includes(query.toLowerCase())).slice(0,80);
 let note=country?'Only records explicitly tagged '+country.name+' are shown. Untagged records remain in Global. This does not establish government attribution.':'Global mode includes records without country attribution.';
 $('wb-results').innerHTML='<p class="wb-note">'+esc(rows.length)+' source leads shown · '+esc(note)+'</p>'+(rows.length?'<section class="wb-grid">'+rows.map(card).join('')+'</section>':'<div class="wb-empty">No matching tagged source references. This is an evidence-coverage gap, not proof of no activity.</div>');
}
function showCaptures(){if(!evidence){$('wb-results').innerHTML='<div class="wb-empty">Evidence storage status unavailable.</div>';return}const ds=evidence.responseDigests||[];
 $('wb-results').innerHTML='<p class="wb-note">A WARC capture is a reconstructed public API response, not an independently authenticated linked document or legal write-once object. Failed and over-limit captures are not counted as stored.</p>'+(ds.length?'<section class="wb-grid">'+ds.map(d=>'<article class="wb-card"><div class="wb-meta"><span>'+esc(day(d.capturedAt))+'</span><span class="wb-pill '+(d.rawArchived?'good':'')+'">'+(d.rawArchived?'WARC stored':'Digest only')+'</span></div><h3>'+esc(d.sourceUrl)+'</h3><div class="wb-field"><span>Response bytes</span><b>'+fmt(d.bytes)+'</b></div><div class="wb-field"><span>Capture status</span><b>'+esc(d.archiveStatus||'unknown')+'</b></div><details><summary>SHA-256 checksums</summary><p>Body SHA-256: <code>'+esc(d.sha256)+'</code></p><p>WARC SHA-256: <code>'+esc(d.archiveSha256||'not preserved')+'</code></p></details></article>').join('')+'</section>':'<div class="wb-empty">No capture receipts yet. New scheduled collector runs will populate this ledger; previous runs were not backfilled.</div>');
}
function showCoverage(){let q=formal?.metrics||{},m=evidence?.metrics||{},runs=evidence?.collectionAttempts||[];
 const reviewRatio=q.records?Math.round(100*(q.reviewed||0)/q.records):0;
 let checks=[{name:'Formal human review',value:reviewRatio,note:fmt(q.reviewed||0)+' / '+fmt(q.records||0)+' records reviewed'},
 {name:'PIR assigned',value:q.records?Math.round(100*(q.pir_assigned||0)/q.records):0,note:fmt(q.pir_assigned||0)+' formal assignments'},
 {name:'Source reliability graded',value:q.records?Math.round(100*(q.reliability_graded||0)/q.records):0,note:fmt(q.reliability_graded||0)+' graded'},
 {name:'Information credibility graded',value:q.records?Math.round(100*(q.credibility_graded||0)/q.records):0,note:fmt(q.credibility_graded||0)+' graded'}];
 $('wb-results').innerHTML='<p class="wb-note">Formal quality gate: <b>'+esc(formal?'Connected':'Unavailable')+'</b> · Collection attempts: '+fmt(m.recordedCollectionAttempts)+' · Failures: '+fmt(m.failedChecks)+' · Zero-match: '+fmt(m.zeroMatchChecks)+'. These are source checks, not a global absence-of-threat index.</p>'+
 (formal?'<div class="wb-coverage">'+checks.map(c=>'<article><b>'+esc(c.name)+'</b><div class="wb-meta">'+esc(c.note)+'</div><div class="bar"><span style="width:'+Math.max(0,Math.min(100,c.value))+'%"></span></div></article>').join('')+'</div>':'<div class="wb-empty">Formal quality registry unavailable; review percentages are not substituted.</div>')+
 '<h2>Recent collection attempts</h2>'+(runs.length?'<div class="wb-grid">'+runs.slice(0,30).map(r=>'<article class="wb-card"><div class="wb-meta"><span>'+esc(r.sourceId)+' · '+esc(day(r.attemptedAt))+'</span><span class="wb-pill">'+esc(r.status==='failed'?'Failed':r.zeroMatches?'Zero matches':'Completed')+'</span></div><h3>'+fmt(r.examined)+' examined / '+fmt(r.matched)+' matched</h3><p>Newly indexed: '+fmt(r.inserted)+(r.failureReason?' · '+esc(r.failureReason):'')+'</p></article>').join('')+'</div>':'<div class="wb-empty">No new-format collection attempts yet. Existing daily source-status checks are tracked separately.</div>');
}
function showGraph(){let m=evidence?.metrics||{};
 $('wb-results').innerHTML='<div class="wb-graphic"><div class="wb-node"><strong>'+fmt(m.indexedReferences)+'</strong><em>Source references</em></div><div style="font-size:27px;color:#9fe7d6">→</div><div class="wb-node"><strong>'+fmt(m.observedReferenceEdges)+'</strong><em>Observed URL edges</em></div><div style="font-size:27px;color:#9fe7d6">≠</div><div class="wb-node"><strong>0</strong><em>Verified identity mergers</em></div></div><section class="wb-grid" style="margin-top:14px"><article class="wb-card"><h3>Layer 1 — deterministic reference links</h3><p>A collected record links to the URL that supplied its evidence. This does not establish ownership, common operators or foreign-government responsibility.</p></article><article class="wb-card"><h3>Layer 2 — attribution hypotheses</h3><p>Disabled until calibrated scoring, independent corroboration and accountable human approval are in place. No probabilistic link may silently promote into an observed fact.</p></article><article class="wb-card"><h3>Source lineage</h3><p>'+fmt(m.syndicationClusters)+' exact normalized-text groups in this bounded sample. A copied story does not become another independent witness.</p></article><article class="wb-card"><h3>Unknowns</h3><p>Shared hosting, repeated names and matching handles are investigative leads—not identity selectors or factual government connections.</p></article></section>';
}
function renderResults(){if(tab==='evidence')showEvidence();else if(tab==='captures')showCaptures();else if(tab==='coverage')showCoverage();else showGraph();}
function render(){if(!$('wb-banner'))return;banner();stats();controls();renderResults();
 let q=formal?.sourceCounts||[],s=$('wb-sources');s.innerHTML=q.length?q.map(x=>'<div class="wb-source-row"><span>'+esc(label[x.source_id]||x.source_id)+'</span><b>'+fmt(x.count)+' records</b></div>').join(''):'<p class="wb-note">Formal source status unavailable.</p>';
 $('wb-limits').innerHTML=(evidence?.limitations||['Collector details unavailable; cannot confirm capture status.']).map(x=>'<p>'+esc(x)+'</p>').join('')+
 '<p>Source reviews and publication approvals are handled in a separate protected workflow. No unreviewed lead is labeled proven on this page.</p>';
 document.querySelectorAll('[data-tab]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.tab===tab)));
}
document.querySelectorAll('[data-tab]').forEach(b=>b.addEventListener('click',()=>{tab=b.dataset.tab;render()}));
$('wb-reload').addEventListener('click',refresh);
addEventListener('ea-country-set',e=>{scope=e.detail?.iso||'';render()});
addEventListener('storage',e=>{if(e.key==='ea-country-focus-v1')updateScope()});
fetch('/data/ea-country-catalog.json').then(r=>r.json()).then(d=>{catalog=d.countries||[];updateScope()}).catch(()=>{catalog=[];render()});
refresh();
})();