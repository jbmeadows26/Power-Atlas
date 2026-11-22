import {useEffect,useState} from 'react';
import {ArrowUpRight,BookOpen,ChevronDown,Database,Globe2} from 'lucide-react';
import {MULTILATERAL_SOURCES,countrySourceUrl,iso3Of,multilateralCoverage} from './lib/multilateralSources';
import './multilateralSources.css';

/**
 * Discovery + provenance, not a substitute for ingestion. Every provider is
 * labelled by actual current integration status and methodology limits.
 */
export default function MultilateralSourceGuide({countryCode,context='library'}:{
  countryCode?:string|null;context?:'library'|'factbook';
}){
  const [open,setOpen]=useState(false);
  useEffect(()=>setOpen(false),[countryCode]);
  const country=iso3Of(countryCode);
  const identity=country?'ISO 3166-1 '+String(countryCode).toUpperCase()+' → '+country:
    countryCode&&countryCode!=='all'?'No standardized ISO-3 mapping':'World / all countries';
  return <section className={'ms-guide ms-'+context} aria-label="Official multilateral country data source coverage">
    <div className="ms-top">
      <div className="ms-heading">
        <span><Globe2 size={14}/> COUNTRY DATA / MULTILATERAL SOURCES</span>
        <strong>Official datasets &amp; source coverage</strong>
        <p>Standardized sources for comparison and trend analysis. Links are not evidence of ingestion.</p>
        <small>{identity} · preserve units, methodology, reporting year, reporter and partner roles</small>
      </div>
      <button type="button" aria-expanded={open} onClick={()=>setOpen(value=>!value)}
        className="ms-toggle" aria-label={open?'Hide multilateral data sources':'Explore multilateral data sources'}>
        {open?'Hide sources':'Explore sources'} <ChevronDown size={15} className={open?'ms-chevron-open':''}/>
      </button>
    </div>
    <div className="ms-coverage">
      <span><Database size={13}/><b>{multilateralCoverage.integrated}</b> connected / partial</span>
      <span><BookOpen size={13}/><b>{multilateralCoverage.reference}</b> reference only</span>
      <span><b>{multilateralCoverage.archived}</b> historical archive</span>
    </div>
    {open&&<div className="ms-list">
      {MULTILATERAL_SOURCES.map(item=><article className="ms-item" key={item.id}>
        <div className="ms-line"><strong>{item.name}</strong>
          <span className={'ms-status ms-'+item.status}>{item.status==='connected'?'CONNECTED':item.status==='partial'?'PARTIAL':item.status==='reference'?'REFERENCE ONLY':'ARCHIVED'}</span>
        </div>
        <p>{item.metrics}</p>
        <small>{item.scope}</small>
        <div className="ms-explainer">{item.notes}</div>
        <div className="ms-source-link"><span>{item.access}</span>
          <a target="_blank" rel="noopener noreferrer" href={countrySourceUrl(item.id,countryCode)}
             aria-label={'Open '+item.name+' official source'}>Official source <ArrowUpRight size={13}/></a>
        </div>
      </article>)}
      <p className="ms-limits">
        Source normalization is not an automatic data join. Country IDs use ISO-3166 alpha-3 only when assigned.
        UN M49 numeric area codes, IMF/OECD agency codes, country aggregation, border changes and historical
        territories require independently verified crosswalks. Missing countries or unpublished years are not zero.
      </p>
    </div>}
  </section>;
}
