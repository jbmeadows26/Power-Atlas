const STATES=['Verified','Partial','Failed','Pending','Not applicable','Blocked'];
const STAGES=['source','local','ci','deployed','production','commercial'];
const PRODUCTION_GATES=new Set(['G02','G05','G06','G07','G08']);
const fail=message=>{throw new Error(message);};
const require=(condition,message)=>{if(!condition)fail(message);};

export function normalizeReleaseContext(value){
 if(!value)return {status:'unavailable',reason:'No independently verified release context supplied.',carryForwardEvidence:new Set()};
 const status=String(value.status||'').toLowerCase();
 if(status==='unavailable')return {status,reason:value.reason||'Release context unavailable.',carryForwardEvidence:new Set()};
 require(status==='verified','Invalid release context status');
 const deployedCommit=value.deployedCommit||value.commit;
 require(/^[0-9a-f]{40}$/.test(deployedCommit||''),'Invalid deployed release commit');
 require(typeof value.source==='string'&&value.source,'Verified release context needs a source');
 require(typeof value.artifact==='string'&&value.artifact,'Verified release context needs an artifact');
 const carry=value.carryForwardEvidence||[];
 require(Array.isArray(carry)&&new Set(carry).size===carry.length,'Invalid carry-forward evidence');
 return {status,deployedCommit,source:value.source,artifact:value.artifact,carryForwardEvidence:new Set(carry)};
}

const currency=(evidence,context)=>{
 if(context.status!=='verified')return 'unavailable';
 if(evidence.commit===context.deployedCommit)return 'current';
 if(context.carryForwardEvidence.has(evidence.id)&&evidence.releaseScope?.policy==='unchanged-assets')return 'current-unchanged-scope';
 return 'stale';
};

export function summarizeAcceptance(data,releaseValue=null){
 const context=normalizeReleaseContext(releaseValue);
 require(data?.schema==='eastern-axis.acceptance.v2','Unsupported registry schema');
 require(JSON.stringify(data.states)===JSON.stringify(STATES),'Invalid canonical states');
 require(JSON.stringify(data.mandatoryGatePolicy)==='{"schema":"eastern-axis.mandatory-gates.v1","gateIds":["G01","G09"],"nonWaivable":true}','Invalid mandatory-gate policy');
 const evidence=new Map(data.evidence.map(item=>[item.id,item]));
 require(evidence.size===data.evidence.length,'Duplicate evidence IDs');
 const requirements=new Map(data.requirements.map(item=>[item.id,item]));
 require(requirements.size===20,'Invalid requirements');
 const states=Object.fromEntries(STATES.map(state=>[state,0]));
 const currentStates=Object.fromEntries([...STATES,'Stale','Unavailable'].map(state=>[state,0]));
 const criterionStates=Object.fromEntries(STATES.map(state=>[state,0]));
 const gateStates=Object.fromEntries(STATES.map(state=>[state,0]));
 const verifiedByStage={};
 const assessmentStates={};
 const evidenceCurrency=Object.fromEntries(data.evidence.map(item=>[item.id,currency(item,context)]));
 for(const requirement of data.requirements){
  require(requirement.criteria.length>0&&requirement.gates.length===11,'Invalid assessment records');
  for(const [kind,records] of [['criterion',requirement.criteria],['gate',requirement.gates]])for(const record of records){
   require(STATES.includes(record.state),'Invalid assessment state');
   require(Array.isArray(record.evidence)&&new Set(record.evidence).size===record.evidence.length,'Invalid assessment evidence');
   for(const id of record.evidence){require(evidence.has(id),'Unknown evidence reference');require(evidence.get(id).disposition?.class==='assessment','Assessment cannot use release-level evidence');}
   states[record.state]++;(kind==='criterion'?criterionStates:gateStates)[record.state]++;
   if(record.state==='Verified')verifiedByStage[record.stage]=(verifiedByStage[record.stage]||0)+1;
   const currencies=record.evidence.map(id=>evidenceCurrency[id]);
   let currentState=record.state;
   if(['Verified','Partial','Failed'].includes(record.state)){
    if(kind==='gate'&&record.id==='G09'&&record.state==='Verified')currentState=context.status==='verified'?'Verified':'Unavailable';
    else if(currencies.includes('unavailable'))currentState='Unavailable';
    else if(currencies.includes('stale'))currentState='Stale';
   }
   currentStates[currentState]++;
   assessmentStates[`${requirement.id}:${record.id}`]={state:record.state,currentState,stage:record.stage||null,evidenceCurrency:currencies};
  }
 }
 const results={};
 for(const requirement of data.requirements){
  const records=[...requirement.criteria,...requirement.gates],applicable=records.filter(record=>record.state!=='Not applicable');
  const contract=[];
  for(const record of requirement.criteria)if(record.state!=='Not applicable')contract.push([record,new Set(['production','commercial'])]);
  for(const gate of requirement.gates)if(gate.state!=='Not applicable'){
   if(PRODUCTION_GATES.has(gate.id))contract.push([gate,new Set(['production'])]);
   else if(gate.id==='G09')contract.push([gate,new Set(['deployed'])]);
  }
  const productionWorkflowVerified=contract.length>0&&contract.every(([record,stages])=>record.state==='Verified'&&stages.has(record.stage)&&assessmentStates[`${requirement.id}:${record.id}`].currentState==='Verified');
  const directBlockers=applicable.filter(record=>assessmentStates[`${requirement.id}:${record.id}`].currentState!=='Verified').map(record=>({assessmentId:record.id,state:record.state,currentState:assessmentStates[`${requirement.id}:${record.id}`].currentState,reason:record.reason||''}));
  results[requirement.id]={acceptanceSatisfied:applicable.length>0&&applicable.every(record=>record.state==='Verified'),currentAcceptanceSatisfied:applicable.length>0&&applicable.every(record=>assessmentStates[`${requirement.id}:${record.id}`].currentState==='Verified'),productionWorkflowVerified,continuous:Boolean(requirement.continuous),directBlockers,dependencyDerivedBlockers:[]};
 }
 const ready=(id,active=new Set())=>{
  if(active.has(id))return false;
  const requirement=requirements.get(id),result=results[id],next=new Set(active);next.add(id);
  return result.currentAcceptanceSatisfied&&result.productionWorkflowVerified&&requirement.dependencies.every(dependency=>ready(dependency,next));
 };
 for(const requirement of data.requirements){
  results[requirement.id].dependencyDerivedBlockers=requirement.dependencies.filter(dependency=>!ready(dependency));
  results[requirement.id].releaseReady=ready(requirement.id);
  results[requirement.id].complete=results[requirement.id].releaseReady&&!results[requirement.id].continuous;
 }
 const countValues=object=>Object.values(object).reduce((a,b)=>a+b,0);
 return {
  schema:'eastern-axis.acceptance-summary.v2',
  currentRelease:Object.fromEntries(Object.entries(context).filter(([key])=>key!=='carryForwardEvidence')),
  states,currentStates,criterionStates,gateStates,verifiedByStage,
  verifiedAcceptanceRecords:states.Verified,
  currentVerifiedAcceptanceRecords:currentStates.Verified,
  currentProductionVerifiedRecords:Object.values(assessmentStates).filter(detail=>detail.currentState==='Verified'&&['deployed','production','commercial'].includes(detail.stage)).length,
  applicableAcceptanceRecords:countValues(states)-states['Not applicable'],notApplicableRecords:states['Not applicable'],
  evidenceCurrency,staleEvidence:Object.keys(evidenceCurrency).filter(id=>evidenceCurrency[id]==='stale').sort(),assessmentStates,requirements:results
 };
}
