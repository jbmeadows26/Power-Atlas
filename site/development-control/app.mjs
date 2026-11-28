import {summarizeAcceptance} from './acceptance-rules.mjs';

const root=document.querySelector('#requirements'),summary=document.querySelector('#acceptance-summary');
const node=(tag,text)=>{const element=document.createElement(tag);if(text!==undefined)element.textContent=text;return element;};
try {
 const [registryResponse,identityResponse]=await Promise.all([fetch('./acceptance.json',{cache:'no-store'}),fetch('../release-identity.json',{cache:'no-store'}).catch(()=>null)]);
 if(!registryResponse.ok)throw new Error('Registry unavailable');
 const data=await registryResponse.json();
 let releaseContext=null;
 if(identityResponse?.ok){
  const identity=await identityResponse.json();
  if(identity.schemaVersion===1&&identity.acceptanceContext?.deployedCommit===identity.commit)releaseContext=identity.acceptanceContext;
 }
 const report=summarizeAcceptance(data,releaseContext);
 const outcomes=data.requirements.flatMap(requirement=>requirement.criteria),gates=data.requirements.flatMap(requirement=>requirement.gates);
 const release=report.currentRelease.status==='verified'?`Current deployed identity ${report.currentRelease.deployedCommit.slice(0,12)} was detected from the content-addressed release manifest.`:'Current deployed identity is unavailable; current-production completion is withheld.';
 summary.textContent=`${report.criterionStates.Verified} historically verified customer outcomes / ${outcomes.length}; ${report.gateStates.Verified} historically verified release assessments / ${gates.filter(gate=>gate.state!=='Not applicable').length} applicable. ${report.currentProductionVerifiedRecords} production or deployment records are current for this release. ${report.currentStates.Stale} assessments are stale and ${report.currentStates.Unavailable} lack release context. ${release}`;
 const render=()=>{
  root.replaceChildren();
  for(const requirement of data.requirements){
   const selected=document.querySelector('#filter').value;
   if(selected!=='all'&&![...requirement.criteria,...requirement.gates].some(record=>record.state===selected||report.assessmentStates[`${requirement.id}:${record.id}`]?.currentState===selected))continue;
   const result=report.requirements[requirement.id],details=node('details'),heading=node('summary',`${requirement.id} · ${requirement.title} · ${requirement.priority}`);
   details.append(heading,node('p',`${requirement.phase}. Historical acceptance: ${result.acceptanceSatisfied?'satisfied':'incomplete'}. Current acceptance: ${result.currentAcceptanceSatisfied?'satisfied':'incomplete'}. Current production workflow: ${result.productionWorkflowVerified?'verified':'not verified'}. Dependencies: ${requirement.dependencies.join(', ')||'None'}.${requirement.continuous?' Continuous obligation; never permanently complete.':''}`));
   if(result.dependencyDerivedBlockers.length)details.append(node('p',`Dependency-derived blockers: ${result.dependencyDerivedBlockers.join(', ')}.`));
   for(const criterion of requirement.criteria){const current=report.assessmentStates[`${requirement.id}:${criterion.id}`].currentState;details.append(node('p',`${criterion.id} — recorded ${criterion.state}; current ${current}: ${criterion.description}`));}
   const list=node('ul');
   for(const gate of requirement.gates){const name=data.releaseGates.find(item=>item.id===gate.id)?.name||gate.id,current=report.assessmentStates[`${requirement.id}:${gate.id}`].currentState;list.append(node('li',`${name}: recorded ${gate.state}; current ${current} (${gate.stage||'not assessed'}). ${gate.description||''} ${gate.reason||''} Evidence: ${gate.evidence.join(', ')||'None recorded'}`));}
   details.append(list);root.append(details);
  }
 };
 document.querySelector('#filter').insertAdjacentHTML('beforeend','<option>Stale</option><option>Unavailable</option>');
 document.querySelector('#filter').addEventListener('change',render);render();
 const evidenceMount=document.querySelector('#evidence');
 if(!data.evidence.length)evidenceMount.append(node('p','No acceptance attestations recorded.'));
 for(const evidence of data.evidence){
  const currency=report.evidenceCurrency[evidence.id],classification=evidence.disposition?.class||'invalid';
  const paragraph=node('p',`${evidence.id}: ${evidence.result}; ${evidence.stage}; ${currency}; ${classification}; ${evidence.executedAt}; commit ${evidence.commit}. ${evidence.limitations||''} `);
  try{const local=evidence.artifact.startsWith('site/development-control/evidence/')&&!evidence.artifact.includes('..'),url=new URL(local?evidence.artifact.replace('site/development-control/','./'):evidence.artifact,location.href);if(local||(url.protocol==='https:'&&url.hostname==='github.com')){const link=node('a','Execution evidence');link.href=url.href;link.rel='noopener noreferrer';paragraph.append(link);}}catch{}
  evidenceMount.append(paragraph);
 }
}catch(error){summary.textContent='Acceptance registry or current-release context is invalid. No readiness claim can be computed.';}
