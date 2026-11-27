import {test} from "node:test";
import assert from "node:assert/strict";
import {analyze,scenario,validFeed,observation,publicContext,validateProfile} from "../site/business-intelligence/engine.mjs";
const now=Date.parse("2026-11-27T12:00:00Z");
const ev={kind:"input-price",title:"Brent crude oil",publisher:"World Bank",period:"2026-10",url:"https://www.worldbank.org/en/research/commodity-markets",changePct:7};
const route={kind:"corridor-transit",title:"Suez",publisher:"IMF PortWatch",period:"2026-11-22",url:"https://portwatch.imf.org/",changePct:-1.2};
const data={shortage:{forecasts:[{id:"fuel",status:"input-cost-watch",summary:"Input pressure, not a shortage.",evidence:[ev,route]},{id:"medicines",status:"data-gap",evidence:[]}]},conflicts:{zones:[{name:"Ukraine / Russia",countryCodes:["UA","RU"],direction:"stable",measurementFresh:true,promoted:false,evidence:[{source:"UCDP",observedAt:"2026-10-31",url:"https://ucdp.uu.se/"}]}]},physical:{metrics:[{id:"sofr-rate",label:"SOFR",source:"NY Fed",period:"2026-11-24",sourceUrl:"https://www.newyorkfed.org/markets/reference-rates/sofr",value:3.94}]},warning:{generatedAt:"2026-11-27T08:00:00Z",reviews:[],summary:{monitoring:67,elevated:0}}};
const p={type:"importer",dependencies:[{name:"QA dependency",country:"UA",product:"fuel",corridor:"Suez",monthlyCost:10000}],financing:true};
test("only declared exposure matches; proxy indicators remain distinct from company costs",()=>{
 const r=analyze(data,p,now);assert.deepEqual(r.findings.map(x=>x.domain),["Supply","Cost","Logistics","Geopolitics","Finance"]);
 assert.ok(r.findings.every(x=>x.evidence.length));assert.match(r.findings[1].detail,/not the company's cost increase/);
 assert.equal(analyze(data,{type:"importer",dependencies:[]},now).findings.length,0);
});
test("missing or stale evidence does not become an all-clear or verified shortage",()=>{
 const r=analyze(data,{type:"manufacturer",dependencies:[{name:"meds",country:"US",product:"medicines",corridor:"Panama",monthlyCost:null}]},now);
 assert.equal(r.findings.length,0);assert.equal(r.gaps.length,3);
 const x=analyze(data,p,Date.parse("2028-01-01"));assert.equal(x.findings.length,0);assert.ok(x.gaps.length>=4);
 assert.equal(validFeed("shortage",{forecasts:[null]}),false);assert.equal(observation("2026-02-30",now),"invalid");
});
test("scenario requires explicit quote input",()=>{
 assert.deepEqual(scenario(10000,7),{monthly:700,annual:8400,alternative:10700});
 assert.deepEqual(scenario(10000,-5),{monthly:-500,annual:-6000,alternative:9500});assert.equal(scenario(10000,null),null);
 assert.throws(()=>validateProfile({type:"importer",dependencies:[{name:"x",country:"USA",monthlyCost:null}]}));
});
test("upstream count uses actual summary keys and freshness",()=>{
 assert.equal(publicContext(data,now).at(-1).value,"67 monitored / 0 elevated");
 assert.equal(publicContext(data,Date.parse("2027-01-01")).length,0);
});
