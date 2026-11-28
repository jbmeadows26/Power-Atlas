import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {summarizeAcceptance} from '../site/development-control/acceptance-rules.mjs';

const registry=()=>JSON.parse(readFileSync(new URL('../site/development-control/acceptance.json',import.meta.url)));

test('control rules withhold current production when release identity is unavailable',()=>{
 const report=summarizeAcceptance(registry());
 assert.equal(report.currentRelease.status,'unavailable');
 assert.equal(Object.values(report.requirements).some(result=>result.complete),false);
 assert.ok(report.currentStates.Unavailable>0);
});

test('control rules distinguish current identity from stale functional evidence',()=>{
 const report=summarizeAcceptance(registry(),{status:'Verified',deployedCommit:'9'.repeat(40),source:'test-release-identity',artifact:'release-identity.json',carryForwardEvidence:[]});
 assert.equal(report.currentRelease.status,'verified');
 assert.ok(report.staleEvidence.includes('production-browser-18ebf114'));
 assert.equal(report.assessmentStates['EA-005:G09'].currentState,'Verified');
 assert.equal(report.assessmentStates['EA-005:G06'].currentState,'Stale');
});

test('control rules reject a modified mandatory-gate policy',()=>{
 const data=registry();data.mandatoryGatePolicy.gateIds=['G01'];
 assert.throws(()=>summarizeAcceptance(data),/mandatory-gate/);
});
