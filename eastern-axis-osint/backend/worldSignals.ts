const URL = 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson';
async function readUSGS() {
  const response=await fetch(URL,{signal:AbortSignal.timeout(8500),headers:{Accept:'application/json'}});
  if(!response.ok)throw new Error('USGS feed HTTP '+response.status);
  const raw=await response.json() as {type?:string;metadata?:{generated?:number};
    features?:Array<{id?:string;properties?:{title?:string;time?:number;mag?:number;url?:string};
      geometry?:{type?:string;coordinates?:number[]}}>};
  if(raw.type!=='FeatureCollection'||!Array.isArray(raw.features)||!raw.metadata?.generated)
    throw new Error('USGS feed schema validation failed');
  const events=raw.features.filter(f=>{
    const c=f.geometry?.coordinates;
    return f.geometry?.type==='Point'&&Array.isArray(c)&&c.length>=2&&
      Number.isFinite(c[0])&&Math.abs(c[0])<=180&&Number.isFinite(c[1])&&Math.abs(c[1])<=90&&
      typeof f.properties?.mag==='number'&&f.properties.mag>=4.5&&
      typeof f.properties?.time==='number';
  }).slice(0,35).map(f=>({
    id:String(f.id||''),title:String(f.properties?.title||'USGS earthquake').slice(0,210),
    longitude:f.geometry!.coordinates![0],latitude:f.geometry!.coordinates![1],
    magnitude:f.properties!.mag!,date:new Date(f.properties!.time!).toISOString(),
    source:'USGS',
    sourceUrl:String(f.properties?.url||URL).startsWith('https://earthquake.usgs.gov/')?
      String(f.properties?.url):URL
  }));
  return {status:'ok',source:'USGS',count:events.length,
    checkedAt:new Date().toISOString(),generatedAt:new Date(raw.metadata.generated).toISOString(),
    events,caveat:'USGS source-reported epicenter coordinates. No foreign-state attribution is inferred.'};
}
type NASAEvent = {
  id?: string; title?: string; link?: string;
  categories?: Array<{ id?: string; title?: string }>;
  geometry?: Array<{ date?: string; type?: string; coordinates?: number[] }>;
};
type NASAResult = { events?: NASAEvent[] };
type NaturalSignal = { id:string; title:string; eventType:string; longitude:number; latitude:number; date:string; source:string; sourceUrl:string };
async function readNASA() {
  const url='https://eonet.gsfc.nasa.gov/api/v3/events?status=open&days=14&limit=30';
  const response=await fetch(url,{signal:AbortSignal.timeout(7500),headers:{Accept:'application/json'}});
  if(!response.ok)throw new Error('NASA EONET HTTP '+response.status);
  const data=await response.json() as NASAResult;
  if(!Array.isArray(data.events))throw new Error('NASA EONET schema mismatch');
  const events:NaturalSignal[]=data.events.map(e=>{
    const geo=(e.geometry||[]).filter(g=>g.type==='Point'&&Array.isArray(g.coordinates)&&g.coordinates.length>=2).slice(-1)[0];
    const coords=geo?.coordinates;
    if(!geo||!coords||!Number.isFinite(coords[0])||!Number.isFinite(coords[1])||Math.abs(coords[0])>180||Math.abs(coords[1])>90)return null;
    const timestamp=String(geo.date||'');
    if(!/^\d{4}-\d{2}-\d{2}T/.test(timestamp))return null;
    const id=String(e.id||'').slice(0,100);
    if(!id||!/^[a-zA-Z0-9_-]+$/.test(id))return null;
    return {id:'nasa-'+id,title:String(e.title||'NASA EONET event').slice(0,180),
      eventType:String(e.categories?.[0]?.title||'Natural event').slice(0,80),
      longitude:coords[0],latitude:coords[1],date:timestamp,source:'NASA EONET',
      sourceUrl:'https://eonet.gsfc.nasa.gov/api/v3/events/'+encodeURIComponent(id)};
  }).filter((e):e is NaturalSignal=>e!==null).slice(0,25);
  return {events,examined:data.events.length,checkedAt:new Date().toISOString()};
}
let signalCache: {until:number;value:unknown}|null=null;
export async function readWorldSignals() {
  if(signalCache&&Date.now()<signalCache.until)return signalCache.value;
  const [usgsResult,nasaResult]=await Promise.allSettled([readUSGS(),readNASA()]);
  const usgs=usgsResult.status==='fulfilled'?usgsResult.value:null;
  const nasa=nasaResult.status==='fulfilled'?nasaResult.value:null;
  // A failed NASA service must never turn a healthy USGS response into an
  // apparent USGS outage, nor should missing events be represented as zero.
  const sourceError=(result:PromiseSettledResult<unknown>,fallback:string)=>{
    if(result.status==='fulfilled')return null;
    const reason=result.reason;
    return reason instanceof Error ? reason.message.slice(0,150) : fallback;
  };
  const value={
    status:usgs&&nasa?'ok':usgs||nasa?'partial':'unavailable',
    source:'USGS / NASA EONET',
    count:usgs?.count??0,events:usgs?.events||[],
    checkedAt:new Date().toISOString(),generatedAt:usgs?.generatedAt||'',
    naturalEvents:nasa?.events||[],nasaCheckedAt:nasa?.checkedAt||null,
    usgsStatus:usgs?'ok':'unavailable',nasaStatus:nasa?'ok':'unavailable',
    usgsError:sourceError(usgsResult,'USGS source request failed'),
    nasaError:sourceError(nasaResult,'NASA EONET events request failed'),
    caveat:'USGS epicenters and NASA EONET natural-event locations are publisher-reported coordinates. EONET is an aggregator. These are not independently geolocated, and natural hazards do not establish conflict or foreign-state action.'
  };
  signalCache={until:Date.now()+180000,value};
  return value;
}