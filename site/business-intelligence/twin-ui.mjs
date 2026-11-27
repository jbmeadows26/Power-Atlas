import {entityTypes,emptyTwin,validateTwin,addEntity,addRelationship} from './twin.mjs';
export function setupTwin(mount){
 let twin=emptyTwin();const el=(tag,text)=>{const n=document.createElement(tag);if(text)n.textContent=text;return n;};
 mount.append(el('h2','Business relationships'),el('p','Declare business entities and their relationships locally. These records describe your business; they do not establish external supplier identity or automatically expand intelligence coverage. Save explicitly in the encrypted vault.'));
 const type=el('select'),name=el('input'),from=el('select'),to=el('select'),relation=el('input'),status=el('p'),list=el('ul');name.maxLength=160;relation.maxLength=80;
 const label=(text,control)=>{const l=el('label',text);l.append(control);mount.append(l);};for(const value of entityTypes){const o=el('option',value);o.value=value;type.append(o);}label('Entity type',type);label('Entity name',name);
 const add=el('button','Add declared entity');add.type='button';mount.append(add);label('From entity',from);label('Relationship (for example supplies)',relation);label('To entity',to);const link=el('button','Add declared relationship');link.type='button';mount.append(link,status,list);
 function render(){list.replaceChildren();from.replaceChildren();to.replaceChildren();for(const e of twin.entities){list.append(el('li',`${e.type}: ${e.name} · ${e.origin}`));for(const select of [from,to]){const o=el('option',e.name+' ('+e.type+')');o.value=e.id;select.append(o);}}for(const r of twin.relationships)list.append(el('li',`${twin.entities.find(e=>e.id===r.from).name} → ${r.relation} → ${twin.entities.find(e=>e.id===r.to).name}`));status.textContent=`${twin.entities.length} entities · ${twin.relationships.length} relationships · schema ${twin.version}`;}
 add.onclick=()=>{try{twin=addEntity(twin,{id:crypto.randomUUID(),type:type.value,name:name.value.trim(),origin:'declared',provenance:null});name.value='';render();}catch(e){status.textContent=e.message;}};
 link.onclick=()=>{try{twin=addRelationship(twin,{id:crypto.randomUUID(),from:from.value,to:to.value,relation:relation.value.trim()});relation.value='';render();}catch(e){status.textContent=e.message;}};
 render();return {get:()=>validateTwin(twin),restore(t){twin=validateTwin(t);render();},reset(){twin=emptyTwin();name.value='';relation.value='';render();}};
}
