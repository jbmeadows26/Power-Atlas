import test from 'node:test';import assert from 'node:assert/strict';
import {conditionalFinancialImplication,inventoryAssessment} from '../site/business-intelligence/engine.mjs';
const d={monthlyCost:10000,currency:'USD',amountOrigin:'declared'};
const assumption={changePct:-5,basis:'supplier-quote',reviewed:true};
test('financial implication requires reviewed explicit input and declared USD basis',()=>{
 const r=conditionalFinancialImplication(d,assumption);assert.equal(r.classification,'Scenario');assert.equal(r.monthly,-500);assert.equal(r.annual,-6000);assert.match(r.verification,/not independently verified/);
 for(const patch of [{currency:'EUR'},{currency:undefined},{monthlyCost:null},{amountOrigin:'extracted'},{amountOrigin:undefined}])assert.equal(conditionalFinancialImplication({...d,...patch},assumption),null);
 for(const patch of [{basis:'public-proxy'},{reviewed:false},{changePct:null}])assert.equal(conditionalFinancialImplication(d,{...assumption,...patch}),null);
 assert.equal(conditionalFinancialImplication({...d,monthlyCost:0},assumption).monthly,0);
});
test('inventory thresholds distinguish missing from zero and never establish stockout',()=>{
 const e={id:'stock-1',type:'inventory',origin:'approved-document',attributes:{quantity:0,reorderPoint:10,unit:'units'}};
 const r=inventoryAssessment(e);assert.equal(r.reviewRequired,true);assert.equal(r.unitsToThreshold,10);assert.match(r.limitations[0],/No stockout/);
 assert.equal(inventoryAssessment({...e,attributes:{quantity:10,reorderPoint:10,unit:'units'}}).unitsToThreshold,0);
 assert.equal(inventoryAssessment({...e,attributes:{quantity:null,reorderPoint:10,unit:'units'}}),null);
 assert.equal(inventoryAssessment({...e,attributes:{quantity:0,reorderPoint:10}}),null);
 assert.equal(inventoryAssessment({...e,origin:'extracted'}),null);assert.equal(inventoryAssessment({...e,archived:true}),null);
});
