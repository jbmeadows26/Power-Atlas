import {ArrowUpRight,BookOpenCheck,Database,Globe2} from 'lucide-react';
import {countryStatisticalSources,isoAlpha3,sourceTotals} from './lib/countryStatisticalSources';
import './countryStatisticalSources.css';

type Props={countryCode?:string|null;countryName?:string;context?:'country'|'coverage'};
const labels={ingested:'DATA INGESTED',partial:'PARTIAL INGESTION',discovery:'REFERENCE ONLY',archived:'HISTORICAL ARCHIVE'} as const;

export default function CountryStatisticalSources({countryCode,countryName,context='country'}:Props){
 const iso3=isoAlpha3(countryCode);
 const totals=sourceTotals();
 const named=context==='country'?(countryName||countryCode||'Selected archive entity'):'all country data sources';
 return <details className="css-root">
   <summary className="css-trigger">
     <span className="css-icon"><BookOpenCheck size={17}/></span>
     <span className="css-summary-copy">
       <strong>{context==='country'?'Current country statistics & source coverage':'International statistical source coverage'}</strong>
       <small>{totals.ingested} ingested · {totals.partial} partly ingested · {totals.discovery} reference only · {totals.archived} archived</small>
     </span>
     <span className="css-expand">Explore sources</span>
   </summary>
   <div className="css-details">
     <div className="css-guidance">
       <Globe2 size={17}/>
       <p><strong>{named}</strong>{context==='country'&&<> · ISO 3166-1 alpha-3: <strong>{iso3||'No verified standard equivalent'}</strong></>}
         <span> Source directory, not a merged measurement table. An external publisher link is not proof of an active data feed. Only independently dated, labelled observations may appear in charts.</span>
       </p>
     </div>
     <div className="css-source-grid">
       {countryStatisticalSources.map(src=><article className="css-source" key={src.id}>
         <div className="css-source-head"><strong>{src.name}</strong><span>{labels[src.status]}</span></div>
         <p className="css-source-topics">{src.topics}</p>
         <p><strong>Measures:</strong> {src.metricExamples}</p>
         <p className="css-coverage-note">{src.coverageNote}</p>
         <div className="css-source-links"><a href={src.landingUrl} target="_blank" rel="noopener noreferrer">Publisher <ArrowUpRight size={12}/></a>
           <a href={src.apiDocsUrl} target="_blank" rel="noopener noreferrer">{src.status==='archived'?'Archive':'API / methodology'} <ArrowUpRight size={12}/></a></div>
         <small>{src.identifierPolicy}</small>
       </article>)}
     </div>
     <p className="css-foot"><Database size={13}/> Country joins require ISO3/M49 reconciliation and matching measures, units, years, methods, and jurisdictions. Missing source coverage is not a zero reading. Historical CIA statistics are never presented as current.</p>
   </div>
 </details>;
}
