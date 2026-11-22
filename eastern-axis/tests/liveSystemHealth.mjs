/**
 * Scheduled production DATA HEALTH gate, not a page-availability check.
 * Deliberately fails when official-data completeness collapses to 1/12.
 * GitHub Actions captures the report even for an upstream provider outage.
 */
import {readFileSync} from 'node:fs';

// Pages has no backend. Use the SAME public Neon origin as the deployed app,
// not an archived Vercel URL. Explicit overrides must also be validated.
const configured=process.env.EASTERN_AXIS_BASE_URL?.trim()||
  readFileSync(new URL('../public-api-origin.txt',import.meta.url),'utf8').trim();
const base=configured.replace(/\/$/,'');
const endpoint=new URL(base);
if(endpoint.protocol!=='https:'||!endpoint.hostname.endsWith('.neon.tech')||
    endpoint.pathname!=='/'||endpoint.search||endpoint.hash||endpoint.username||endpoint.password){
  throw Error('Country completeness audit requires the active public Neon API origin');
}
if(process.argv.includes('--check-config')){
  console.log('Country completeness source: '+base+' (public Neon API)');
  process.exit(0);
}
/**
 * A global World Bank household-survey Gini and the World Inequality
 * Database's PRE-TAX Gini are not interchangeable measurements.
 * Validate the alternate-measure status, exact publisher and visible
 * methodology warning. Match capitalization without relaxing the policy.
 */
const properlyLabelledWorldGini=(row)=>{
  if(!row||row.value===null)return true;
  const publisher=String(row.sourceName||'');
  const status=String(row.observationStatus||'');
  const isWid=/(?:\bWID\b|World Inequality Database)/i.test(publisher);
  const isAlternative=status==='alternative-measure:pretax-income-gini';
  if(!isWid&&!isAlternative)return true;
  const labelCorrect=/\bpre[\s-]?tax\b/i.test(String(row.label||''));
  const methodClear=/World Bank survey Gini/i.test(String(row.meaning||''));
  if(!(isWid&&isAlternative&&labelCorrect&&methodClear)){
    console.error('WORLD GINI DISCLOSURE CHECK:',JSON.stringify({label:row.label,sourceName:row.sourceName,
      observationStatus:row.observationStatus,meaning:row.meaning}));
  }
  return isWid&&isAlternative&&labelCorrect&&methodClear;
};
if(process.argv.includes('--test-gini')){
  const base={
    value:67.69,sourceName:'World Inequality Database · via Our World in Data',
    observationStatus:'alternative-measure:pretax-income-gini',
    meaning:'Do not compare this with World Bank survey Gini.'
  };
  if(!properlyLabelledWorldGini({...base,label:'Pre-tax income inequality (WID Gini)'})||
     !properlyLabelledWorldGini({...base,label:'pre-tax Gini'})||
      properlyLabelledWorldGini({...base,label:'Income inequality (Gini)'})||
      properlyLabelledWorldGini({...base,label:'Pre-tax Gini',observationStatus:''})||
     !properlyLabelledWorldGini({value:40,label:'Household survey Gini',
       sourceName:'World Bank PIP',observationStatus:'alternative-source:world-bank-pip'})){
    throw Error('World Gini source/measure labelling regression');
  }
  console.log('World Gini labels and method separation: PASS');
  process.exit(0);
}
const cases=[['WLD',10],['US',10],['CN',8],['IR',7]];
let failed=false;
for(const [code,minimum] of cases){
 try{
  const resp=await fetch(base+'/api/global-systems/'+code,{
    signal:AbortSignal.timeout(50000),
    headers:{Accept:'application/json',Origin:'https://jbmeadows26.github.io'}
  });
  if(!resp.ok)throw Error('HTTP '+resp.status);
  const data=await resp.json();
  if(!Array.isArray(data.indicators)||data.indicators.length!==12)throw Error('Changed 12-indicator response schema');
  const valid=data.indicators.filter(i=>typeof i.value==='number'&&Number.isFinite(i.value)&&/^\d{4}$/.test(i.year||'')&&
    typeof i.sourceUrl==='string'&&i.sourceUrl.startsWith('https://')).length;
  const supplemental=data.indicators.filter(i=>i.observationStatus?.startsWith('alternative-'));
  const report={code,available:valid,minimum,sourceLabels:supplemental.map(x=>({id:x.code,name:x.sourceName,year:x.year})),warning:data.warning};
  console.log(JSON.stringify(report));
  if(valid<minimum){failed=true;console.error('QUALITY GATE: '+code+' has '+valid+'/12 with minimum '+minimum);}
  if(code==='WLD'&&data.indicators.some(i=>i.code==='SI.POV.GINI'&&!properlyLabelledWorldGini(i))){
    failed=true;
    console.error('QUALITY GATE: World Gini must disclose that WID is a different measure');
    console.error('WORLD GINI EVIDENCE:',JSON.stringify(data.indicators.filter(i=>i.code==='SI.POV.GINI')
      .map(i=>({label:i.label,status:i.observationStatus,sourceName:i.sourceName,meaning:i.meaning,year:i.year})))));
  }
 }catch(e){failed=true;console.error('QUALITY GATE '+code+' error:',String(e));}
}
if(failed)process.exitCode=1;
