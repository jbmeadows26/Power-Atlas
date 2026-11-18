import {useEffect,useMemo,useState} from 'react';
import {Activity,ArrowUpRight,BarChart3,Database,Globe2,RefreshCcw,ShieldCheck} from 'lucide-react';
import './supplyContext.css';
import {api} from './lib/api';

type Month={date:string;value:number};
type Pressure={status:string;checkedAt:string;vintage:string|null;latest:Month|null;previous:Month|null;
 series:Month[];totalPeriods:number;source:string;download:string;unit:string;note:string;warning?:string};
type Trade={status:string;countryCode:string;partner:string;hs:string;product:string;year:number|null;
 partnerValue:number|null;worldValue:number|null;sharePct:number|null;source:string;checkedAt:string;warning?:string;method:string};
const groups=[['TOTAL','All goods'],['27','Fuel & energy'],['85','Electronics'],['31','Fertilizer'],['10','Grains'],['26','Ores'],['72','Steel'],['90','Precision devices']] as const;
const usd=(value:number|null)=>value===null?'—':'$'+new Intl.NumberFormat('en-US',{notation:'compact',maximumFractionDigits:2}).format(value);
function dateMonth(date:string){return new Date(date+'T12:00:00Z').toLocaleDateString('en-US',{month:'short',year:'2-digit',timeZone:'UTC'});}
export default function SupplyContext({countryCode,countryName}:{countryCode:string;countryName?:string}){
 const [macro,setMacro]=useState<Pressure|null>(null);
 const [macroLoading,setMacroLoading]=useState(true);
 const [trade,setTrade]=useState<Trade|null>(null);
 const [tradeLoading,setTradeLoading]=useState(false);
 const [macroError,setMacroError]=useState('');
 const [tradeError,setTradeError]=useState('');
 const [commodity,setCommodity]=useState('TOTAL');
 const [retry,setRetry]=useState(0);
 useEffect(()=>{
   let active=true;setMacroLoading(true);setMacroError('');
   api.get('/api/supply-macro').then(r=>{if(active)setMacro(r.data as Pressure);})
     .catch(()=>{if(active)setMacroError('NY Fed monthly series could not be retrieved.');})
     .finally(()=>{if(active)setMacroLoading(false);});
   return()=>{active=false};
 },[retry]);
 useEffect(()=>{
   let active=true;setTrade(null);setTradeError('');
   if(countryCode==='all'){setTradeLoading(false);return()=>{active=false};}
   setTradeLoading(true);
   api.get('/api/supply-trade/'+encodeURIComponent(countryCode)+'/'+encodeURIComponent(commodity))
     .then(r=>{if(active)setTrade(r.data as Trade);})
     .catch(()=>{if(active)setTradeError('UN Comtrade public preview could not be retrieved.');})
     .finally(()=>{if(active)setTradeLoading(false);});
   return()=>{active=false};
 },[countryCode,commodity,retry]);
 const trend=useMemo(()=>{
   if(!macro?.latest||!macro.previous)return null;
   return Math.round((macro.latest.value-macro.previous.value)*100)/100;
 },[macro]);
 return <div className="scx-root">
   <section className="scx-panel" aria-label="Federal Reserve global supply chain pressure">
     <header><span className="sc-eyebrow"><Activity size={14}/> 03 / GLOBAL SUPPLY PRESSURE</span><a href="https://www.newyorkfed.org/research/policy/gscpi" target="_blank" rel="noopener noreferrer">NY FED / ORIGINAL SOURCE <ArrowUpRight size={13}/></a></header>
     <h2>Is pressure building worldwide?</h2>
     <p>Monthly New York Fed Global Supply Chain Pressure Index (GSCPI). Values are standard deviations from its historical mean—not percentages, shipping prices, or country-specific risks.</p>
     {macroLoading&&<div className="scx-note">Loading monthly revision-vintage data…</div>}
     {(macroError||macro?.status==='unavailable'||macro?.status==='stale')&&<div className="scx-note scx-warn">{macroError||macro?.warning||(macro?.status==='stale'?'Latest observation is more than 125 days old. Interpret as historical.':'NY Fed data unavailable.')}</div>}
     {macro?.latest&&<div className="scx-macro-stat"><div><strong>{macro.latest.value>0?'+':''}{macro.latest.value.toFixed(2)} <small>standard deviations</small></strong><span>{dateMonth(macro.latest.date)} observation · {macro.vintage} revision vintage</span></div><div className="scx-macro-change"><strong>{trend===null?'—':(trend>0?'+':'')+trend.toFixed(2)}</strong><small>change vs prior month<br/>index points</small></div></div>}
     {macro?.series.length? <div className="scx-history" role="img" aria-label={'Last '+macro.series.length+' monthly NY Fed global supply chain pressure index observations'}>
       {macro.series.map((m,i)=>{
         const size=Math.min(48,Math.max(1,Math.abs(m.value)*14));
         return <div className="scx-month" key={m.date} title={dateMonth(m.date)+' · '+m.value.toFixed(2)+' standard deviations'}><div className="scx-barwrap"><span className={m.value>=0?'up':'down'} style={{top:m.value>=0?(50-size)+'%':'50%',height:size+'%'}}/></div><small>{i%3===0||i===macro.series.length-1?dateMonth(m.date):''}</small></div>;
       })}
       </div>:null}
     <div className="scx-method"><ShieldCheck size={16}/> {macro?.note||'Source-published monthly data only. No index observations invented when the publisher is unavailable.'}</div>
   </section>
   <section className="scx-panel" aria-label="UN Comtrade bilateral imports">
     <header><span className="sc-eyebrow"><Database size={14}/> 04 / VERIFIED COUNTRY DEPENDENCIES</span><a href="https://comtradeplus.un.org/en/api-docs" target="_blank" rel="noopener noreferrer">UN COMTRADE / API <ArrowUpRight size={13}/></a></header>
     <h2>What does the U.S. import from {countryCode==='all'?'other countries?':(countryName||countryCode)+'?'}</h2>
     <p>Compare historical U.S.-reported imports from the selected country with the same commodity's U.S. imports from all partners. The global country selector controls this comparison.</p>
     <div className="scx-groups" aria-label="Select merchandise group">{groups.map(([hs,label])=><button key={hs} type="button" className={commodity===hs?'selected':''} onClick={()=>setCommodity(hs)}>{label}</button>)}</div>
     {countryCode==='all'?<div className="scx-note">Choose a country in the header to inspect a verified bilateral merchandise comparison. No assumed partner is selected.</div>:
       tradeLoading?<div className="scx-note">Checking annual country and world trade observations…</div>:
       (tradeError||trade?.status!=='observed')?<div className="scx-note scx-warn">{tradeError||trade?.warning||'No validated paired import statistics for this country and product.'}</div>:
       trade&&<div className="scx-trade-stats"><div className="scx-trade-share"><span>SHARE OF U.S. IMPORTS FROM {trade.partner.toUpperCase()}</span><strong>{trade.sharePct===null?'—':trade.sharePct.toFixed(2)+'%'}</strong><small>{trade.product} · {trade.year} reporting year</small></div><div className="scx-trade-amounts"><div><span>From {trade.partner}</span><strong>{usd(trade.partnerValue)}</strong></div><div><span>From all partners (world)</span><strong>{usd(trade.worldValue)}</strong></div></div></div>}
     <div className="scx-method"><Globe2 size={16}/> Imports are reported by the U.S. and may include re-exports, valuation differences, revisions, and indirect supply relationships. A high import share is exposure context, not evidence of a current shortage or of a particular shipping route.</div>
   </section>
   <div className="scx-foot"><span>Separate frequencies: PortWatch daily estimates · NY Fed GSCPI monthly · Comtrade annual merchandise reporting.</span><button type="button" onClick={()=>setRetry(v=>v+1)} disabled={macroLoading||tradeLoading}><RefreshCcw size={13}/> Recheck context</button></div>
 </div>;
}
