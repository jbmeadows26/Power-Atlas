/**
 * Official DOJ FARA bulk intake. FARA registration and representation are
 * DISCLOSURES, not misconduct, nationality or government-control findings.
 * Never attribute an agency relationship beyond the published foreign-principal row.
 */
import { createHash } from 'node:crypto';
import { inflateRawSync } from 'node:zlib';
import type { IntakeRecord } from './collector.js';

const ROOT='https://efile.fara.gov';
const BULK_REG=ROOT+'/bulk/zip/FARA_All_Registrants.csv.zip';
const BULK_PRINCIPALS=ROOT+'/bulk/zip/FARA_All_ForeignPrincipals.csv.zip';
const ACTIVE_API=ROOT+'/api/v1/Registrants/json/Active';
const MAX_DOWNLOAD=7_000_000;
const MAX_EXPANDED=32_000_000;
const countryTags:Record<string,string>={
 'RUSSIA':'RU','RUSSIAN FEDERATION':'RU','CHINA':'CN','PEOPLE S REPUBLIC OF CHINA':'CN',
 'IRAN':'IR','ISLAMIC REPUBLIC OF IRAN':'IR','NORTH KOREA':'KP','KOREA, NORTH':'KP',
 'CUBA':'CU','VENEZUELA':'VE','BELARUS':'BY','KAZAKHSTAN':'KZ','KYRGYZSTAN':'KG',
 'TAJIKISTAN':'TJ','UKRAINE':'UA','UNITED KINGDOM':'GB','UNITED STATES':'US',
 'INDIA':'IN','SAUDI ARABIA':'SA','UNITED ARAB EMIRATES':'AE','TURKEY':'TR',
 'ISRAEL':'IL','CANADA':'CA','FRANCE':'FR','GERMANY':'DE','JAPAN':'JP',
 'MEXICO':'MX','BRAZIL':'BR','QATAR':'QA','AUSTRALIA':'AU','SOUTH AFRICA':'ZA',
 'KOREA, SOUTH':'KR','SOUTH KOREA':'KR','TAIWAN':'TW','GEORGIA':'GE',
 'PAKISTAN':'PK','EGYPT':'EG','VIETNAM':'VN','INDONESIA':'ID','ARGENTINA':'AR',
 'AZERBAIJAN':'AZ','POLAND':'PL','ETHIOPIA':'ET','MYANMAR':'MM','SYRIA':'SY',
 'IRAQ':'IQ','SUDAN':'SD','YEMEN':'YE','LEBANON':'LB','ARMENIA':'AM',
 'HUNGARY':'HU','THAILAND':'TH','MALAYSIA':'MY','SINGAPORE':'SG',
 'UZBEKISTAN':'UZ','TURKMENISTAN':'TM','PALESTINE':'PS'
};
const focus=new Set(['RU','CN','IR','KP','BY','CU','VE','KZ','KG','TJ']);
type Principal={name:string;country:string;countryCode?:string;source:string};
type FaraResult={rows:IntakeRecord[];examined:number;method:string;registrants:number;matchedPrincipals:number;sourceUrls:string[];sourceHashes:Record<string,string>};
const sha=(bytes:Buffer)=>createHash('sha256').update(bytes).digest('hex');
const cleaned=(s:any)=>String(s??'').replace(/\s+/g,' ').trim().slice(0,220);
const iso=(s:any)=>{
 const value=String(s??'').trim();
 if(/^\d{2}\/\d{2}\/\d{4}$/.test(value)){const [m,d,y]=value.split('/');return y+'-'+m+'-'+d;}
 return /^\d{4}-\d{2}-\d{2}/.test(value)?value.slice(0,10):'';
};
const normalizeCountry=(s:string)=>{
 const name=cleaned(s).toUpperCase().normalize('NFKD').replace(/[\u0300-\u036f]/g,'').replace(/\s+/g,' ').trim();
 return countryTags[name];
};
function parseCsv(source:string):Array<Record<string,string>> {
 const lines:string[][]=[];let fields:string[]=[],field='',quote=false;
 for(let i=0;i<source.length;i++){
  const c=source[i];
  if(c==='"'){if(quote&&source[i+1]==='"'){field+='"';i++;}else quote=!quote;}
  else if(c===','&&!quote){fields.push(field);field='';}
  else if((c==='\n'||c==='\r')&&!quote){
   if(c==='\r'&&source[i+1]==='\n')i++;
   fields.push(field);field='';if(fields.length>1)lines.push(fields);fields=[];
  }else field+=c;
 }
 if(field||fields.length){fields.push(field);lines.push(fields);}
 const hdr=lines.shift()?.map(x=>x.replace(/^\uFEFF/,'').trim())||[];
 if(!hdr.includes('Registration_Number'))throw Error('FARA bulk CSV missing registration key');
 return lines.map(row=>Object.fromEntries(hdr.map((h,i)=>[h,row[i]||''])));
}
function unpackCsv(zip:Buffer):Buffer {
 // Locate central directory so ZIP data descriptors are parsed correctly.
 let end=-1;
 for(let i=zip.length-22;i>=Math.max(0,zip.length-65557);i--){
  if(zip.readUInt32LE(i)===0x06054b50){end=i;break;}
 }
 if(end<0)throw Error('DOJ bulk archive has no ZIP central directory');
 const count=zip.readUInt16LE(end+10);
 let off=zip.readUInt32LE(end+16);
 if(count<1||count>50)throw Error('Unexpected number of ZIP members');
 for(let i=0;i<count;i++){
  if(off+46>zip.length||zip.readUInt32LE(off)!==0x02014b50)throw Error('Invalid ZIP member header');
  const method=zip.readUInt16LE(off+10), size=zip.readUInt32LE(off+20), expanded=zip.readUInt32LE(off+24);
  const n=zip.readUInt16LE(off+28),e=zip.readUInt16LE(off+30),c=zip.readUInt16LE(off+32);
  const local=zip.readUInt32LE(off+42);
  const filename=zip.subarray(off+46,off+46+n).toString('utf8');
  off+=46+n+e+c;
  if(!filename.toLowerCase().endsWith('.csv'))continue;
  if(expanded<100||expanded>MAX_EXPANDED||size>MAX_DOWNLOAD)throw Error('FARA CSV size outside safe limits');
  if(local+30>zip.length||zip.readUInt32LE(local)!==0x04034b50)throw Error('Invalid local ZIP header');
  const start=local+30+zip.readUInt16LE(local+26)+zip.readUInt16LE(local+28);
  if(start+size>zip.length)throw Error('Truncated DOJ ZIP member');
  const payload=zip.subarray(start,start+size);
  const result=method===8?inflateRawSync(payload):method===0?payload:undefined;
  if(!result||result.length!==expanded)throw Error('Unsupported/corrupt DOJ ZIP compression');
  return result;
 }
 throw Error('DOJ bulk archive contained no CSV data');
}
async function officialZip(url:string):Promise<{rows:Array<Record<string,string>>;digest:string}> {
 const response=await fetch(url,{headers:{Accept:'application/zip,*/*'},signal:AbortSignal.timeout(18000)});
 if(!response.ok)throw Error('DOJ bulk HTTP '+response.status+' from '+new URL(url).pathname);
 const max=Number(response.headers.get('content-length')||0);
 if(max>MAX_DOWNLOAD)throw Error('FARA ZIP exceeded download ceiling');
 const buffer=Buffer.from(await response.arrayBuffer());
 if(buffer.length>MAX_DOWNLOAD)throw Error('FARA ZIP exceeded transfer ceiling');
 const records=parseCsv(new TextDecoder('iso-8859-1').decode(unpackCsv(buffer)));
 return {rows:records,digest:sha(buffer)};
}
function makeRecord(reg:Record<string,string>,principals:Principal[],at:string,origin:string):IntakeRecord {
 const num=String(reg.Registration_Number).trim();
 const name=cleaned(reg.Name);
 const codes=[...new Set(principals.map(p=>p.countryCode).filter((x):x is string=>!!x))];
 const principalSample=principals.slice(0,6);
 return {
  id:'fara-'+num,sourceId:'fara',sourceRecordId:num,title:name,
  date:iso(reg.Registration_Date),
  summary:principals.length
    ?'Active DOJ FARA registrant. '+principals.length+' published foreign-principal entry/entries in the official source. Countries refer to disclosed foreign-principal locations, NOT the registrant nationality or government direction.'
    :'Active DOJ FARA registration. Foreign-principal details are not independently verified in this record; registration is a disclosure, not evidence of wrongdoing.',
  sourceUrl:ROOT+'/api/v1/RegDocs/json/'+num,
  recordType:'FARA active registration',reviewState:'unreviewed',
  evidenceTier:'original-source-index',collectedAt:at,
  ...(codes.length===1?{countryMention:codes[0],countryRule:'DOJ foreign-principal country/location field; not registrant nationality or state attribution'}:{}),
  countryCodes:codes,
  foreignPrincipals:principalSample,
  faraMethod:origin
 };
}
export async function readFARAOfficial():Promise<FaraResult> {
 const at=new Date().toISOString();
 let bulkError='';
 try{
  const [registrants,foreign]=await Promise.all([officialZip(BULK_REG),officialZip(BULK_PRINCIPALS)]);
  if(registrants.rows.length<4000||foreign.rows.length<2000)throw Error('DOJ bulk dataset incomplete');
  if(!foreign.rows[0]||!Object.prototype.hasOwnProperty.call(foreign.rows[0],'Country/Location_Represented'))throw Error('DOJ foreign-principal CSV schema changed');
  const byNumber=new Map<string,Principal[]>();
  for(const p of foreign.rows){
   const id=String(p.Registration_Number||'').trim();
   if(!/^\d{1,8}$/.test(id)||String(p.Foreign_Principal_Termination_Date||'').trim())continue;
   const name=cleaned(p.Foreign_Principal),country=cleaned(p['Country/Location_Represented']);
   if(!name)continue;
   const list=byNumber.get(id)||[];
   if(list.length<12)list.push({name,country,countryCode:normalizeCountry(country),source:BULK_PRINCIPALS});
   byNumber.set(id,list);
  }
  const active=registrants.rows.filter(r=>/^\d{1,8}$/.test(String(r.Registration_Number||''))&&cleaned(r.Name)&&!String(r.Termination_Date||'').trim());
  if(active.length<150)throw Error('FARA active-registrant completeness check failed');
  active.sort((a,b)=>Number(b.Registration_Number)-Number(a.Registration_Number));
  const featured=active.filter(r=>(byNumber.get(String(r.Registration_Number))||[]).some(p=>p.countryCode&&focus.has(p.countryCode))).slice(0,25);
  const chosen=[...featured,...active.slice(0,55)];
  const unique=[...new Map(chosen.map(r=>[String(r.Registration_Number),r])).values()].slice(0,75);
  return {rows:unique.map(r=>makeRecord(r,byNumber.get(String(r.Registration_Number))||[],at,'DOJ daily bulk CSV')),
   examined:active.length,registrants:active.length,
   matchedPrincipals:unique.filter(r=>(byNumber.get(String(r.Registration_Number))||[]).length>0).length,
   method:'DOJ daily bulk CSV',sourceUrls:[BULK_REG,BULK_PRINCIPALS],
   sourceHashes:{registrants:registrants.digest,foreignPrincipals:foreign.digest}};
 }catch(e){bulkError=e instanceof Error?e.message:'DOJ bulk source failed';}
 // Fallback to the official API. Do not issue repeated bursts of requests
 // against DOJ's documented shared rolling 10-second limit.
 for(let attempt=0;attempt<2;attempt++){
  const response=await fetch(ACTIVE_API,{headers:{Accept:'application/json'},signal:AbortSignal.timeout(12500)});
  if(response.status===429&&attempt===0){await new Promise(resolve=>setTimeout(resolve,11500));continue;}
  if(!response.ok)throw Error('DOJ bulk unavailable ('+bulkError+'); FARA API HTTP '+response.status);
  const raw=await response.text();
  const body=JSON.parse(raw) as {REGISTRANTS_ACTIVE?:{ROW?:Array<Record<string,string>>|Record<string,string>}};
  const field=body.REGISTRANTS_ACTIVE?.ROW;
  const array=Array.isArray(field)?field:field?[field]:[];
  if(array.length<150)throw Error('FARA API returned unexpectedly few active registrants');
  const rows=array.filter(r=>/^\d{1,8}$/.test(String(r.Registration_Number||''))&&cleaned(r.Name))
   .sort((a,b)=>Number(b.Registration_Number)-Number(a.Registration_Number))
   .slice(0,60).map(r=>makeRecord(r,[],at,'DOJ active registrants API; principal details not imported'));
  return {rows,examined:array.length,registrants:array.length,matchedPrincipals:0,
   method:'DOJ active registrants API (degraded: no foreign-principal joins)',sourceUrls:[ACTIVE_API],
   sourceHashes:{activeApi:sha(Buffer.from(raw))}};
 }
 throw Error('Both DOJ FARA sources unavailable ('+bulkError+')');
}
