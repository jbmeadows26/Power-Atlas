const root=document.querySelector('#requirements'), summary=document.querySelector('#summary');
const node=(tag,text)=>{const el=document.createElement(tag);el.textContent=text;return el;};
try {
 const response=await fetch('./acceptance.json',{cache:'no-store'});
 if(!response.ok)throw new Error('Registry unavailable');
 const data=await response.json();
 if(data.schema!=='eastern-axis.acceptance.v1')throw new Error('Unsupported registry');
 const records=data.requirements.flatMap(r=>[...r.criteria,...r.gates]);
 const applicable=records.filter(r=>r.state!=='Not applicable');
 // Registry validation in CI is authoritative. The view never edits or persists progress.
 const verified=applicable.filter(r=>r.state==='Verified'&&r.evidence.length&&r.evidence.every(id=>data.evidence.some(e=>e.id===id&&e.result==='passed')));
 const outcomes=data.requirements.flatMap(r=>r.criteria), gates=data.requirements.flatMap(r=>r.gates);
 const production=verified.filter(r=>r.stage==='production');
 summary.textContent=`${outcomes.filter(r=>verified.includes(r)).length} verified customer outcomes / ${outcomes.length}; ${gates.filter(r=>verified.includes(r)).length} verified release assessments / ${gates.filter(r=>r.state!=='Not applicable').length} applicable. ${production.length} records verified in production. ${records.length-applicable.length} not applicable, separately excluded. CI evidence is commit-specific and does not establish production readiness.`;
 const render=()=>{
 root.replaceChildren();
 for(const r of data.requirements){
  const selected=document.querySelector('#filter').value;
  if(selected!=='all'&&![...r.criteria,...r.gates].some(c=>c.state===selected))continue;
  const details=node('details',''),heading=node('summary',`${r.id} · ${r.title} · ${r.priority}`);
  details.append(heading,node('p',`${r.phase}. Dependencies: ${r.dependencies.join(', ')||'None'}.${r.continuous?' Continuous obligation; never permanently complete.':''}`));
  for(const c of r.criteria)details.append(node('p',`${c.id} — ${c.state}: ${c.description}`));
  const list=node('ul','');
  for(const g of r.gates){const name=data.releaseGates.find(x=>x.id===g.id)?.name||g.id;list.append(node('li',`${name}: ${g.state} (${g.stage||'not verified'}). ${g.description||''} ${g.reason||''} Evidence: ${g.evidence.join(', ')||'None recorded'}`));}
  details.append(list);root.append(details);
 }
 };
 document.querySelector('#filter').addEventListener('change',render);render();
 const evidence=document.querySelector('#evidence');
 if(!data.evidence.length)evidence.append(node('p','No acceptance attestations recorded. Existing test files and merged commits do not automatically establish production verification.'));
 for(const e of data.evidence){const p=node('p',`${e.id}: ${e.result}; ${e.stage||e.scope}; ${e.executedAt}; commit ${e.commit}. ${e.limitations||''} `);try{const local=e.artifact.startsWith('site/development-control/evidence/')&&!e.artifact.includes('..');const url=new URL(local?e.artifact.replace('site/development-control/','./'):e.artifact,location.href);if(local||(url.protocol==='https:'&&url.hostname==='github.com')){const a=node('a','Execution evidence');a.href=url.href;a.rel='noopener noreferrer';p.append(a);}}catch{}evidence.append(p);}
}catch(error){summary.textContent='Acceptance registry unavailable or invalid. No readiness claim can be computed.';}
