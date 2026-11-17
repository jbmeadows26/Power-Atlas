import { createHash } from 'node:crypto';
import { db, storage } from './runtime.js';

type RunStatus = 'ok' | 'failed';
type Capture = {
  sourceUrl: string; capturedAt: string; sha256: string; bytes: number; contentType: string;
  etag: string | null; lastModified: string | null; rawArchived: boolean;
  archiveFormat: 'warc-1.1' | 'none'; archivePath?: string; archiveSha256?: string;
  captureKind: 'decoded-http-api-response'; storageClass: 'managed-mutable-object-storage';
  archiveStatus: 'stored' | 'unavailable' | 'size-limit';
};
type Attempt = { sourceId: string; attemptedAt: string; finishedAt: string; status: RunStatus; examined: number; matched: number; inserted: number; zeroMatches: boolean; failureReason?: string; collectionScope: 'bounded-scheduled-official-public' };
const sha = (text: string) => createHash('sha256').update(text, 'utf8').digest('hex');
const key = (prefix: string, value: string) => prefix + '-' + sha(value).slice(0, 36);
const MAX_WARC_BYTES=800_000;

// WARC/1.1 response record from HTTP fetch-decoded bytes. This is NOT an exact wire-level packet capture.
// Object paths are content addressed and kept inaccessible to anonymous clients. Storage has no Object Lock.
function makeWarc(sourceUrl:string, raw:string, response:Response, capturedAt:string) {
  const status=Number.isInteger(response.status)?response.status:200;
  const headers:Array<[string,string]>=[];
  response.headers.forEach((v,k)=>{if(/^[a-z0-9-]{1,80}$/.test(k)&&!/[\\r\\n]/.test(v)) headers.push([k,v.slice(0,1500)]);});
  const inner='HTTP/1.1 '+status+' '+(response.statusText||'OK').replace(/[\\r\\n]/g,' ').slice(0,80)+'\r\n'+
    headers.map(([k,v])=>k+': '+v).join('\r\n')+'\r\n\r\n'+raw;
  const innerBytes=Buffer.byteLength(inner,'utf8');
  const id=sha(sourceUrl+'|'+capturedAt+'|'+sha(raw)).slice(0,40);
  const header='WARC/1.1\r\nWARC-Type: response\r\nWARC-Target-URI: '+sourceUrl+
    '\r\nWARC-Date: '+capturedAt+'\r\nWARC-Record-ID: <urn:uuid:'+id.slice(0,8)+'-'+id.slice(8,12)+'-'+id.slice(12,16)+'-'+id.slice(16,20)+'-'+id.slice(20,32)+
    '>\r\nContent-Type: application/http; msgtype=response\r\nContent-Length: '+innerBytes+
    '\r\nWARC-Payload-Digest: sha256:'+sha(raw)+'\r\n\r\n';
  return header+inner+'\r\n\r\n';
}

export async function recordHttpDigest(sourceUrl: string, raw: string, response: Response) {
  const capturedAt = new Date().toISOString();
  const payloadHash=sha(raw);
  const length=Buffer.byteLength(raw,'utf8');
  const record:Capture={
    sourceUrl,capturedAt,sha256:payloadHash,bytes:length,
    contentType:(response.headers.get('content-type')||'').slice(0,120),
    etag:response.headers.get('etag'),lastModified:response.headers.get('last-modified'),
    rawArchived:false,archiveFormat:'none',
    captureKind:'decoded-http-api-response',storageClass:'managed-mutable-object-storage',
    archiveStatus:'unavailable'
  };
  if(length<=MAX_WARC_BYTES){
    try{
      const warc=makeWarc(sourceUrl,raw,response,capturedAt);
      const archiveSize=Buffer.byteLength(warc,'utf8');
      if(archiveSize>MAX_WARC_BYTES)record.archiveStatus='size-limit';
      else{
        const warcHash=sha(warc);
        const path='official-collection/warc/sha256/'+warcHash.slice(0,2)+'/'+warcHash+'.warc';
        const [ok]=await storage.write([{path,content:Buffer.from(warc,'utf8').toString('base64'),contentType:'application/warc'}]);
        if(ok){record.rawArchived=true;record.archiveFormat='warc-1.1';record.archivePath=path;record.archiveSha256=warcHash;record.archiveStatus='stored';}
      }
    }catch(err){console.error('WARC preservation failed; not marked archived',sourceUrl,err);}
  }else record.archiveStatus='size-limit';
  // Metadata is keyed by exact capture receipt, cannot be conflated with a new capture.
  try{
    const [saved]=await db.tx.add('intel_capture_digests',[{
      id:key('cap',sourceUrl+'|'+capturedAt+'|'+payloadHash),...record
    }]);
    if(!saved)console.warn('Duplicate capture receipt');
  }catch(err){console.error('Capture receipt write failed',sourceUrl,err);}
  return {archived:record.rawArchived,archiveStatus:record.archiveStatus,sha256:payloadHash};
}

export async function recordCollectionAttempt(input: Attempt) {
  const identifier=key('run',input.sourceId+'|'+input.attemptedAt+'|'+input.status);
  try{
    const [saved]=await db.tx.add('intel_collection_attempts',[{id:identifier,...input}]);
    if(!saved)console.warn('Duplicate collection attempt',identifier);
  }catch(err){console.error('Collection audit failed',input.sourceId,err);}
}

type IndexedRecord={id:string;sourceId?:string;sourceRecordId?:string;title?:string;summary?:string;date?:string;sourceUrl?:string;countryMention?:string;countryRule?:string;recordType?:string;reviewState?:string;collectedAt?:string;evidenceTier?:string};
type RunEntry=Attempt&{id:string};
type CaptureEntry=Capture&{id:string};
const sourceGroup=(url:string,fallback:string)=>{
  try{const h=new URL(url).hostname.toLowerCase();return h.endsWith('.justice.gov')?'DOJ':h.endsWith('.treasury.gov')||h.endsWith('.treas.gov')?'US Treasury':h.endsWith('.nist.gov')?'NIST':h.endsWith('.gov')?h:fallback;}
  catch{return fallback;}
};
export async function readEvidenceWorkbench() {
 const reads=await Promise.allSettled([
   db.list<IndexedRecord>('intel_records',{limit:220}),
   db.list<RunEntry>('intel_collection_attempts',{limit:80}),
   db.list<CaptureEntry>('intel_capture_digests',{limit:80})
 ]);
 const from=<T>(i:number):T[]=>reads[i].status==='fulfilled'?(reads[i] as PromiseFulfilledResult<{items:T[]}>).value.items:[];
 const indexed=from<IndexedRecord>(0).filter(r=>['doj','fara','cisa','ofac'].includes(r.sourceId||''))
   .sort((a,b)=>(b.collectedAt||'').localeCompare(a.collectedAt||'')).slice(0,120);
 const attempts=from<RunEntry>(1).sort((a,b)=>(b.attemptedAt||'').localeCompare(a.attemptedAt||'')).slice(0,60);
 const digests=from<CaptureEntry>(2).sort((a,b)=>(b.capturedAt||'').localeCompare(a.capturedAt||'')).slice(0,40);
 const trusted=indexed.map(r=>{
   const originGroup=sourceGroup(r.sourceUrl||'',r.sourceId||'unknown');
   const normalizedText=[r.title||'',r.summary||''].join(' ').normalize('NFKC').toLowerCase().replace(/\s+/g,' ').trim();
   return {
     id:r.id,sourceId:r.sourceId,sourceRecordId:r.sourceRecordId,title:r.title||'',summary:r.summary||'',
     date:r.date||'',sourceUrl:r.sourceUrl||'',collectedAt:r.collectedAt||'',
     countryCode:r.countryMention||null,geographicBasis:r.countryRule||'Country attribution unavailable',
     reviewState:r.reviewState||'unreviewed',evidenceTier:r.evidenceTier||'source-index',
     referenceHash:sha([r.sourceId,r.sourceRecordId,r.sourceUrl,r.title,r.date].join('|')),
     hashScope:'normalized-reference-fields-not-original-document',
     originGroup,syndicationCluster:sha(normalizedText).slice(0,24),
     independentConfirmation:false,informationCredibility:'not-assessed',
     sourceReliability:'not-assessed'
   };
 });
 const clusters=new Map<string,{count:number;origins:Set<string>}>();
 for(const r of trusted){
   const c=clusters.get(r.syndicationCluster)||{count:0,origins:new Set<string>()};
   c.count++;c.origins.add(r.originGroup);clusters.set(r.syndicationCluster,c);
 }
 const records=trusted.map(r=>({...r,syndicationCopies:clusters.get(r.syndicationCluster)?.count||1,
   distinctOriginGroups:clusters.get(r.syndicationCluster)?.origins.size||1}));
 const observedEdges=records.filter(r=>/^https:\/\//.test(r.sourceUrl)).slice(0,60)
   .map(r=>({source:r.id,target:r.sourceUrl,relation:'references_document_url',
      basis:'direct-source-link',attribution:false,provenance:r.sourceUrl,layer:'observed-selector'}));
 return {
   schemaVersion:2,generatedAt:new Date().toISOString(),
   sampleBound:{records:120,collectionRuns:60,responseDigests:40},
   collectionStatus:{
    recordStore:reads[0].status==='fulfilled'?'available':'unavailable',
    attemptLog:reads[1].status==='fulfilled'?'available':'unavailable',
    digestLedger:reads[2].status==='fulfilled'?'available':'unavailable'
   },
   metrics:{
    indexedReferences:records.length,reviewedReferences:records.filter(r=>r.reviewState==='reviewed').length,
    recordedCollectionAttempts:attempts.length,
    zeroMatchChecks:attempts.filter(r=>r.status==='ok'&&r.zeroMatches).length,
    failedChecks:attempts.filter(r=>r.status==='failed').length,responseFingerprints:digests.length,
    warcRecords:digests.filter(d=>d.rawArchived&&d.archiveFormat==='warc-1.1').length,
    observedReferenceEdges:observedEdges.length,syndicationClusters:clusters.size,
    analystApprovedAttributionEdges:0,immutableArchives:0
   },
   records,observedEdges,hypothesisEdges:[],collectionAttempts:attempts,
   responseDigests:digests.map(d=>({...d,archivePath:undefined})), // Never leak private paths
   limitations:[
    'Original HTTP API response bodies are preserved in WARC/1.1 for successful bounded captures. Linked filing PDFs and source documents are not automatically captured.',
    'AppDeploy storage permits modification; these WARC objects are NOT S3 Object Lock or write-once legal hold.',
    'WARC records use fetch-decoded response payloads and observed HTTP headers, not complete TLS or wire-level traffic captures.',
    'Original API responses larger than 800,000 bytes may only receive a SHA-256 fingerprint and size-limit status.',
    'Source similarity groups are exact normalized-text matches and publisher groups. These clusters do not prove cross-source independence or confirm the underlying claim.',
    'Country mentions are lexical references, not foreign-government attribution. There are no AI-approved identity mergers.',
    'Logs and archives start with new collector executions; historical public records are not backfilled.',
    'Analyst verification, secure reviewer approval and immutable retention require further infrastructure and human examination.',
    'No-match searches and source outages are recorded but neither establishes an absence of activity.'
   ]
 };
}
