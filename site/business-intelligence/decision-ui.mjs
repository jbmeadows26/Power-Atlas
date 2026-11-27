import {createDecision,recordOutcome,validateDecisions,exportDecisions} from './decisions.mjs';
const el=(tag,value)=>{const n=document.createElement(tag);if(value!==undefined)n.textContent=value;return n;};
const field=(parent,name)=>{const label=el('label',name),input=el('textarea');input.maxLength=2000;label.append(input);parent.append(label);return input;};
export function setupDecisions(mount){
 let records=[];const status=el('p');status.setAttribute('role','status');
 function render(){
  const opened=new Set([...mount.querySelectorAll("details[open]")].map(n=>n.dataset.id));
  mount.replaceChildren(el('h2','Private decisions and outcomes'),el('p','User-reported records. Save the encrypted business profile to retain this journal. Export contains private plaintext; store it carefully.'),status);
  const download=el('button','Export decision journal');download.type='button';download.onclick=()=>{const url=URL.createObjectURL(new Blob([exportDecisions(records)],{type:'application/json'})),a=el('a');a.href=url;a.download='eastern-axis-private-decisions.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};mount.append(download);
  if(!records.length)mount.append(el('p','No decisions recorded. Open a matched finding to record your management choice.'));
  for(const record of records){const box=el('details'),summary=el('summary',record.option);box.dataset.id=record.id;box.open=opened.has(record.id);box.append(summary,el('p',record.decidedAt+' · '+(record.finding.dependency||'Business context')),el('p',record.finding.title),el('p',record.finding.detail));
   for(const evidence of record.finding.evidence){const link=el('a',evidence.label+' · '+evidence.source+' · '+evidence.date);link.href=evidence.url;link.target='_blank';link.rel='noopener noreferrer';box.append(link,el('br'));}
   for(const outcome of record.outcomes)box.append(el('p','User-reported · '+outcome.reportedAt+' · '+outcome.description));
   const outcome=field(box,'Outcome or operational change'),button=el('button','Record user-reported outcome');button.type='button';button.onclick=()=>{try{records=records.map(r=>r.id===record.id?recordOutcome(r,{description:outcome.value}):r);status.textContent='Outcome recorded locally. Save encrypted profile to persist.';render();}catch(e){status.textContent=e.message;}};box.append(button);mount.append(box);
  }
 }
 render();return {get:()=>validateDecisions(records),restore:value=>{records=validateDecisions(value);render();},reset:()=>{records=[];status.textContent='';render();},attach: (box,finding)=>{
  const choice=field(box,'Management choice considered or taken'),button=el('button','Record decision');button.type='button';const note=el('p');note.setAttribute('role','status');button.onclick=()=>{try{if(records.length>=100)throw Error('Decision limit reached.');records.push(createDecision({finding,option:choice.value}));choice.value='';note.textContent='Decision recorded locally. Save encrypted profile to persist.';render();}catch(e){note.textContent=e.message;}};box.append(button,note);
 }};
}
