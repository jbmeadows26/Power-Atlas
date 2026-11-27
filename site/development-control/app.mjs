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
 summary.textContent=`${verified.length} verified acceptance records / ${applicable.length} applicable. ${records.length-applicable.length} not applicable, separately excluded. Deployment identity is unverified unless supported by production evidence.`;
 const render=()=>{
 root.replaceChildren();
 for(const r of data.requirements){
  const selected=document.querySelector('#filter').value;
  if(selected!=='all'&&![...r.criteria,...r.gates].some(c=>c.state===selected))continue;
  const details=node('details',''),heading=node('summary',`${r.id} · ${r.title} · ${r.priority}`);
  details.append(heading,node('p',`${r.phase}. Dependencies: ${r.dependencies.join(', ')||'None'}.${r.continuous?' Continuous obligation; never permanently complete.':''}`));
  for(const c of r.criteria)details.append(node('p',`${c.id} — ${c.state}: ${c.description}`));
  const list=node('ul','');
  for(const g of r.gates){const name=data.releaseGates.find(x=>x.id===g.id)?.name||g.id;list.append(node('li',`${name}: ${g.state}. ${g.reason||''} Evidence: ${g.evidence.join(', ')||'None recorded'}`));}
  details.append(list);root.append(details);
 }
 };
 document.querySelector('#filter').addEventListener('change',render);render();
 const evidence=document.querySelector('#evidence');
 if(!data.evidence.length)evidence.append(node('p','No acceptance attestations recorded. Existing test files and merged commits do not automatically establish production verification.'));
 for(const e of data.evidence)evidence.append(node('p',`${e.id}: ${e.result}; ${e.scope}; ${e.executedAt}; commit ${e.commit}; artifact ${e.artifact}`));
}catch(error){summary.textContent='Acceptance registry unavailable or invalid. No readiness claim can be computed.';}
