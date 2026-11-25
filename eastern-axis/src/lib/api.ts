export type ApiResult<T = any> = { data: T; fallbackCapturedAt?:string };

const apiOrigin = String(import.meta.env.VITE_EA_API_ORIGIN || '').trim().replace(/\/$/, '');
const pagesTarget = import.meta.env.VITE_EA_TARGET === 'github-pages';
const inflight=new Map<string,Promise<ApiResult<any>>>();
const mirrorPaths=new Set(['/api/overview',...['WLD','US','CN','RU','IR'].map(code=>'/api/global-systems/'+code)]);
const signal=(path:string,capturedAt?:string)=>{if(typeof window!=='undefined')window.dispatchEvent(new CustomEvent('ea-api-fallback',{detail:{path,capturedAt}}));};
class HttpError extends Error{status:number;constructor(status:number,message:string){super(message);this.status=status;}}
async function fetchJson(url:string,method:'GET'|'POST',payload?:unknown){
 const controller=new AbortController();
 const timer=setTimeout(()=>controller.abort(),15000);
 try{
   const res=await fetch(url,{method,credentials:apiOrigin?'omit':'same-origin',
    headers:{Accept:'application/json',...(method==='POST'?{'Content-Type':'application/json'}:{})},
    ...(method==='POST'?{body:JSON.stringify(payload??{})}:{}),cache:'no-store',signal:controller.signal});
   if(!res.ok)throw new HttpError(res.status,'API request failed ('+res.status+')');
   const data=await res.json();
   if(!data||typeof data!=='object')throw Error('Unexpected JSON response');
   return data;
 }finally{clearTimeout(timer);}
}
function validMirror(path:string,data:any){
 if(path==='/api/overview')return Array.isArray(data?.countries)&&data.countries.length>=195&&Array.isArray(data.cases)&&Array.isArray(data.sources);
 return data?.code===path.split('/').at(-1)&&Array.isArray(data.indicators)&&data.indicators.length===12&&data.indicators.every((x:any)=>x.value==null||(typeof x.value==='number'&&Number.isFinite(x.value)&&x.year&&x.sourceUrl));
}
async function request<T=any>(path:string,method:'GET'|'POST',payload?:unknown):Promise<ApiResult<T>>{
 if(!path.startsWith('/api/'))throw Error('Unexpected API path');
 if(pagesTarget&&!apiOrigin)throw Error('Eastern Axis live API is not connected. Source data is unavailable, not zero.');
 const url=apiOrigin?apiOrigin+path:path;
 try{
   let data:any;
   try{data=await fetchJson(url,method,payload);}
   catch(error){
     if(method==='POST'||(error instanceof HttpError&&error.status<500))throw error;
     data=await fetchJson(url,method,payload);
   }
   if(mirrorPaths.has(path)&&!validMirror(path,data))throw Error('Invalid or mismatched API response');
   if(method==='GET')signal(path);
   return {data:data as T};
 }catch(error){
   // Only the intentionally published public read-only catalog and baselines.
   // Never fallback for writes, explicit authorization failures or arbitrary paths.
   if(!pagesTarget||method!=='GET'||!mirrorPaths.has(path)||(error instanceof HttpError&&error.status<500))throw error;
   const mirrorUrl=String(import.meta.env.BASE_URL||'/')+'api-fallback/'+path.slice(5).replaceAll('/','-')+'.json';
   try{
     const mirror=await fetchJson(mirrorUrl,'GET');
     if(mirror.path!==path||!Number.isFinite(Date.parse(mirror.capturedAt))||!validMirror(path,mirror.data))throw Error('Invalid release snapshot');
     signal(path,mirror.capturedAt);
     return {data:mirror.data as T,fallbackCapturedAt:mirror.capturedAt};
   }catch{throw error;}
 }
}
export const api={
 get:<T=any>(path:string):Promise<ApiResult<T>>=>{
   const existing=inflight.get(path);if(existing)return existing;
   const promise=request<T>(path,'GET').finally(()=>inflight.delete(path));inflight.set(path,promise);return promise;
 },
 post:<T=any>(path:string,payload?:unknown)=>request<T>(path,'POST',payload)
};
