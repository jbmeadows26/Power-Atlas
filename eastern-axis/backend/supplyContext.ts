/**
 * Source-validated, keyless public context for the Supply Chain dashboard.
 * A country comparison is United States' imports from that partner, NOT
 * a causal claim that a PortWatch corridor supplied any of those imports.
 */
const FED_CSV='https://www.newyorkfed.org/medialibrary/research/interactives/data/gscpi/gscpi_interactive_data.csv';
const FED_HOME='https://www.newyorkfed.org/research/policy/gscpi';
const COMTRADE='https://comtradeapi.un.org/public/v1/preview/C/A/HS';
const COUNTRY_REF='https://comtradeapi.un.org/files/v1/app/reference/Reporters.json';
const PRODUCT_CODES:Record<string,string>={
 TOTAL:'All merchandise', '27':'Mineral fuels and energy', '85':'Electrical machinery and equipment',
 '31':'Fertilizers','10':'Cereals and grains','26':'Ores and concentrates',
 '72':'Iron and steel','90':'Optical, medical and precision equipment'
};
const validAmount=(v:unknown):v is number=>typeof v==='number'&&Number.isFinite(v)&&v>=0;
const timeout=()=>AbortSignal.timeout(9000);
const quoteSplit=(line:string)=>{
 const cells:string[]=[];let cell='',inside=false;
 for(let i=0;i<line.length;i++){
   const c=line[i];
   if(c==='"'&&inside&&line[i+1]==='"'){cell+='"';i++;}
   else if(c==='"')inside=!inside;
   else if(c===','&&!inside){cells.push(cell.trim());cell='';}
   else cell+=c;
 }
 cells.push(cell.trim());return cells;
};
const monthCodes:Record<string,number>={Jan:1,Feb:2,Mar:3,Apr:4,May:5,Jun:6,Jul:7,Aug:8,Sep:9,Oct:10,Nov:11,Dec:12};
function fedDate(input:string):string|null{
 const m=input.match(/^(\d{1,2})-([A-Za-z]{3})-(\d{4})$/);
 if(!m||!monthCodes[m[2]])return null;
 const yy=Number(m[3]),mm=monthCodes[m[2]],dd=Number(m[1]);
 const date=new Date(Date.UTC(yy,mm-1,dd));
 if(date.getUTCFullYear()!==yy||date.getUTCMonth()!==mm-1||date.getUTCDate()!==dd)return null;
 return date.toISOString().slice(0,10);
}
let fedCache:{until:number;value:ReturnType<typeof parseFed>}|null=null;
function parseFed(csv:string){
 const lines=csv.replace(/^\uFEFF/,'').split(/\r?\n/).filter(Boolean);
 if(lines.length<100)throw new Error('GSCPI dataset unexpectedly short');
 const head=quoteSplit(lines[0]);
 if(head[0]!=='Date'||head.length<3)throw new Error('GSCPI vintage header changed');
 const vintage=head[head.length-1];
 if(!/^[A-Za-z]{3}-\d\d$/.test(vintage))throw new Error('GSCPI latest vintage label unrecognized');
 const observations:{date:string;value:number}[]=[];
 for(const row of lines.slice(1)){
   const cells=quoteSplit(row);
   const date=fedDate(cells[0]||'');
   const value=Number(cells[head.length-1]);
   if(!date||!cells[head.length-1]?.trim()||!Number.isFinite(value)||value < -15 || value>15)continue;
   observations.push({date,value:Math.round(value*1000)/1000});
 }
 observations.sort((a,b)=>a.date.localeCompare(b.date));
 const today=new Date().toISOString().slice(0,10);
 const unique=new Map<string,number>();
 for(const row of observations){if(row.date<=today)unique.set(row.date,row.value);}
 const series=[...unique].map(([date,value])=>({date,value}));
 if(series.length<100)throw new Error('GSCPI latest vintage has insufficient observations');
 const latest=series[series.length-1],previous=series[series.length-2];
 if(new Date(latest.date+'T00:00:00Z').getTime()<Date.UTC(2018,0,1))throw new Error('GSCPI observations are not recent enough');
 return {status:(Date.now()-Date.parse(latest.date+'T00:00:00Z'))/86400000>125?'stale':'observed',
   checkedAt:new Date().toISOString(),vintage,latest,previous,series:series.slice(-18),totalPeriods:series.length,
   source:FED_HOME,download:FED_CSV,unit:'standard deviations from long-run average',
   note:'Monthly global index from NY Fed, latest published revision vintage. Not a freight price, country risk score, real-time port alert or causal proof.'};
}
export async function readSupplyMacro(){
 const now=Date.now();
 if(fedCache&&fedCache.until>now)return fedCache.value;
 try{
   const response=await fetch(FED_CSV,{signal:timeout(),headers:{Accept:'text/csv'}});
   if(!response.ok)throw new Error('New York Fed source HTTP '+response.status);
   const body=await response.text();
   if(body.length>5000000)throw new Error('GSCPI response size exceeds guard');
   const value=parseFed(body);
   fedCache={until:now+60*60*1000,value};
   return value;
 }catch(e){
   return {status:'unavailable',checkedAt:new Date().toISOString(),vintage:null,latest:null,previous:null,
     series:[],totalPeriods:0,source:FED_HOME,download:FED_CSV,unit:'standard deviations',
     note:'NY Fed monthly observations not verified; no values substituted.',
     warning:e instanceof Error?e.message:'Source request failed'};
 }
}

type Reporter={reporterCode?:number;reporterCodeIsoAlpha2?:string;reporterDesc?:string;entryExpiredDate?:string;isGroup?:boolean};
let refCache:{until:number;map:Map<string,Reporter>}|null=null;
async function reporterDirectory(){
 if(refCache&&refCache.until>Date.now())return refCache.map;
 const r=await fetch(COUNTRY_REF,{signal:timeout(),headers:{Accept:'application/json'}});
 if(!r.ok)throw new Error('Comtrade reference HTTP '+r.status);
 const json=await r.json() as {results?:Reporter[]};
 if(!Array.isArray(json.results)||json.results.length<180)throw new Error('Comtrade reference schema changed');
 const map=new Map<string,Reporter>();
 for(const row of json.results){
   if(/^[A-Z]{2}$/.test(row.reporterCodeIsoAlpha2||'')&&
     Number.isInteger(row.reporterCode)&&!row.entryExpiredDate&&!row.isGroup){
     map.set(row.reporterCodeIsoAlpha2!,row);
   }
 }
 if(map.size<150)throw new Error('Comtrade active country reference list incomplete');
 refCache={until:Date.now()+24*60*60*1000,map};
 return map;
}
type TradeRow={refYear?:number;period?:string|number;reporterCode?:number;partnerCode?:number;
  partner2Code?:number;flowCode?:string;cmdCode?:string;primaryValue?:number;customsCode?:string;
  motCode?:number;classificationSearchCode?:string;isAggregate?:boolean};
function selectValue(rows:TradeRow[],partnerCode:number,hs:string,year:number):number|null{
 const filtered=rows.filter(r=>r.reporterCode===842 && r.partnerCode===partnerCode &&
   r.flowCode==='M' && String(r.cmdCode).toUpperCase()===hs &&
   Number(r.refYear||r.period)===year && (r.partner2Code===0||r.partner2Code==null) &&
   (r.customsCode==='C00'||r.customsCode==null) && (r.motCode===0||r.motCode==null) &&
   validAmount(r.primaryValue));
 if(filtered.length!==1)return null;
 return filtered[0].primaryValue!;
}
type TradeResult={status:string;countryCode:string;partner:string;hs:string;product:string;year:number|null;
  partnerValue:number|null;worldValue:number|null;sharePct:number|null;source:string;checkedAt:string;warning?:string;method:string};
const tradeCache=new Map<string,{until:number;value:TradeResult}>();
export async function readTradeDependency(code:string,hs:string):Promise<TradeResult|null>{
 if(!/^[A-Z]{2}$/.test(code)||!(hs in PRODUCT_CODES))return null;
 const checkedAt=new Date().toISOString();
 const base={countryCode:code,partner:code,hs,product:PRODUCT_CODES[hs],source:'https://comtradeplus.un.org/',
   checkedAt,method:'U.S.-reported annual merchandise imports by named partner divided by U.S.-reported imports from World, same HS commodity and year (USD). Historical, not present-day shipment tracking.'};
 const cached=tradeCache.get(code+':'+hs);
 if(cached&&cached.until>Date.now())return cached.value;
 if(code==='US')return {...base,status:'not-applicable',year:null,partnerValue:null,worldValue:null,sharePct:null,
   warning:'Choose a foreign partner; U.S. domestic production is not an international import partner.'};
 try{
   const lookup=await reporterDirectory();
   const partner=lookup.get(code);
   if(!partner||!Number.isInteger(partner.reporterCode))return {...base,status:'no-reference',year:null,partnerValue:null,worldValue:null,sharePct:null,
     warning:'No current official UN Comtrade partner code for this jurisdiction.'};
   const common={...base,partner:partner.reporterDesc||code};
   let observed:TradeResult|null=null;
   for(const year of [2025,2024,2023]){
     const query=new URLSearchParams({reporterCode:'842',period:String(year),partnerCode:'0,'+partner.reporterCode,
       cmdCode:hs,flowCode:'M',maxRecords:'25'});
     const url=COMTRADE+'?'+query.toString();
     const response=await fetch(url,{signal:timeout(),headers:{Accept:'application/json'}});
     if(!response.ok){if(response.status===429)throw new Error('Comtrade public API rate limit reached');continue;}
     const body=await response.json() as {data?:TradeRow[];error?:unknown;count?:number};
     if(!Array.isArray(body.data))continue;
     if(body.data.length>25)continue; // Never infer a full comparison from a truncated sample.
     const world=selectValue(body.data,0,hs,year);
     const chosen=selectValue(body.data,partner.reporterCode!,hs,year);
     if(world===null||chosen===null||world<=0||chosen>world)continue;
     observed={...common,status:'observed',year,partnerValue:Math.round(chosen),
       worldValue:Math.round(world),sharePct:Math.round(10000*chosen/world)/100};
     break;
   }
   const value=observed||{...common,status:'not-reported',year:null,partnerValue:null,worldValue:null,sharePct:null,
     warning:'No complete world-and-partner matched annual import comparison for 2023–2025 from the public preview API.'};
   tradeCache.set(code+':'+hs,{until:Date.now()+2*60*60*1000,value});
   return value;
 }catch(e){
   return {...base,status:'unavailable',year:null,partnerValue:null,worldValue:null,sharePct:null,
     warning:e instanceof Error?e.message:'Comtrade request unavailable'};
 }
}
