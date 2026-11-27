import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createDecision,recordOutcome,validateDecisions,exportDecisions} from '../site/business-intelligence/decisions.mjs';
const finding={domain:'Cost',dependency:'Test material',title:'Test observation',status:'Review',detail:'Fixture only',action:'Obtain quote',evidence:[{label:'Fixture',source:'Test publisher',date:'2026-01',url:'https://example.org/observation'}]};
test('decision preserves evidence snapshot and user-reported outcome through export',()=>{
 const d=createDecision({finding,option:'Request quote',decidedAt:'2026-02-01'});finding.title='Changed source';assert.equal(d.finding.title,'Test observation');
 const done=recordOutcome(d,{description:'Quote received',amount:0,currency:'USD',reportedAt:'2026-02-02'});
 assert.equal(d.outcomes.length,0);assert.equal(done.outcomes[0].verification,'user-reported');assert.deepEqual(JSON.parse(exportDecisions([done])).decisions,[done]);
});
test('rejects invalid backup, duplicate ids, unsupported verification and invalid values',()=>{
 const d=createDecision({finding,option:'Review',decidedAt:'2026-02-01'});
 assert.throws(()=>validateDecisions([d,d]));assert.throws(()=>recordOutcome(d,{description:'Result',amount:NaN,currency:'USD'}));assert.throws(()=>recordOutcome(d,{description:'Result',reportedAt:'2026-01-01'}));
 const done=recordOutcome(d,{description:'Result'});done.outcomes[0].verification='independently-verified';assert.throws(()=>validateDecisions([done]));
 assert.throws(()=>createDecision({finding:{...finding,evidence:[]},option:'Review'}));
 assert.throws(()=>createDecision({finding:{...finding,evidence:[{...finding.evidence[0],url:'javascript:alert(1)'}]},option:'Review'}));
});
