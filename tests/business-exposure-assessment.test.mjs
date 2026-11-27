import test from 'node:test';import assert from 'node:assert/strict';
import {analyze,validateProfile} from '../site/business-intelligence/engine.mjs';
import {createDecision,validateDecisions,updateDecisionStatus} from '../site/business-intelligence/decisions.mjs';
const now=Date.parse('2026-11-27T12:00:00Z');
const dep=id=>({id,name:'Shared label',country:'',product:'fuel',corridor:'',monthlyCost:null,twinPath:['supplier:a','product:b']});
const data={shortage:{forecasts:[{id:'fuel',status:'input-cost-watch',evidence:[{kind:'input-price',title:'Input benchmark',publisher:'Official source fixture',period:'2026-11-01',url:'https://example.org/observation',changePct:-8}]}]}};
const profile={type:'importer',dependencies:[dep('twin:a'),dep('twin:b')]};
test('same label distinct dependencies retain independent findings and approved paths',()=>{const r=analyze(data,profile,now);assert.equal(r.findings.length,4);for(const f of r.findings){assert.equal(f.classification,'Analytical assessment');assert.equal(f.materiality.amount,null);assert.ok(f.managementOptions.length);assert.ok(f.informationGaps.length);assert.deepEqual(f.relationshipPath,['supplier:a','product:b']);assert.equal(f.observationFreshness[0].state,'dated');}assert.equal(r.findings.filter(f=>f.kind==='opportunity').length,2);assert.throws(()=>validateProfile({...profile,dependencies:[{...dep('a'),twinPath:['<script>']}]}));});
test('insufficient or stale evidence does not manufacture opportunities',()=>{assert.equal(analyze({},profile,now).findings.length,0);assert.equal(analyze(data,profile,now+365*86400000).findings.length,0);});
test('decision state history and traceability preserve legacy compatibility',()=>{const finding=analyze(data,profile,now).findings[0],r=createDecision({finding,option:'Check quote',decidedAt:'2026-11-27'});assert.equal(r.finding.dependencyId,'twin:a');const accepted=updateDecisionStatus(r,'accepted','2026-11-28');const acted=updateDecisionStatus(accepted,'acted','2026-11-29');assert.equal(acted.statusHistory.length,3);assert.equal(validateDecisions([acted])[0].status,'acted');assert.throws(()=>updateDecisionStatus(acted,'deferred','2026-11-26'));assert.throws(()=>updateDecisionStatus(acted,'verified'));const legacy={...r};delete legacy.status;delete legacy.statusHistory;assert.equal(validateDecisions([legacy])[0].status,'considered');});

test('actual twin projection flows into analysis without losing declared path or evidence',async()=>{
 const {emptyTwin,addEntity,addRelationship,exposureProjection}=await import('../site/business-intelligence/twin.mjs');
 let twin=emptyTwin();twin=addEntity(twin,{id:'product-a',type:'product',name:'Finished product',origin:'declared',provenance:null});twin=addEntity(twin,{id:'supplier-a',type:'supplier',name:'Fuel supplier',origin:'declared',provenance:null,exposure:{country:'',product:'fuel',corridor:''}});twin=addRelationship(twin,{id:'edge-a',from:'product-a',to:'supplier-a',relation:'depends-on'});
 const projection=exposureProjection(twin);const findings=analyze(data,{type:'importer',dependencies:projection.dependencies},now).findings;
 const indirect=findings.find(f=>f.dependencyId==='twin:product-a');assert.ok(indirect);assert.deepEqual(indirect.relationshipPath,['product-a','supplier-a']);assert.equal(indirect.evidence[0].url,'https://example.org/observation');
 assert.ok(analyze({}, {type:'importer',dependencies:projection.dependencies},now).gaps.length);
});
