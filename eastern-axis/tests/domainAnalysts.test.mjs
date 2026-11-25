import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {buildDomainBrief,ANALYST_ROUTE_KEYS,SNAPSHOT_PATHS} from '../src/lib/domainAnalysts.ts';

const source=(id,code='CN')=>({id,code,title:id,sourceUrl:'https://example.org/'+id,publisher:'Official reference',published:'2026-11-21'});
const minimal=()=>({
 source:{schemaVersion:2,generatedAt:'2026-11-21T10:00:00Z',records:[{...source('publication'),countries:['CN']}]},
 triage:{schemaVersion:1,generatedAt:'2026-11-21T10:00:00Z',reviews:[
  {...source('signal'),screened:true,modelReviewed:true,anomalous:true,corroborated:false,status:'monitor',fresh:true}
 ]},
 inventory:{schemaVersion:1,generatedAt:'2026-11-21',assets:[
  {...source('asset'),'category':'Nuclear',quantity:'620',value:620,unit:'warheads',basis:'independent estimate'}
 ]},
 conflict:{schemaVersion:1,generatedAt:'2026-11-21',zones:[
  {id:'theater',countryCodes:['CN'],status:'review',modelReviewed:false,promoted:false,evidence:[{source:'Official record',url:'https://example.org/zone'}]}
 ]},
 markets:{schemaVersion:1,checkedAt:'2026-11-21',metrics:[
  {id:'SP500',label:'S&P 500',sourceUrl:'https://example.org/market',change5Pct:-5.5,history:[{date:'2026-11-18',value:100},{date:'2026-11-19',value:96},{date:'2026-11-20',value:94}]}
 ]},
 transmission:{schemaVersion:1,checkedAt:'2026-11-21',householdMetrics:[source('credit')],issuers:[{name:'Sample issuer',sourceUrl:'https://example.org/issuer'}],filings:[]},
 shortage:{schemaVersion:1,generatedAt:'2026-11-21',forecasts:[
  {id:'fuel',status:'cross-source-watch',confirmedShortage:false,commandEligible:false,evidence:[{source:'Official inventory',url:'https://example.org/fuel'}]}
 ]},
 early:{schemaVersion:1,checkedAt:'2026-11-21',metrics:[{...source('electricity'),group:'Energy',label:'Electricity supply',period:'2026-11'}]},
 resilience:{schemaVersion:1,checkedAt:'',observations:[],incidents:[],capabilities:[]}
});
const build=(view,focus='overview',country='all',snapshots=minimal())=>buildDomainBrief({
 view,focus,country,countryName:country==='all'?'Worldwide':'China',
 cases:[{code:'CN',source:'https://example.org/case',title:'Curated legal action'}],
 snapshots,systems:country==='all'?undefined:{indicators:[
  {code:'FP.CPI.TOTL.ZG',value:3.2,year:'2025',sourceUrl:'https://example.org/cpi'},
  {code:'SP.DYN.LE00.IN',value:75,year:'2024',sourceUrl:'https://example.org/life'}
 ]},failures:[]
});
test('every navigation subcategory has an evidence-backed analyst route',()=>{
 const code=readFileSync(new URL('../src/App.tsx',import.meta.url),'utf8');
 const regex=/\{label:'[^']+',section:'([^']+)'(?:,focus:'([^']+)')?\}/g;
 const found=new Set([...code.matchAll(regex)].map(match=>match[1]==='Economic intelligence'?
  'Economic intelligence:'+(match[2]||'overview'):match[1]));
 assert.equal(found.size,26,'Navigation taxonomy changed; update analyst coverage');
 for(const key of found)assert.ok(ANALYST_ROUTE_KEYS.includes(key),'Unmapped submenu: '+key);
 for(const key of ANALYST_ROUTE_KEYS)assert.ok(found.has(key),'Inactive analyst route: '+key);
});
test('all analyst routes return numeric evidence, direction, limits and original links or an explicit gap',()=>{
 for(const route of ANALYST_ROUTE_KEYS){
  const key=route.startsWith('Economic intelligence:')?'Economic intelligence':route;
  const focus=route.startsWith('Economic intelligence:')?route.split(':')[1]:'overview';
  const brief=build(key,focus);
  assert.ok(brief.title&&brief.finding&&brief.direction&&brief.implication&&brief.watch&&brief.limitation,route);
  assert.ok(['source-dated','monitoring','coverage-gap'].includes(brief.status),route);
  for(const src of brief.sources)assert.ok(src.url.startsWith('https://'),route);
  for(const number of brief.metrics)assert.notEqual(number.value,'undefined',route);
 }
});
test('non-corroborated anomaly never promoted as command alert',()=>{
 const brief=build('Overview');
 assert.equal(brief.metrics.find(m=>m.label==='Corroborated alerts')?.value,'0');
 assert.match(brief.direction,/cannot be inferred/);
});
test('indexed military observation is never confused with active hardware count',()=>{
 const brief=build('Defense intelligence','overview','CN');
 assert.equal(brief.metrics[0].value,'1');
 assert.match(brief.metrics[0].detail,/Not a count of equipment/);
 assert.match(brief.limitation,/Warhead subsets overlap/);
});
test('country conflict selection tolerates missing countryCodes without false attribution',()=>{
 const snap=minimal();
 snap.conflict.zones.push({id:'untagged',status:'monitor'});
 const china=build('Global conflict watch','overview','CN',snap);
 assert.equal(china.metrics[0].value,'1');
 const global=build('Global conflict watch','overview','all',snap);
 assert.equal(global.metrics[0].value,'2');
});
test('empty collector is marked coverage gap, never represented as zero threats',()=>{
 const snap=minimal();
 snap.resilience={schemaVersion:1,status:'unavailable',observations:[],incidents:[],capabilities:[]};
 const brief=build('Cyber resilience','overview','all',snap);
 assert.equal(brief.status,'coverage-gap');
 assert.match(brief.finding,/No current independently sampled/);
 assert.match(brief.implication,/Do not interpret an unavailable collector as zero/);
});
test('shortage watch never masquerades as confirmed shortage',()=>{
 const brief=build('Economic intelligence','shortages');
 assert.equal(brief.metrics.find(x=>x.label==='Confirmed shortages')?.value,'0');
 assert.match(brief.direction,/cannot establish a retail shortage/);
});
test('original snapshot paths remain relative and source-bounded',()=>{
 for(const path of Object.values(SNAPSHOT_PATHS)){
  assert.ok(/^(analysis|telemetry)\/[a-z-]+\.json$/.test(path),path);
 }
});

test('unloaded feeds never render fake zero-valued insights',()=>{
 const brief=build('Economic intelligence','signals','all',{});
 assert.ok(brief.metrics.every(x=>x.value==='—'));
 assert.match(brief.finding,/Loading source-validated/);
});

test('partial source outage is never summarized as zero publications',()=>{
 const snap=minimal();
 delete snap.source;
 const brief=build('Overview','overview','all',snap);
 assert.equal(brief.metrics[0].value,'—');
 assert.match(brief.finding,/publication coverage unavailable/i);
 assert.doesNotMatch(brief.finding,/0 dated public-source records/);
});

test('forecast routes withhold unsupported probabilities',()=>{for(const route of ['Forecast intelligence','Forecast track record']){const b=build(route);assert.equal(b.status,'coverage-gap');assert.ok(b.metrics.every(m=>m.value==='—'));}});

test('country baseline cards show the selected country data without waiting for unrelated snapshots',()=>{
 const indicators=[
  {code:'NY.GDP.MKTP.KD.ZG',value:4.9,year:'2025',sourceUrl:'https://example.org/gdp'},
  {code:'FP.CPI.TOTL.ZG',value:0,year:'2025',sourceUrl:'https://example.org/cpi'},
  {code:'SL.UEM.TOTL.ZS',value:4.6,year:'2025',sourceUrl:'https://example.org/labor'},
  {code:'NE.TRD.GNFS.ZS',value:38,year:'2025',sourceUrl:'https://example.org/trade'},
  {code:'BX.KLT.DINV.WD.GD.ZS',value:0.4,year:'2025',sourceUrl:'https://example.org/fdi'},
  {code:'EG.ELC.ACCS.ZS',value:100,year:'2024',sourceUrl:'https://example.org/electricity'}
 ];
 const input={focus:'overview',country:'CN',countryName:'China',cases:[],snapshots:{},systems:{indicators},failures:['markets','shortage','early']};
 const macro=buildDomainBrief({...input,view:'Macro indicators'});
 assert.deepEqual(macro.metrics.map(m=>m.label),['GDP growth','Consumer inflation','Unemployment']);
 assert.equal(macro.metrics[1].value,'0%','A measured zero must remain zero');
 assert.equal(macro.status,'source-dated');
 assert.equal(macro.sources.length,3);
 const trade=buildDomainBrief({...input,view:'Trade indicators'});
 assert.deepEqual(trade.metrics.map(m=>m.label),['Trade / GDP','FDI / GDP']);
 assert.equal(trade.sources.length,2);
 const energy=buildDomainBrief({...input,view:'Energy & resources'});
 assert.equal(energy.metrics[0].value,'+100%');
 assert.ok(energy.metrics.slice(1).every(m=>m.value==='—'));
 assert.equal(energy.status,'coverage-gap');
});
test('worldwide tagged-record count excludes untagged documents',()=>{
 const snap=minimal();snap.source.records.push({...source('untagged'),countries:[]});
 const b=build('Countries','overview','all',snap);
 assert.equal(b.metrics.find(x=>x.label==='Country-tagged reports')?.value,'1');
});
test('a failed refresh preserves last dated data but exposes the gap',()=>{
 const b=buildDomainBrief({view:'Overview',focus:'overview',country:'all',cases:[],snapshots:minimal(),failures:['source']});
 assert.equal(b.metrics[0].value,'1');assert.match(b.metrics[0].detail,/refresh failed/);
 assert.equal(b.status,'coverage-gap');
});
test('stale cyber telemetry is not a current reading',()=>{
 const snap=minimal();snap.resilience={schemaVersion:1,checkedAt:'2000-01-01',observations:[source('probe')],incidents:[],capabilities:[]};
 const b=build('Cyber resilience','overview','all',snap);
 assert.equal(b.metrics[0].value,'—');assert.equal(b.metrics[1].value,'—');
 assert.equal(b.status,'coverage-gap');
});
test('blocked issuer collection is not a verified zero filing count',()=>{
 const snap=minimal();snap.transmission.issuers=[{name:'Issuer',status:'unavailable',sourceUrl:'https://example.org/issuer'}];
 const b=build('Corporate intelligence','overview','all',snap);
 assert.equal(b.metrics[1].value,'—');assert.match(b.finding,/filings are unavailable/);
});
