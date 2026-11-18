/**
 * Source-verified public social/climate supplemental observations.
 * Do not blend WID pretax inequality into World Bank survey Gini silently.
 * Original-source year and methodology are part of each observation.
 */
const OWID='https://ourworldindata.org/grapher/';
export type SupplementalPoint={year:string;value:number;sourceUrl:string;sourceName:string;meaning:string;label?:string};
type CsvSpec={slug:string;column:string;meaning:string;sourceName:string};
const sources={
 co2:{slug:'co-emissions-per-capita',column:'CO₂ emissions per capita',meaning:'Territorial fossil-fuel and industry CO₂ emissions per person (tonnes), based on the Global Carbon Budget; not all greenhouse gases or consumption-based emissions.',sourceName:'Our World in Data · Global Carbon Budget'},
 giniWB:{slug:'gini-coefficient-wb',column:'Gini coefficient',meaning:'World Bank Poverty and Inequality Platform survey-based Gini; income/consumption definitions and survey years differ across countries.',sourceName:'World Bank PIP · via Our World in Data'},
 giniWID:{slug:'gini-coefficient-wid',column:'Gini coefficient (before tax)',meaning:'WID pre-tax income distribution Gini; not interchangeable with World Bank survey-based income/consumption Gini.',sourceName:'World Inequality Database · via Our World in Data'}
} satisfies Record<string,CsvSpec>;
type Series=Map<string,{year:string;value:number}>;
const dataCache=new Map<string,{until:number;data:Series}>();
const pending=new Map<string,Promise<Series>>();
const isoCache=new Map<string,{until:number;code:string|null}>();
const nowYear=()=>new Date().getUTCFullYear();
function csvCells(line:string){
 const cells:string[]=[];let value='',inside=false;
 for(let i=0;i<line.length;i++){
  const x=line[i];
  if(x==='"'&&inside&&line[i+1]==='"'){value+='"';i++;}
  else if(x==='"')inside=!inside;
  else if(x===','&&!inside){cells.push(value);value='';}
  else value+=x;
 }
 cells.push(value);
 return cells;
}
export function parseSocialCsv(csv:string,spec:CsvSpec):Series{
 const lines=csv.replace(/^\uFEFF/,'').split(/\r?\n/);
 if(lines.length<50)throw Error('OWID table unexpectedly short: '+spec.slug);
 const header=csvCells(lines[0]);
 if(header[0]!=='Entity'||header[1]!=='Code'||header[2]!=='Year'||header[3]!==spec.column)
  throw Error('OWID schema changed: '+spec.slug);
 const map:Series=new Map();
 let count=0;
 for(const line of lines.slice(1)){
  if(!line)continue;
  const row=csvCells(line);
  if(row.length<4)continue;
  const key=row[1],year=Number(row[2]),value=Number(row[3]);
  if(!/^([A-Z]{3}|OWID_WRL|OWID_KOS)$/.test(key)||!Number.isInteger(year)||
   year<1850||year>nowYear()||row[3]===''||!Number.isFinite(value))continue;
  if(spec.slug==='co-emissions-per-capita'?(value<0||value>500):(value<0||value>1))continue;
  const last=map.get(key);
  if(!last||Number(last.year)<year)map.set(key,{year:String(year),value});
  count++;
 }
 if(count<50||map.size<30)throw Error('OWID public-source coverage guard failed: '+spec.slug);
 return map;
}
async function getSeries(spec:CsvSpec):Promise<Series>{
 const cached=dataCache.get(spec.slug);
 if(cached&&cached.until>Date.now())return cached.data;
 const ongoing=pending.get(spec.slug);
 if(ongoing)return ongoing;
 const task=(async()=>{
  const url=OWID+spec.slug+'.csv?v=1&csvType=full&useColumnShortNames=false';
  const response=await fetch(url,{headers:{Accept:'text/csv'},signal:AbortSignal.timeout(12500)});
  if(!response.ok)throw Error('OWID '+spec.slug+' HTTP '+response.status);
  const length=Number(response.headers.get('content-length')||0);
  if(length>11000000)throw Error('OWID '+spec.slug+' payload too large');
  const csv=await response.text();
  if(csv.length>11000000)throw Error('OWID '+spec.slug+' payload too large');
  const data=parseSocialCsv(csv,spec);
  dataCache.set(spec.slug,{until:Date.now()+2*60*60*1000,data});
  return data;
 })();
 pending.set(spec.slug,task);
 try{return await task;}finally{pending.delete(spec.slug);}
}
async function getISO3(iso2:string):Promise<string|null>{
 if(iso2==='WLD')return 'OWID_WRL';
 if(iso2==='XK')return 'OWID_KOS';
 if(!/^[A-Z]{2}$/.test(iso2))return null;
 const cached=isoCache.get(iso2);
 if(cached&&cached.until>Date.now())return cached.code;
 try{
  const r=await fetch('https://api.worldbank.org/v2/country/'+iso2+'?format=json',{signal:AbortSignal.timeout(7000)});
  if(!r.ok)throw Error('WB country metadata HTTP '+r.status);
  const j=await r.json() as unknown;
  if(!Array.isArray(j)||!Array.isArray(j[1]))throw Error('Invalid WB country metadata');
  const match=j[1].find((x:{iso2Code?:string;id?:string})=>x.iso2Code===iso2);
  const code=typeof match?.id==='string'&&/^[A-Z]{3}$/.test(match.id)?match.id:null;
  isoCache.set(iso2,{until:Date.now()+24*60*60*1000,code});
  return code;
 }catch{return null;}
}
export async function readSocialSupplements(iso2:string):Promise<{
 co2:SupplementalPoint|null;giniWB:SupplementalPoint|null;giniWID:SupplementalPoint|null;
 warnings:string[];
}>{
 const result={co2:null,giniWB:null,giniWID:null,warnings:[]} as {
  co2:SupplementalPoint|null;giniWB:SupplementalPoint|null;giniWID:SupplementalPoint|null;warnings:string[];
 };
 const iso3=await getISO3(iso2);
 if(!iso3){result.warnings.push('The World Bank country identifier could not be mapped to an ISO3 code for alternative-source lookup.');return result;}
 const names=['co2','giniWB','giniWID'] as const;
 const settled=await Promise.allSettled(names.map(name=>getSeries(sources[name])));
 for(let i=0;i<names.length;i++){
  const name=names[i],s=sources[name],r=settled[i];
  if(r.status==='rejected'){result.warnings.push(s.sourceName+' unavailable.');continue;}
  const point=r.value.get(iso3);
  if(!point)continue;
  result[name]={...point,sourceUrl:OWID+s.slug,sourceName:s.sourceName,meaning:s.meaning};
 }
 return result;
}
