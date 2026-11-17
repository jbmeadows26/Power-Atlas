import { neon } from '@neondatabase/serverless';
type Doc = Record<string,unknown> & { id:string };
let sql: ReturnType<typeof neon> | undefined;
let readyPromise: Promise<void> | undefined;
function client() {
  if(!process.env.EA_DATABASE_URL) throw Error('EA_DATABASE_URL missing');
  return sql ||= neon(process.env.EA_DATABASE_URL);
}
function ready() {
  return readyPromise ||= client().query('CREATE TABLE IF NOT EXISTS ea_osint_documents (collection text NOT NULL,id text NOT NULL,document jsonb NOT NULL,updated_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(collection,id))',[]).then(()=>{}).catch(e=>{readyPromise=undefined;throw e;});
}
function normalized(item:any):Doc {
  if(!item?.id || typeof item.id!=='string') throw Error('Invalid record ID');
  const value=(item.record && typeof item.record==='object')?item.record:item;
  return {...value,id:item.id};
}
export const db={
  async get<T>(bucket:string,ids:string[],_opts?:unknown):Promise<Array<T|null>> {
    if(!ids.length)return [];
    await ready();
    const rows=await client().query('SELECT id,document FROM ea_osint_documents WHERE collection=$1 AND id=ANY($2::text[])',[bucket,ids]) as Array<{id:string,document:T}>;
    const values=new Map(rows.map(r=>[r.id,r.document]));
    return ids.map(id=>values.get(id)??null);
  },
  async list<T>(bucket:string,options:{limit?:number}={}):Promise<{items:T[]}> {
    await ready();
    const rows=await client().query('SELECT document FROM ea_osint_documents WHERE collection=$1 ORDER BY updated_at DESC LIMIT $2',[bucket,Math.min(1000,Math.max(1,options.limit||100))]) as Array<{document:T}>;
    return {items:rows.map(r=>r.document)};
  },
  tx:{
    async add(bucket:string,items:any[]):Promise<Array<Doc|null>> {
      if(!items.length)return [];
      await ready();
      const docs=items.map(normalized);
      // Batch insertion preserves first observed source records and avoids
      // one Neon round trip per DOJ disclosure.
      const rows=await client().query(
        'INSERT INTO ea_osint_documents(collection,id,document) SELECT $1, x.id, x.doc FROM jsonb_to_recordset($2::jsonb) AS x(id text,doc jsonb) ON CONFLICT DO NOTHING RETURNING id',
        [bucket,JSON.stringify(docs.map(doc=>({id:doc.id,doc})))]
      ) as Array<{id:string}>;
      const saved=new Set(rows.map(row=>row.id));
      return docs.map(doc=>saved.has(doc.id)?doc:null);
    },
    async update(bucket:string,items:any[]):Promise<Doc[]> {
      await ready();const result:Doc[]=[];
      for(const item of items){const doc=normalized(item);await client().query('INSERT INTO ea_osint_documents(collection,id,document) VALUES($1,$2,$3::jsonb) ON CONFLICT(collection,id) DO UPDATE SET document=EXCLUDED.document,updated_at=now()',[bucket,doc.id,JSON.stringify(doc)]);result.push(doc);}
      return result;
    }
  }
};
/* Storage and generative AI fail closed until independent providers are configured. */
export const storage={async write(_items:unknown):Promise<boolean[]>{throw Error('Durable archival storage not configured');}};
export const ai={async generate(_request:unknown):Promise<{text:string}>{throw Error('Independent AI provider not configured');}};
type Ctx={params:Record<string,string>;query:Record<string,string>;body:any};
type Action=(context:Ctx)=>Promise<any>|any;
export const json=(body:unknown)=>({status:200,body});
export const error=(message:string,status=400)=>({status,body:{error:message}});
export function router(routes:Record<string,Action[]>) {
 const handlers=Object.entries(routes).map(([key,actions])=>{
 const i=key.indexOf(' ');return {method:key.slice(0,i),parts:key.slice(i+1).split('/').filter(Boolean),action:actions[0]};
 });
 return async(request:any,response:any)=>{
 const method=String(request.method||'GET').toUpperCase();
 const url=new URL(request.url||'/', 'https://eastern-axis.invalid');
 const parts=url.pathname.split('/').filter(Boolean);
 const target=handlers.find(h=>h.method===method&&h.parts.length===parts.length&&h.parts.every((p,i)=>p.startsWith(':')||p===parts[i]));
 if(!target)return response.status(404).json({error:'Route not found'});
 const params:Record<string,string>={};target.parts.forEach((p,i)=>{if(p.startsWith(':'))params[p.slice(1)]=decodeURIComponent(parts[i]);});
 try{const result=await target.action({params,query:Object.fromEntries(url.searchParams.entries()),body:request.body??null});
 return response.status(typeof result?.status==='number'?result.status:200).json(result?.body??result);}
 catch(e){console.error('Eastern Axis API unavailable',method,url.pathname,e);return response.status(503).json({error:'Source service unavailable; no evidence inferred.'});}
 };
}
