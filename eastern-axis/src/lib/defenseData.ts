import {api} from './api';

export type AssetEntry={
 id:string;code:string;category:string;name:string;quantity:string;unit:string;
 published:string;publisher:string;url:string;basis:string;detail:string;
 value?:number;status?:string;estimate?:boolean;observationYear?:number;
};
export type DefenseCatalog={
 reviewedAsOf:string;mode:string;assets:AssetEntry[];assessments:any[];operations:any[];
 sources:Array<{id:string;name:string;group:string;what:string;url:string}>;
 caveats:string[];inventoryHealth?:unknown;
};
type Supplemental={
 reviewedAsOf:string;generatedAt:string;assets:AssetEntry[];
 sources:DefenseCatalog['sources'];collectionHealth?:unknown;
};
const empty=():DefenseCatalog=>({reviewedAsOf:'',mode:'Partial source library',assessments:[],operations:[],assets:[],sources:[],caveats:[]});
const dedupe=<T extends {id:string}>(items:T[]):T[]=>Array.from(new Map(items.map(item=>[item.id,item])).values());

/** An HTTP success is not a usable catalog unless its critical collections exist. */
const validCatalog=(value:unknown):value is DefenseCatalog=>{
 if(!value||typeof value!=='object')return false;
 const row=value as Partial<DefenseCatalog>;
 return Array.isArray(row.assets)&&Array.isArray(row.assessments)&&Array.isArray(row.operations)&&Array.isArray(row.sources);
};
const validSupplemental=(value:unknown):value is Supplemental=>{
 if(!value||typeof value!=='object')return false;
 const row=value as Partial<Supplemental>;
 return Array.isArray(row.assets)&&Array.isArray(row.sources);
};

/** Static source-attributed estimates remain visible when the Neon API is unavailable. */
export async function loadDefenseCatalog():Promise<{data:DefenseCatalog;apiFailed:boolean;inventoryFailed:boolean}>{
 const settled=await Promise.allSettled([
   api.get<DefenseCatalog>('/api/defense-intel'),
   fetch(import.meta.env.BASE_URL+'analysis/military-inventory.json',{cache:'no-store'})
     .then(async res=>{if(!res.ok)throw new Error('Static inventory HTTP '+res.status);return await res.json() as Supplemental;})
 ]);
 const receivedPrimary=settled[0].status==='fulfilled'?settled[0].value.data:null;
 const receivedSecondary=settled[1].status==='fulfilled'?settled[1].value:null;
 const primary=validCatalog(receivedPrimary)?receivedPrimary:null;
 const secondary=validSupplemental(receivedSecondary)?receivedSecondary:null;
 if(!primary&&!secondary)throw new Error('Neither catalog source is available');
 const source=primary||empty();
 return {data:{
   ...source,
   assets:dedupe([...(source.assets||[]),...(secondary?.assets||[])]),
   sources:dedupe([...(source.sources||[]),...(secondary?.sources||[])]),
   assessments:source.assessments||[],operations:source.operations||[],
   caveats:source.caveats||[],
   inventoryHealth:secondary?.collectionHealth,
   reviewedAsOf:secondary?.reviewedAsOf||source.reviewedAsOf
 },apiFailed:!primary,inventoryFailed:!secondary};
}
