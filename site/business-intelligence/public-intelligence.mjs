// Read-only public demonstrations and operational coverage. No private profile API.
export async function mountPublicIntelligence(mount){
 const node=(tag,text)=>{const n=document.createElement(tag);if(text)n.textContent=text;return n;};
 const section=node('section');section.id='public-business-case';section.className='panel';mount.append(section);
 section.append(node('h2','See the dependency-to-decision workflow'));
 const status=node('p','Loading attributable public case…');section.append(status);
 try{
  const response=await fetch('./data/public-case.json',{credentials:'omit'});if(!response.ok)throw Error();const c=await response.json();
  if(c.schemaVersion!==1||!c.source||!Array.isArray(c.options))throw Error();
  status.textContent=c.caseType;section.append(node('h3',c.title));
  const chain=node('ol');for(const [title,text] of [['Public dependency',`${c.dependency.company} → ${c.dependency.products.join(' / ')} → ${c.dependency.facility}`],['External observation',c.observation],['Supported implication',c.implication]]){const li=node('li');li.append(node('strong',title),node('p',text));chain.append(li);}section.append(chain);
  const source=node('a','Read the original Apple statement');const u=new URL(c.source.url);if(u.protocol!=='https:')throw Error();source.href=u.href;source.rel='noopener noreferrer';section.append(source,node('p',`Published ${c.source.publicationDate} · Observation ${c.source.observationPeriod} · Retrieved ${c.source.retrievedAt}`));
  const label=node('label','Explore a management consideration '),select=node('select');select.setAttribute('aria-label','Public case management consideration');for(const o of c.options){const option=node('option',o.label);option.value=o.id;select.append(option);}label.append(select);const detail=node('div');detail.setAttribute('aria-live','polite');section.append(label,detail);
  const render=()=>{detail.replaceChildren();const o=c.options.find(x=>x.id===select.value);detail.append(node('p',o.consideration),node('p','Private inputs needed: '+o.inputs.join('; ')),node('p',o.tradeoff));};select.onchange=render;render();
  const limitations=node('details');limitations.append(node('summary','Evidence classification and limitations'),node('p',c.classification),node('p',`Source reliability: ${c.source.reliability}. Information credibility: ${c.source.credibility}.`));for(const text of c.limitations)limitations.append(node('p',text));section.append(limitations,node('p',c.isolation));
 }catch{status.textContent='Public case unavailable. No demonstration facts have been added to your business.';}
 const analysts=node('section');analysts.className='panel';analysts.id='analyst-operations';analysts.append(node('h2','Analyst execution and coverage'));mount.append(analysts);
 try{const response=await fetch('./data/analyst-registry.json',{credentials:'omit'});if(!response.ok)throw Error();const r=await response.json();if(r.analysts?.length!==18||r.schemaVersion!==2)throw Error();analysts.append(node('p',r.method));
  for(const a of r.analysts){const d=node('details'),last=(value)=>value?.recordedAt||'Unavailable';d.append(node('summary',`${a.name} · analysis ${a.analyticalStatus} · publication ${a.publicationStatus} · production ${a.productionVerificationStatus}`),node('p',a.responsibilities),node('p',`Last recorded successful analysis: ${last(a.lastSuccessfulAnalysis)}. Last recorded successful publication: ${last(a.lastSuccessfulPublication)}. Last production verification: ${last(a.lastProductionVerification)}.`),node('p',`Retained artifact generated: ${a.outputGeneratedAt||'Unavailable'}. ${a.outputGeneratedAtMeaning}`),node('p',a.dataFreshness),node('p',a.outputValidation),node('p',a.coverageLimitations.join(' ')));if(a.executionEvidence){const u=new URL(a.executionEvidence);if(u.protocol==='https:'&&u.hostname==='github.com'){const link=node('a','Recorded analysis evidence');link.href=u.href;link.rel='noopener noreferrer';d.append(link);}}analysts.append(d);}
 }catch{analysts.append(node('p','Analyst registry unavailable. No operational status inferred.'));}
}
