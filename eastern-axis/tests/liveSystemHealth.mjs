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
const base=configured.replace(/\\/$/,'');
const endpoint=new URL(base);
if(endpoint.protocol!=='https:'||!endpoint.hostname.endsWith('.neon.tech')||
    endpoint.pathname!=='/'||endpoint.search||endpoint.hash||endpoint.username||endpoint.password){
  throw Error('Country completeness audit requires the active public Neon API origin');
}
if(process.argv.includes('--check-config')){
  console.log('Country completeness source: '+base+' (public Neon API)');
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
  if(code==='WLD'&&data.indicators.some(i=>i.code==='SI.POV.GINI'&&i.value!==null&&!i.label.includes('pre-tax'))){
    failed=true;console.error('QUALITY GATE: World Gini must disclose that WID is a different measure');
  }
 }catch(e){failed=true;console.error('QUALITY GATE '+code+' error:',String(e));}
}
if(failed)process.exitCode=1;
