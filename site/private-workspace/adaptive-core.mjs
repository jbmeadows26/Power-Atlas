export const MAX_ITEMS=24,MAX_QUERY=400,MAX_TEXT=1000;
const words=s=>new Set(String(s).toLowerCase().normalize("NFKC").match(/[\p{L}\p{N}]+/gu)||[]);
export function prepareItems(items){
 if(!Array.isArray(items))return [];
 return items.filter(x=>x&&typeof x.title==="string"&&x.title.trim()).slice(0,MAX_ITEMS).map((x,i)=>({id:i,title:x.title.slice(0,200),text:[x.title,x.detail,x.action,x.status,x.value].filter(v=>typeof v==="string").join(" ").slice(0,MAX_TEXT),status:String(x.status||"Existing finding").slice(0,100)}));
}
export function standardRank(query,items){
 const q=words(query);if(!q.size)return [];
 return items.map(x=>({id:x.id,score:[...q].filter(w=>words(x.text).has(w)).length/q.size})).filter(x=>x.score>0).sort((a,b)=>b.score-a.score||a.id-b.id);
}
export function validateRank(rows,items){
 if(!Array.isArray(rows)||rows.length>items.length)throw Error("Invalid local result");
 const ids=new Set(items.map(x=>x.id)),seen=new Set();
 for(const x of rows){if(!x||!ids.has(x.id)||seen.has(x.id)||typeof x.score!=="number"||!Number.isFinite(x.score)||x.score< -1.001||x.score>1.001)throw Error("Invalid local result");seen.add(x.id);}
 return [...rows].sort((a,b)=>b.score-a.score||a.id-b.id);
}
export async function capabilities(scope=globalThis){
 const n=scope.navigator||{};let gpu=false;
 try{gpu=!!(n.gpu&&await n.gpu.requestAdapter());}catch{}
 return {secure:scope.isSecureContext===true,wasm:typeof scope.WebAssembly==="object",worker:typeof scope.Worker==="function",gpu,memory:typeof n.deviceMemory==="number"?n.deviceMemory:null,cores:typeof n.hardwareConcurrency==="number"?n.hardwareConcurrency:null,saveData:n.connection?.saveData===true};
}
export function eligible(c){return c.secure&&c.wasm&&c.worker&&(c.memory===null||c.memory>=2);}
