import { useEffect, useState } from 'react';
import { ClipboardCopy, FileCheck2, ShieldCheck } from 'lucide-react';
import './verificationChecklist.css';

type Ref = { id:string; title:string; date:string; sourceId:string; sourceUrl:string; referenceHash:string; hashScope:string };
type Review = { reliability:string; credibility:string; disposition:string; checkedOriginal:boolean; independent:boolean; notes:string };
const blank:Review={reliability:'F',credibility:'6',disposition:'not assessed',checkedOriginal:false,independent:false,notes:''};
export default function VerificationChecklist({records}:{records:Ref[]}) {
  const [id,setId]=useState('');
  const [review,setReview]=useState<Review>(blank);
  const [notice,setNotice]=useState('');
  const record=records.find(r=>r.id===id);
  useEffect(()=>{if(!records.some(r=>r.id===id))setId(records[0]?.id||'');},[id,records]);
  useEffect(()=>{
    try{
      const stored=window.localStorage.getItem('ea.local-review.'+id);
      setReview(stored?{...blank,...JSON.parse(stored) as Partial<Review>}:blank);
    }catch{setReview(blank);}
    setNotice('');
  },[id]);
  const update=<K extends keyof Review>(key:K,value:Review[K])=>{
    const next={...review,[key]:value};
    setReview(next);
    try{window.localStorage.setItem('ea.local-review.'+id,JSON.stringify(next));}catch{}
  };
  const copy=async()=>{
    if(!record)return;
    const text=[
      'EASTERN AXIS — LOCAL, NON-PUBLISHED ANALYST WORKSHEET',
      'Reference: '+record.id+' · '+record.title,
      'Source: '+record.sourceUrl+' · '+record.date,
      'Reference fingerprint: '+record.referenceHash+' ('+record.hashScope+')',
      'Source reliability: '+review.reliability,
      'Information credibility: '+review.credibility,
      'Triage: '+review.disposition,
      'Original read: '+review.checkedOriginal,
      'Independent corroboration personally examined: '+review.independent,
      'Notes: '+review.notes,
      'NOT AN OFFICIAL APPROVAL. No server review status changed.'
    ].join('\n');
    try{await navigator.clipboard.writeText(text);setNotice('Copied. No public record changed.');}
    catch{setNotice('Clipboard unavailable. Local notes remain in this browser.');}
  };
  return <section className="vc-box">
    <div className="vc-heading"><FileCheck2 size={18}/><div><h2>Research verification worksheet</h2><p>Separate source reliability from information credibility. Private triage, not publication.</p></div></div>
    <div className="vc-alert"><ShieldCheck size={17}/> Browser-only notes. They are not analyst credentials, approved findings, a dispute resolution, or a server-side evidence record.</div>
    <label>Select indexed reference
      <select value={id} onChange={e=>setId(e.target.value)}>
        {records.slice(0,90).map(r=><option key={r.id} value={r.id}>{r.sourceId.toUpperCase()} · {r.title.slice(0,90)}</option>)}
      </select>
    </label>
    {record?<div>
      <div className="vc-source"><strong>{record.title}</strong><a href={record.sourceUrl} target="_blank" rel="noopener noreferrer">Open original source</a></div>
      <div className="vc-fields">
        <label>Source reliability
          <select value={review.reliability} onChange={e=>update('reliability',e.target.value)}>
            {['F · Cannot be judged','A · Completely reliable','B · Usually reliable','C · Fairly reliable','D · Not usually reliable','E · Unreliable'].map(x=><option key={x} value={x[0]}>{x}</option>)}
          </select>
        </label>
        <label>Information credibility
          <select value={review.credibility} onChange={e=>update('credibility',e.target.value)}>
            {['6 · Cannot be judged','1 · Independently confirmed','2 · Probably true','3 · Possibly true','4 · Doubtful','5 · Improbable'].map(x=><option key={x} value={x[0]}>{x}</option>)}
          </select>
        </label>
        <label>Research disposition
          <select value={review.disposition} onChange={e=>update('disposition',e.target.value)}>
            {['not assessed','needs corroboration','conflicting reports','propose supervisor review'].map(x=><option key={x}>{x}</option>)}
          </select>
        </label>
      </div>
      <label className="vc-check"><input type="checkbox" checked={review.checkedOriginal} onChange={e=>update('checkedOriginal',e.target.checked)}/> I personally examined the original source</label>
      <label className="vc-check"><input type="checkbox" checked={review.independent} onChange={e=>update('independent',e.target.checked)}/> I personally examined an independent corroborating source (not syndicated reporting)</label>
      <label>Research notes (saved only in this browser)
        <textarea rows={3} maxLength={2400} value={review.notes} onChange={e=>update('notes',e.target.value)} placeholder="Citations, conflicting evidence, known legal status and unknowns…" />
      </label>
      <div className="vc-actions"><button onClick={copy}><ClipboardCopy size={14}/> Copy audit memo</button><span>{notice||'Not submitted. No publication approval.'}</span></div>
    </div>:<p>No matching references yet. Use Global to inspect untagged source leads.</p>}
  </section>;
}
