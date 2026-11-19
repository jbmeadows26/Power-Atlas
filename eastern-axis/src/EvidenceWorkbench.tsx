import {useEffect, useMemo, useState} from 'react';
import {api} from '@appdeploy/client';
import {Activity, AlertTriangle, ArrowUpRight, Database, FileCheck2, Fingerprint, Globe2, Network, RefreshCcw, ShieldCheck} from 'lucide-react';
import './evidence.css';
import VerificationChecklist from './VerificationChecklist';

type Reference = {id:string;title:string;summary:string;sourceId:string;sourceRecordId:string;date:string;sourceUrl:string;countryCode:string|null;geographicBasis:string;reviewState:string;referenceHash:string;hashScope:string;collectedAt:string};
type Run = {id:string;sourceId:string;status:string;attemptedAt:string;examined:number;matched:number;inserted:number;zeroMatches:boolean;failureReason?:string};
type Digest = {id:string;sourceUrl:string;capturedAt:string;sha256:string;bytes:number;rawArchived:boolean;archiveFormat:string;archiveStatus:string;archiveSha256?:string};
type Workbench = {generatedAt:string;records:Reference[];collectionAttempts:Run[];responseDigests:Digest[];hypothesisEdges:unknown[];observedEdges:unknown[];metrics:Record<string,number>;collectionStatus:Record<string,string>;limitations:string[]};
type Props = {countryCode?:string};
const safeDate=(s?:string)=>s?new Date(s).toLocaleString('en-US',{dateStyle:'medium',timeStyle:'short'}):'Not recorded';
const names:Record<string,string>={doj:'DOJ',fara:'FARA',cisa:'CISA KEV',ofac:'Treasury OFAC'};

export default function EvidenceWorkbench({countryCode}:Props){
 const [data,setData]=useState<Workbench|null>(null);
 const [error,setError]=useState('');
 const [loading,setLoading]=useState(false);
 const [source,setSource]=useState('all');
 const [term,setTerm]=useState('');
 const [panel,setPanel]=useState<'records'|'runs'|'digests'|'graph'>('records');
 const refresh=()=>{setLoading(true);setError('');api.get('/api/evidence-workbench').then(r=>setData(r.data as Workbench)).catch(()=>setError('The verification API is unavailable. No data is inferred.')).finally(()=>setLoading(false));};
 useEffect(refresh,[]);
 const focused=countryCode && countryCode!=='all';
 const records=useMemo(()=>(data?.records||[]).filter(r=>(!focused||r.countryCode===countryCode)&&(source==='all'||r.sourceId===source)&&[r.title,r.summary,r.sourceRecordId].join(' ').toLowerCase().includes(term.trim().toLowerCase())),[data,focused,countryCode,source,term]);
 return <div className="ea-lab">
   <div className="eyebrow"><span className="eyebrow-line"/> RESEARCH OPERATIONS / EVIDENCE VERIFICATION</div>
   <div className="ea-lab-head"><div><h1>Verification Lab<span className="period">.</span></h1><p>Inspect what collectors observed, what evidence was fingerprinted, and what remains unverified.</p></div><button onClick={refresh} disabled={loading}><RefreshCcw size={15}/> {loading?'Checking…':'Refresh evidence status'}</button></div>
   <div className="ea-lab-notice"><ShieldCheck size={21}/><p><strong>Publication boundary:</strong> These entries are raw collection leads, not substantiated allegations. An original URL is not proof of the claim it contains, and a hash without the original bytes is not a preserved artifact.</p></div>
   {error&&<div className="ea-lab-warning"><AlertTriangle size={17}/>{error}</div>}
   {!data&&loading&&<p>Reading the indexed evidence and collection logs…</p>}
   {data&&<>
    <div className="ea-lab-cards">
     <div><span>SOURCE REFERENCES</span><strong>{data.metrics.indexedReferences}</strong><small>Bounded read, not a full corpus</small></div>
     <div><span>ANALYST-REVIEWED</span><strong>{data.metrics.reviewedReferences}</strong><small>Do not equate a source with verification</small></div>
     <div><span>WARC CAPTURES / HASHES</span><strong>{data.metrics.warcRecords||0} / {data.metrics.responseFingerprints}</strong><small>Managed storage; no write-once guarantee</small></div>
     <div><span>COLLECTION OUTCOMES</span><strong>{data.metrics.zeroMatchChecks} no-match · {data.metrics.failedChecks} failed</strong><small>Independent counts; not a success rate or fraction</small></div>
    </div>
    <div className="ea-lab-scopes"><Globe2 size={16}/><span>{focused?'Country scope: '+countryCode+' — only explicitly tagged references appear. Untagged leads remain in Global.':'Global scope — includes untagged references.'}</span><span>Source and collection health remain global.</span></div>
    <div className="ea-lab-tabs" role="group" aria-label="Verification views">
      <button aria-pressed={panel==='records'} onClick={()=>setPanel('records')}><FileCheck2 size={15}/> Evidence</button>
      <button aria-pressed={panel==='runs'} onClick={()=>setPanel('runs')}><Activity size={15}/> Collection runs</button>
      <button aria-pressed={panel==='digests'} onClick={()=>setPanel('digests')}><Fingerprint size={15}/> Fingerprints</button>
      <button aria-pressed={panel==='graph'} onClick={()=>setPanel('graph')}><Network size={15}/> Relationship rules</button>
    </div>
    {panel==='records'&&<><div className="ea-lab-controls"><input aria-label="Search indexed evidence" placeholder="Search source records…" value={term} onChange={e=>setTerm(e.target.value)}/><select aria-label="Filter evidence source" value={source} onChange={e=>setSource(e.target.value)}><option value="all">All source families</option>{Object.entries(names).map(([id,name])=><option key={id} value={id}>{name}</option>)}</select></div>
       <p className="ea-lab-subtle">{records.length} displayed references. Country tags identify text mentions, not source-country responsibility.</p>
       <div className="ea-lab-list">{records.length?records.slice(0,70).map(r=><article key={r.id}><div className="ea-lab-item-top"><span>{names[r.sourceId]||r.sourceId} · {r.date||'undated'}</span><span>UNREVIEWED</span></div><h3>{r.title}</h3><p>{r.summary}</p><small>Record: {r.sourceRecordId} · {r.countryCode?'Tagged '+r.countryCode+' (mention only)':'Country attribution unknown'}</small><details><summary>Reference fingerprint and evidence limitations</summary><p>SHA-256 normalized reference: <code>{r.referenceHash}</code></p><p>{r.geographicBasis}. Fingerprint covers metadata fields, not a preserved original document.</p></details>{r.sourceUrl&&<a href={r.sourceUrl} rel="noopener noreferrer" target="_blank">Inspect original source <ArrowUpRight size={13}/></a>}</article>):<div className="ea-lab-empty">No records match this scope. This is a collection or tagging gap, not proof that no relevant activity exists.</div>}</div>
    </>}
    {panel==='runs'&&<div className="ea-lab-list"><p className="ea-lab-subtle">Collection attempt records start with newly executed scheduled checks. A zero-hit search and an API failure are different outcomes.</p>{data.collectionAttempts.length?data.collectionAttempts.map(x=><article key={x.id}><div className="ea-lab-item-top"><span>{names[x.sourceId]||x.sourceId}</span><span>{x.status==='failed'?'FAILED':x.zeroMatches?'ZERO MATCHES':'CHECKED'}</span></div><h3>{safeDate(x.attemptedAt)}</h3><p>Examined: {x.examined} · Matched: {x.matched} · Newly indexed: {x.inserted}</p>{x.failureReason&&<p>Failure: {x.failureReason}</p>}</article>):<div className="ea-lab-empty">No new-format collection attempts yet. Previous collector status exists elsewhere but was not backfilled.</div>}</div>}
    {panel==='digests'&&<div className="ea-lab-list"><p className="ea-lab-subtle">SHA-256 fingerprints identify public API responses. Bounded WARC archives are stored only when storage succeeds. Managed storage does not provide Object Lock.</p>{data.responseDigests.length?data.responseDigests.map(x=><article key={x.id}><div className="ea-lab-item-top"><span>HTTP response fingerprint</span><span>{safeDate(x.capturedAt)}</span></div><h3>{x.sourceUrl}</h3><p>SHA-256: <code>{x.sha256}</code></p><small>Observed bytes: {x.bytes.toLocaleString()} · WARC: {x.rawArchived?'Stored':'Not stored'} · Status: {x.archiveStatus||'legacy digest-only'} {x.archiveSha256?' · WARC hash: '+x.archiveSha256:''}</small></article>):<div className="ea-lab-empty">No newly recorded HTTP fingerprints yet.</div>}</div>}
    {panel==='graph'&&<div className="ea-lab-list"><article><h3>Layer 1 — observed source-reference edges</h3><p>{data.metrics.observedReferenceEdges} direct links between indexed entries and cited document URLs. These do NOT establish identity, control, ownership or government affiliation.</p><h3>Layer 2 — attribution hypotheses</h3><p>0 AI-suggested links, 0 analyst-approved identity mergers. This layer is disabled until confidence calibration, independent evidence and human approvals are implemented.</p></article><article><h3>Source lineage</h3><p>Exact normalized text is clustered under publisher origin groups to prevent repeated identical text from being treated as multiple independent findings. This is not a full synthetic-content classifier, and independent corroboration still requires analysis.</p></article></div>}
    <VerificationChecklist records={records} />
    <details className="ea-lab-method"><summary>Open methodology and outstanding chain-of-custody gaps</summary>{data.limitations.map((l,i)=><p key={i}>{l}</p>)}<p>System health: records {data.collectionStatus.recordStore}, attempts {data.collectionStatus.attemptLog}, fingerprints {data.collectionStatus.digestLedger}.</p><p>Snapshot checked {safeDate(data.generatedAt)}</p></details>
   </>}
 </div>;
}
