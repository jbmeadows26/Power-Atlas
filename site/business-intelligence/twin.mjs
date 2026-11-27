import {products,corridors} from "./engine.mjs";
// Local relational records. Relationships are declared, never inferred identities.
export const entityTypes=['dependency','supplier','customer','product','sku','material','contract','inventory','logistics','facility','financial','workforce','technology','objective'];
const stamp=v=>{if(v==null)return null;if(typeof v!=='string'||!Number.isFinite(Date.parse(v)))throw Error('Invalid change timestamp.');return v;};
const fields=['quantity','reorderPoint','unitPrice','monthlyCost','currency','unit','renewalDate','deliveryDate','obligation','carrier','port','location'];
function attributes(v={}){if(!v||typeof v!=='object'||Array.isArray(v))throw Error('Invalid business attributes.');const out={};for(const [k,x] of Object.entries(v)){if(!fields.includes(k))throw Error('Unsupported business field.');if(['quantity','reorderPoint','unitPrice','monthlyCost'].includes(k)){if(x!==null&&(typeof x!=='number'||!Number.isFinite(x)||x<0||x>1e12))throw Error('Invalid quantity or cost.');}else if(typeof x!=='string'||x.length>1000)throw Error('Invalid business field.');if(k==='currency'&&x&&!/^[A-Z]{3}$/.test(x))throw Error('Use a three-letter currency.');if(['renewalDate','deliveryDate'].includes(k)&&x&&(!/^\d{4}-\d{2}-\d{2}$/.test(x)||!Number.isFinite(Date.parse(x))||new Date(x).toISOString().slice(0,10)!==x))throw Error('Invalid business date.');out[k]=x;}return out;}
function snapshot(v){if(!v||typeof v!=='object'||JSON.stringify(v).length>60000)throw Error('Invalid historical snapshot.');return JSON.parse(JSON.stringify(v));}
const bounded=(v,n)=>typeof v==='string'&&v.length>0&&v.length<=n;
export function emptyTwin(){return {version:2,entities:[],relationships:[],history:[]};}
export function validateTwin(t){
 if(!t||![1,2].includes(t.version)||!Array.isArray(t.entities)||!Array.isArray(t.relationships)||!Array.isArray(t.history)||t.entities.length>500||t.relationships.length>1000||t.history.length>2000)throw Error('Invalid or unsupported Digital Twin schema.');
 const ids=new Set();
 const entities=t.entities.map(e=>{if(!e||!bounded(e.id,100)||ids.has(e.id)||!entityTypes.includes(e.type)||!bounded(e.name,160)||!['declared','approved-document','legacy-declared'].includes(e.origin))throw Error('Invalid Digital Twin entity.');if(e.archived!==undefined&&typeof e.archived!=='boolean')throw Error('Invalid archive state.');if(e.lastChangeOrigin!==undefined&&!['declared-correction','declared','approved-document','legacy-declared'].includes(e.lastChangeOrigin))throw Error('Invalid change origin.');ids.add(e.id);const exposure=e.exposure??{country:'',product:'',corridor:''};if(!exposure||typeof exposure.country!=='string'||(exposure.country&&!/^[A-Z]{2}$/.test(exposure.country))||typeof exposure.product!=='string'||(exposure.product&&!Object.hasOwn(products,exposure.product))||typeof exposure.corridor!=='string'||(exposure.corridor&&!corridors.includes(exposure.corridor)))throw Error('Invalid entity exposure mapping.');if(e.provenance!==null&&(typeof e.provenance!=='object'||Array.isArray(e.provenance)||JSON.stringify(e.provenance).length>50000))throw Error('Invalid entity provenance.');return {id:e.id,type:e.type,name:e.name,origin:e.origin,lastChangeOrigin:e.lastChangeOrigin==='declared-correction'?'declared-correction':e.origin,archived:e.archived===true,updatedAt:stamp(e.updatedAt),attributes:attributes(e.attributes),provenance:e.provenance?snapshot(e.provenance):null,exposure:{country:exposure.country,product:exposure.product,corridor:exposure.corridor}};});
 const links=new Set();const relationships=t.relationships.map(r=>{if(!r||!bounded(r.id,100)||links.has(r.id)||!ids.has(r.from)||!ids.has(r.to)||r.from===r.to||!bounded(r.relation,80))throw Error('Invalid or dangling Digital Twin relationship.');links.add(r.id);return {id:r.id,from:r.from,to:r.to,relation:r.relation};});
 const history=t.history.map(h=>{if(!h||!['migration','entity-created','relationship-created','entity-updated','entity-archived','entity-restored','entity-removed','relationship-removed'].includes(h.action)||!bounded(h.id,100)||!bounded(h.at,40)||!Number.isFinite(Date.parse(h.at)))throw Error('Invalid Digital Twin history.');return {action:h.action,id:h.id,at:h.at,...(h.before?{before:snapshot(h.before)}:{}),...(h.after?{after:snapshot(h.after)}:{})};});
 return {version:2,entities,relationships,history};
}
export function migrateTwin(profile,now=new Date().toISOString()){
 if(profile.twin!==undefined)return validateTwin(profile.twin);
 const t=emptyTwin();for(const d of profile.dependencies||[]){t.entities.push({id:'dependency:'+d.id,type:'dependency',name:d.name,origin:d.provenance?'approved-document':'legacy-declared',provenance:d.provenance??null});}
 if(t.entities.length)t.history.push({action:'migration',id:'legacy-dependencies',at:now});return validateTwin(t);
}
export function addEntity(t,entity,now=new Date().toISOString()){const next=validateTwin(t);next.entities.push({...entity,updatedAt:stamp(now)});next.history.push({action:'entity-created',id:entity.id,at:now});return validateTwin(next);}
export function addRelationship(t,relationship,now=new Date().toISOString()){const next=validateTwin(t);next.relationships.push(relationship);next.history.push({action:'relationship-created',id:relationship.id,at:now});return validateTwin(next);}
export function includeDependencies(t,dependencies,now=new Date().toISOString()){
 let next=validateTwin(t);const live=new Set(dependencies.map(d=>'dependency:'+d.id));
 for(const e of next.entities.filter(e=>e.type==='dependency'&&!live.has(e.id))){for(const r of next.relationships.filter(r=>r.from===e.id||r.to===e.id))next=removeRelationship(next,r.id,now);next.entities=next.entities.filter(x=>x.id!==e.id);next.history.push({action:'entity-removed',id:e.id,at:now,before:e});}
 for(const d of dependencies){const id='dependency:'+d.id,record={id,type:'dependency',name:d.name,origin:d.provenance?'approved-document':'declared',provenance:d.provenance??null},index=next.entities.findIndex(e=>e.id===id);if(index<0)next=addEntity(next,record,now);else if(next.entities[index].name!==record.name||JSON.stringify(next.entities[index].provenance)!==JSON.stringify(record.provenance)){const before=next.entities[index];next.entities[index]={...before,...record,updatedAt:now};next.history.push({action:'entity-updated',id,at:now,before});}}
 return validateTwin(next);
}
// Only explicit depends-on paths participate; free-text relationships remain descriptive.
export function exposureProjection(t){
 const all=validateTwin(t),active=new Set(all.entities.filter(e=>!e.archived).map(e=>e.id)),twin={...all,entities:all.entities.filter(e=>active.has(e.id)),relationships:all.relationships.filter(r=>active.has(r.from)&&active.has(r.to))},dependencies=[],gaps=[];
 for(const root of twin.entities.filter(e=>e.type!=='dependency')){
  const reached=new Set(),visit=id=>{if(reached.has(id))return;reached.add(id);for(const r of twin.relationships.filter(r=>r.from===id&&r.relation==='depends-on'))visit(r.to);};visit(root.id);
  const nodes=twin.entities.filter(e=>reached.has(e.id)),values=key=>[...new Set(nodes.map(e=>e.exposure?.[key]).filter(Boolean))];
  const countries=values('country'),products=values('product'),corridors=values('corridor');
  if([countries,products,corridors].some(v=>v.length>1)){gaps.push(root.name+': multiple exposure values on dependency paths; mapping withheld.');continue;}
  if(!countries.length&&!products.length&&!corridors.length){gaps.push(root.name+': no supported country, product or corridor mapping.');continue;}
  dependencies.push({id:'twin:'+root.id,name:root.name,country:countries[0]||'',product:products[0]||'',corridor:corridors[0]||'',monthlyCost:null,provenance:null,twinPath:[...reached]});
 }
 return {dependencies,gaps};
}

export function updateEntity(t,id,patch,now=new Date().toISOString()){
 const next=validateTwin(t),index=next.entities.findIndex(e=>e.id===id);if(index<0)throw Error('Entity no longer exists.');
 if(Object.keys(patch).some(k=>!['name','exposure','attributes'].includes(k)))throw Error('Identity, origin and source provenance cannot be overwritten.');
 const before=next.entities[index];if(before.type==='dependency')throw Error('Edit the original dependency form, not its graph mirror.');next.entities[index]={...before,...patch,lastChangeOrigin:'declared-correction',updatedAt:stamp(now)};next.history.push({action:'entity-updated',id,at:now,before,after:snapshot(next.entities[index])});return validateTwin(next);
}
export function archiveEntity(t,id,archived=true,now=new Date().toISOString()){
 const next=validateTwin(t),e=next.entities.find(e=>e.id===id);if(!e)throw Error('Entity no longer exists.');if(e.type==='dependency')throw Error('Manage this record through the original dependency form.');next.history.push({action:archived?'entity-archived':'entity-restored',id,at:now,before:snapshot(e)});e.archived=archived;e.updatedAt=stamp(now);return validateTwin(next);
}
export function removeEntity(t,id,now=new Date().toISOString()){
 const next=validateTwin(t),e=next.entities.find(e=>e.id===id);if(!e)throw Error('Entity no longer exists.');if(e.type==='dependency')throw Error('Remove the original dependency form record first.');if(next.relationships.some(r=>r.from===id||r.to===id))throw Error('Remove linked relationships before removing this entity.');next.entities=next.entities.filter(e=>e.id!==id);next.history.push({action:'entity-removed',id,at:now,before:e});return validateTwin(next);
}
export function removeRelationship(t,id,now=new Date().toISOString()){
 const next=validateTwin(t),r=next.relationships.find(r=>r.id===id);if(!r)throw Error('Relationship no longer exists.');next.relationships=next.relationships.filter(r=>r.id!==id);next.history.push({action:'relationship-removed',id,at:now,before:r});return validateTwin(next);
}
export function twinGaps(t){return validateTwin(t).entities.filter(e=>!e.archived).flatMap(e=>{const out=[];if(!Object.values(e.exposure).some(Boolean))out.push(e.name+': no supported exposure mapping');if(e.type==='inventory'&&e.attributes.quantity==null)out.push(e.name+': inventory quantity unavailable');if(e.type==='contract'&&!e.attributes.renewalDate)out.push(e.name+': renewal date unavailable');return out;});}

export function twinCompleteness(t){const active=validateTwin(t).entities.filter(e=>!e.archived);const relevant={inventory:['quantity','unit','reorderPoint'],contract:['renewalDate','obligation'],supplier:['location'],facility:['location'],financial:['monthlyCost','currency'],logistics:['carrier','port']};let known=0,applicable=0;for(const e of active)for(const field of relevant[e.type]||[]){applicable++;if(e.attributes[field]!==undefined&&e.attributes[field]!==null&&e.attributes[field]!=='')known++;}return {known,applicable,ratio:applicable?known/applicable:null};}
