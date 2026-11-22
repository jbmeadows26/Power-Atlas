import { Activity, ArrowUpRight, BookOpen, Layers3, ShieldCheck } from 'lucide-react';
import './countryDefenseSnapshot.css';

/** Explicit country tags only. A publisher's jurisdiction is not the subject country. */
export type CountryDefenseDataset = {
  assessments: Array<{id:string;title:string;agency:string;countries:string[];published:string;url:string;government?:string;finding?:string}>;
  operations: Array<{id:string;title:string;roles:Array<{code:string;role:string}>;published:string;url:string;state?:string;publisher?:string}>;
  assets: Array<{id:string;code:string;name:string;quantity:string;published:string;url:string;publisher?:string;category?:string;detail?:string;status?:string;observationYear?:number}>;
};

export function defenseForCountry(data:CountryDefenseDataset|null|undefined,code:string) {
  if(!data || !code || code==='all') return {assessments:[],operations:[],assets:[]};
  return {
    assessments:data.assessments.filter(a=>a.countries.includes(code)),
    operations:data.operations.filter(o=>o.roles.some(role=>role.code===code)),
    assets:data.assets.filter(a=>a.code===code),
  };
}

export function defenseCounts(data:CountryDefenseDataset|null|undefined,code:string) {
  const records=defenseForCountry(data,code);
  return {assessments:records.assessments.length,operations:records.operations.length,assets:records.assets.length};
}

const indexed=(n:number)=>n===0?'Not indexed':n+' indexed';
type Branch='reports'|'operations'|'assets';

export default function CountryDefenseSnapshot({code,name,data,unavailable=false,onSelect}:{
  code:string;name:string;data:CountryDefenseDataset|null|undefined;unavailable?:boolean;onSelect?:(category:Branch)=>void;
}) {
  const records=defenseForCountry(data,code);
  const loading=!data&&!unavailable;
  const groups=[
    {id:'reports' as Branch,title:'Allied intelligence assessments',icon:BookOpen,count:records.assessments.length,
      items:records.assessments.slice(0,2).map(a=>({id:a.id,title:a.title,meta:(a.government||a.agency)+' · '+a.published,url:a.url}))},
    {id:'operations' as Branch,title:'Military operations',icon:Activity,count:records.operations.length,
      items:records.operations.slice(0,2).map(o=>({id:o.id,title:o.title,meta:o.published+' · '+(o.roles.find(role=>role.code===code)?.role||'Country-linked context'),url:o.url}))},
    {id:'assets' as Branch,title:'Military capabilities & assets',icon:Layers3,count:records.assets.length,
      items:records.assets.slice(0,3).map(a=>({id:a.id,title:a.quantity+' '+a.name,meta:(a.publisher||'Attributed public estimate')+' · '+a.published+(a.status?' · '+a.status.replaceAll('-',' '):''),url:a.url}))},
  ];
  return <section className="cds-root" aria-label={name+' country defense intelligence card'}>
    <div className="cds-head">
      <div><span className="cds-kicker"><ShieldCheck size={14}/> COUNTRY-SPECIFIC SOURCE INDEX · {code}</span>
        <h3>{name}: military & allied intelligence</h3>
        <p>Explicit country-linked public records. Source publishers may be from other countries; the publisher is not the subject. No live unit tracking or inferred counts.</p>
      </div>
      <span className="cds-status">{loading?'Loading library':unavailable?'Source unavailable':'Sourced snapshots'}</span>
    </div>
    <div className="cds-grid">{groups.map(group=>{
      const Icon=group.icon;
      return <article className="cds-panel" key={group.id}>
        <div className="cds-panel-head">
          <Icon size={18}/>
          <div>{onSelect?<button type="button" onClick={()=>onSelect(group.id)}>{group.title} <ArrowUpRight size={12}/></button>:<strong>{group.title}</strong>}
            <small>{loading?'Checking catalog…':unavailable?'Unavailable':indexed(group.count)}</small>
          </div>
        </div>
        {data&&group.items.length>0?<div className="cds-references">{group.items.map(item=><a href={item.url} target="_blank" rel="noopener noreferrer" key={item.id} title={'Open original source for '+item.title}>
          <strong>{item.title}</strong><small>{item.meta}</small><span>Original source <ArrowUpRight size={12}/></span>
        </a>)}</div>:<p className="cds-empty">{loading?'Checking source records…':unavailable?'Source coverage could not be checked.': 'No country-specific source value indexed. This does not mean zero equipment or zero activity.'}</p>}
      </article>;
    })}</div>
    <p className="cds-method">Coverage reflects only indexed records and their publication dates. Assessments, reported roles and inventory estimates have different evidentiary status; the links preserve the underlying source for scrutiny.</p>
  </section>;
}
