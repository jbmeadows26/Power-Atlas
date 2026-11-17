import { db } from './runtime.js';

export const OFAC_EXPORT = 'https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/SDN.CSV';
type OFACHealth = {
  sourceId: 'ofac'; status: 'ok'|'error'; lastAttemptAt:string; lastSuccessAt?:string;
  lastError?:string; examined:number; inserted:number; duplicates:number;
};
type RecordItem = {
  id:string; sourceId:'ofac'; sourceRecordId:string; title:string; summary:string; date:string;
  sourceUrl:string; recordType:string; reviewState:'unreviewed';
  evidenceTier:'original-source-index'; collectedAt:string; sanctionsPrograms:string[];
};
type Metadata = {
  id:'ofac-sdn'; checkedAt:string; sourceUrl:string; records:number;
  sampleSize:number; etag?:string; lastModified?:string; programCounts:Record<string,number>;
  recordTypes:Record<string,number>; dataset:'SDN'; scope:'official-primary-list-only';
};
const SELECT = [
  {key:'RUSSIA', match:/^RUSSIA/i},
  {key:'IRAN', match:/^IRAN|^IFSR/i},
  {key:'DPRK', match:/^DPRK|^NKOREA/i},
  {key:'CUBA', match:/^CUBA/i},
  {key:'VENEZUELA', match:/^VENEZUELA/i},
  {key:'BELARUS', match:/^BELARUS/i},
  {key:'CYBER', match:/^CYBER/i},
];
function csvEach(text:string, receive:(row:string[])=>void) {
  let fields:string[]=[]; let value=''; let quoted=false;
  for(let i=0;i<text.length;i++){
    const c=text[i];
    if(c==='"'){
      if(quoted && text[i+1]==='"') {value+='"';i++;}
      else quoted=!quoted;
    }else if(c===',' && !quoted){fields.push(value.trim());value='';}
    else if((c==='\n'||c==='\r') && !quoted){
      if(c==='\r' && text[i+1]==='\n') i++;
      fields.push(value.trim());value='';
      if(fields.length>1) receive(fields);
      fields=[];
    } else {value+=c;}
  }
  if(value.length||fields.length){fields.push(value.trim());if(fields.length>1)receive(fields);}
}
export async function readOFACMetadata() {
  try {
    const [data] = await db.get<Metadata>('intel_feed_metadata',['ofac-sdn'],{consistent:true});
    return data || null;
  } catch { return null; }
}
async function storeState(state:OFACHealth) {
  const [saved]=await db.tx.update('intel_source_health',[{id:'ofac',record:state}]);
  if(!saved) throw new Error('OFAC source health write not confirmed');
}
export async function syncOFAC() {
  const attemptedAt=new Date().toISOString();
  let previous:OFACHealth|null=null;
  try {
    try { [previous]=await db.get<OFACHealth>('intel_source_health',['ofac'],{consistent:true}); } catch {}
    const prior=await readOFACMetadata();
    // Avoid redownloading the full official list if the actual published object has not changed.
    // A HEAD failure is nonfatal; GET remains authoritative.
    let response:Response|null=null;
    try {
      const head=await fetch(OFAC_EXPORT,{method:'HEAD',signal:AbortSignal.timeout(8500)});
      const tag=head.headers.get('etag') || '';
      if(head.ok && prior?.etag && tag && prior.etag===tag) {
        await storeState({sourceId:'ofac',status:'ok',lastAttemptAt:attemptedAt,lastSuccessAt:attemptedAt,
          examined:prior.records,inserted:0,duplicates:0});
        return {sourceId:'ofac',status:'ok',examined:prior.records,inserted:0,unchanged:true};
      }
    } catch {}
    response=await fetch(OFAC_EXPORT,{signal:AbortSignal.timeout(20500),
      headers:{Accept:'text/csv'}});
    if(!response.ok) throw new Error('Treasury SDN export returned HTTP '+response.status);
    const csv=await response.text();
    if(csv.length<750000) throw new Error('OFAC export unexpectedly small; refusing partial update');
    let records=0, invalid=0;
    const recordTypes:Record<string,number>={};
    const programCounts:Record<string,number>={};
    const picks:Record<string,RecordItem[]>={};
    for(const group of SELECT) picks[group.key]=[];
    csvEach(csv,row=>{
      const id=String(row[0]||'').replace(/^\uFEFF/,'').trim();
      const name=String(row[1]||'').trim();
      const type=String(row[2]||'entity').replace(/^-0-$/,'entity');
      if(row.length!==12 || !/^\d{1,10}$/.test(id)||name.length<2){invalid++;return;}
      records++;
      const programs=(String(row[3]||'').match(/\[([^\]]+)\]/g)||[])
        .map(s=>s.slice(1,-1).trim())
        .filter(Boolean);
      if(!programs.length && row[3] && row[3]!=='-0-') programs.push(row[3].trim());
      recordTypes[type]=(recordTypes[type]||0)+1;
      for(const p of programs) programCounts[p]=(programCounts[p]||0)+1;
      for(const g of SELECT) {
        if(picks[g.key].length>=3 || !programs.some(p=>g.match.test(p))) continue;
        picks[g.key].push({
          id:'ofac-'+id,sourceId:'ofac',sourceRecordId:id,
          title:name.slice(0,350),summary:'Listed in the U.S. Treasury OFAC SDN dataset. Sanctions programs: '+programs.slice(0,5).join(', ')+'. A program code does not establish nationality, location or state direction. Check aliases and other lists separately.',
          date:'',sourceUrl:'https://sanctionssearch.ofac.treas.gov/',
          recordType:'OFAC SDN / '+type,reviewState:'unreviewed',evidenceTier:'original-source-index',
          collectedAt:attemptedAt,sanctionsPrograms:programs.slice(0,12)
        });
      }
    });
    if(records<10000||invalid>records*0.05) throw new Error('OFAC export format validation failed: '+records+' valid / '+invalid+' invalid');
    const selected=[...new Map(SELECT.flatMap(g=>picks[g.key]).map(x=>[x.id,x])).values()].slice(0,21);
    const adds=selected.length?await db.tx.add('intel_records',selected):[];
    const inserted=adds.filter(Boolean).length;
    const metadata:Metadata={
      id:'ofac-sdn',checkedAt:attemptedAt,sourceUrl:OFAC_EXPORT,records,sampleSize:selected.length,
      etag:response.headers.get('etag')||undefined,lastModified:response.headers.get('last-modified')||undefined,
      programCounts,recordTypes,dataset:'SDN',scope:'official-primary-list-only'
    };
    const [metaWritten]=await db.tx.update('intel_feed_metadata',[{id:'ofac-sdn',record:metadata}]);
    if(!metaWritten) throw new Error('OFAC metadata write not confirmed');
    await storeState({sourceId:'ofac',status:'ok',lastAttemptAt:attemptedAt,lastSuccessAt:attemptedAt,
      examined:records,inserted,duplicates:selected.length-inserted});
    console.info('OFAC official SDN check', {records,inserted,invalid});
    return {sourceId:'ofac',status:'ok',examined:records,inserted};
  } catch(err) {
    const message=err instanceof Error ? err.name+': '+err.message : 'OFAC sync exception';
    try {await storeState({sourceId:'ofac',status:'error',lastAttemptAt:attemptedAt,
      lastSuccessAt:previous?.lastSuccessAt,lastError:message.slice(0,200),
      examined:previous?.examined||0,inserted:0,duplicates:0});}
    catch(statusErr){console.error('OFAC status persistence failed',statusErr);}
    console.error('Official OFAC intake unavailable',message);
    return {sourceId:'ofac',status:'error',error:message};
  }
}