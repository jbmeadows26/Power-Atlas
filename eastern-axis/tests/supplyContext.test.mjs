import test from 'node:test';
import assert from 'node:assert/strict';
import {parseFed,selectValue} from '../backend/supplyContext.ts';

function dateLabel(d){
 const months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
 return String(d.getUTCDate()).padStart(2,'0')+'-'+months[d.getUTCMonth()]+'-'+d.getUTCFullYear();
}
function sampleCSV(){
 const rows=['Date,46296,46327'];
 // Nov 2017 through Oct 2026: enough historical observations for schema guard.
 for(let i=0;i<108;i++){
   const year=2017+Math.floor((i+10)/12);
   const month=(i+10)%12;
   const d=new Date(Date.UTC(year,month+1,0));
   const value=i===107?'1.26191118130865':i===106?'0.98':'0.25';
   rows.push(dateLabel(d)+',0.21,'+value);
 }
 return rows.join('\n')+'\n';
}

test('NY Fed parser recognizes Excel serial release vintages and date format',()=>{
 const out=parseFed(sampleCSV());
 assert.match(out.vintage,/Nov.*26/);
 assert.equal(out.latest.date,'2026-10-31');
 assert.equal(out.latest.value,1.262);
 assert.equal(out.previous.date,'2026-09-30');
 assert.equal(out.series.length,18);
 assert.ok(out.totalPeriods>=100);
});

test('NY Fed parser fails closed on short or malformed series',()=>{
 assert.throws(()=>parseFed('Date,46296,46327\n31-Oct-2026,0.9,1.2'),/unexpectedly short/);
 const malformed=sampleCSV().replace('Date,46296,46327','RELEASE,46296,46327');
 assert.throws(()=>parseFed(malformed),/header changed/);
});

const base={reporterCode:842,partner2Code:0,flowCode:'M',cmdCode:'85',refYear:2025,customsCode:'C00',motCode:0};
test('UN trade parser requires exact partner/reporter/commodity/flow match',()=>{
 const records=[{...base,partnerCode:0,primaryValue:10000},{...base,partnerCode:156,primaryValue:2300}];
 assert.equal(selectValue(records,0,'85',2025),10000);
 assert.equal(selectValue(records,156,'85',2025),2300);
 assert.equal(selectValue(records,156,'27',2025),null);
 assert.equal(selectValue(records,156,'85',2024),null);
});

test('UN trade parser rejects duplicate aggregate rows and negative values',()=>{
 const row={...base,partnerCode:156,primaryValue:125};
 assert.equal(selectValue([row,row],156,'85',2025),null);
 assert.equal(selectValue([{...row,primaryValue:-5}],156,'85',2025),null);
 assert.equal(selectValue([{...row,reporterCode:36}],156,'85',2025),null);
});
