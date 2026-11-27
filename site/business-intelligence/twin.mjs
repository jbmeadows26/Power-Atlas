import {products,corridors} from "./engine.mjs";
// Local relational records. Relationships are declared, never inferred identities.
export const entityTypes=['dependency','supplier','customer','product','material','contract','inventory','logistics','facility','financial','workforce','technology','objective'];
const bounded=(v,n)=>typeof v==='string'&&v.length>0&&v.length<=n;
export function emptyTwin(){return {version:1,entities:[],relationships:[],history:[]};}
export function validateTwin(t){
 if(!t||t.version!==1||!Array.isArray(t.entities)||!Array.isArray(t.relationships)||!Array.isArray(t.history)||t.entities.length>500||t.relationships.length>1000||t.history.length>2000)throw Error('Invalid or unsupported Digital Twin schema.');
 const ids=new Set();
 const entities=t.entities.map(e=>{if(!e||!bounded(e.id,100)||ids.has(e.id)||!entityTypes.includes(e.type)||!bounded(e.name,160)||!['declared','approved-document','legacy-declared'].includes(e.origin))throw Error('Invalid Digital Twin entity.');ids.add(e.id);const exposure=e.exposure??{country:'',product:'',corridor:''};if(!exposure||typeof exposure.country!=='string'||(exposure.country&&!/^[A-Z]{2}$/.test(exposure.country))||typeof exposure.product!=='string'||(exposure.product&&!Object.hasOwn(products,exposure.product))||typeof exposure.corridor!=='string'||(exposure.corridor&&!corridors.includes(exposure.corridor)))throw Error('Invalid entity exposure mapping.');if(e.provenance!==null&&(typeof e.provenance!=='object'||Array.isArray(e.provenance)||JSON.stringify(e.provenance).length>50000))throw Error('Invalid entity provenance.');return {id:e.id,type:e.type,name:e.name,origin:e.origin,provenance:e.provenance??null,exposure:{country:exposure.country,product:exposure.product,corridor:exposure.corridor}};});
 const links=new Set();const relationships=t.relationships.map(r=>{if(!r||!bounded(r.id,100)||links.has(r.id)||!ids.has(r.from)||!ids.has(r.to)||r.from===r.to||!bounded(r.relation,80))throw Error('Invalid or dangling Digital Twin relationship.');links.add(r.id);return {id:r.id,from:r.from,to:r.to,relation:r.relation};});
 const history=t.history.map(h=>{if(!h||!['migration','entity-created','relationship-created'].includes(h.action)||!bounded(h.id,100)||!bounded(h.at,40)||!Number.isFinite(Date.parse(h.at)))throw Error('Invalid Digital Twin history.');return {action:h.action,id:h.id,at:h.at};});
 return {version:1,entities,relationships,history};
}
export function migrateTwin(profile,now=new Date().toISOString()){
 if(profile.twin!==undefined)return validateTwin(profile.twin);
 const t=emptyTwin();for(const d of profile.dependencies||[]){t.entities.push({id:'dependency:'+d.id,type:'dependency',name:d.name,origin:d.provenance?'approved-document':'legacy-declared',provenance:d.provenance??null});}
 if(t.entities.length)t.history.push({action:'migration',id:'legacy-dependencies',at:now});return validateTwin(t);
}
export function addEntity(t,entity,now=new Date().toISOString()){const next=validateTwin(t);next.entities.push(entity);next.history.push({action:'entity-created',id:entity.id,at:now});return validateTwin(next);}
export function addRelationship(t,relationship,now=new Date().toISOString()){const next=validateTwin(t);next.relationships.push(relationship);next.history.push({action:'relationship-created',id:relationship.id,at:now});return validateTwin(next);}
export function includeDependencies(t,dependencies,now=new Date().toISOString()){
 let next=validateTwin(t);for(const d of dependencies){const id='dependency:'+d.id;if(!next.entities.some(e=>e.id===id))next=addEntity(next,{id,type:'dependency',name:d.name,origin:d.provenance?'approved-document':'declared',provenance:d.provenance??null},now);}return next;
}
// Only explicit depends-on paths participate; free-text relationships remain descriptive.
export function exposureProjection(t){
 const twin=validateTwin(t),dependencies=[],gaps=[];
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
