import {readBusinessDocument} from './document-formats.mjs';
// Bounded local extraction. Documents are data; no model or network is used.
export function extractDocument(text, filename) {
 if(typeof text!=="string"||text.length>200000)throw Error("Use a text or CSV document under 200 KB.");
 const lines=text.replace(/^\uFEFF/,"").split(/\r?\n/);
 const facts=[];
 for(let i=0;i<lines.length;i++){
  const match=lines[i].match(/^\s*(supplier|vendor|country|product|currency|invoice date|delivery terms|total)\s*[:,]\s*(.{1,300})$/i);
  if(match)facts.push({field:match[1].toLowerCase(),value:match[2].trim().replace(/^"|"$/g,""),line:i+1});
 }
 return {filename:String(filename).slice(0,160),facts,preview:lines.slice(0,100).join("\n")};
}
function validateLocation(l){if(!l||typeof l!=="object"||Array.isArray(l))throw Error("Invalid source location.");const out={};for(const k of ["page","line"]){if(l[k]!==undefined){if(!Number.isInteger(l[k])||l[k]<1||l[k]>100000)throw Error("Invalid source location.");out[k]=l[k];}}for(const k of ["sheet","cells"]){if(l[k]!==undefined){if(typeof l[k]!=="string"||l[k].length>300)throw Error("Invalid source location.");out[k]=l[k];}}return out;}
export function validateProvenance(p){
 if(p==null)return null;
 if(!p||p.kind!=="document-reviewed"||typeof p.filename!=="string"||p.filename.length>160||!/^\d{4}-\d{2}-\d{2}T/.test(p.approvedAt)||!Array.isArray(p.facts)||p.facts.length>100)throw Error("Invalid document provenance.");
 for(const f of p.facts)if(!f||typeof f.field!=="string"||f.field.length>40||typeof f.value!=="string"||f.value.length>300||!Number.isInteger(f.line)||f.line<1)throw Error("Invalid extracted fact.");
 return {kind:p.kind,factStatus:"raw-extraction-not-approved",filename:p.filename,approvedAt:p.approvedAt,facts:p.facts.map(f=>({field:f.field,value:f.value,line:f.line,...(f.location?{location:validateLocation(f.location)}:{})}))};
}
export function setupDocuments({mount,approve,products}){
 const el=(tag,text)=>{const n=document.createElement(tag);if(text)n.textContent=text;return n;};
 mount.append(el("h2","Private document review"),el("p","Open a supplier invoice or equivalent TXT/CSV document locally. Extracted source facts remain an unapproved transcription. Approval applies only to the dependency label, country and product mapping you review below. Text-based PDF and XLSX are processed locally. Scanned documents have no OCR support; enter verified facts manually. Invoice totals are never treated as monthly costs."));
 const file=el("input");file.type="file";file.accept=".txt,.csv,.pdf,.xlsx";file.setAttribute("aria-label","Business document");
 const preview=el("pre"),status=el("p"),name=el("input"),country=el("input"),product=el("select"),button=el("button","Approve as new dependency");
 preview.style.whiteSpace="pre-wrap";preview.style.overflowWrap="anywhere";
 name.maxLength=80;country.maxLength=2;
 for(const [value,label] of [["","Not mapped"],...Object.entries(products)]){const o=el("option",label);o.value=value;product.append(o);}
 for(const [caption,control] of [["Supplier or dependency label",name],["Confirmed country (ISO alpha-2)",country],["Confirmed product group",product]]){const label=el("label",caption);label.append(control);mount.append(label);}
 let draft=null,generation=0;button.type="button";button.disabled=true;
 file.onchange=async()=>{const run=++generation;draft=null;button.disabled=true;preview.textContent="";name.value="";country.value="";product.value="";try{const f=file.files[0];if(!f)return;const parsed=await readBusinessDocument(f);if(run!==generation)return;if(parsed.status!=="text-extracted")throw Error(parsed.limitation);draft=extractDocument(parsed.text,f.name);draft.facts=draft.facts.map(f=>({...f,location:parsed.locations.find(l=>l.line===f.line)||{line:f.line}}));draft.limitation=parsed.limitation;preview.textContent=draft.preview;name.value=draft.facts.find(x=>["supplier","vendor"].includes(x.field))?.value.slice(0,80)||"";const c=draft.facts.find(x=>x.field==="country")?.value||"";country.value=/^[A-Za-z]{2}$/.test(c)?c:"";status.textContent=draft.facts.map(x=>`${x.field}: ${x.value} (${x.location?.page?"page "+x.location.page:x.location?.sheet?x.location.sheet+" "+x.location.cells:"line "+x.line})`).join(" · ")||"No labeled facts extracted. Review the document preview and map fields manually.";status.textContent+=(draft.limitation?" · "+draft.limitation:"");button.disabled=false;}catch(e){if(run===generation)status.textContent=e.message;}};
 button.onclick=()=>{try{if(!draft)throw Error("Open a document first.");if(!name.value.trim())throw Error("Enter a dependency label.");if(country.value&&!/^[A-Za-z]{2}$/.test(country.value))throw Error("Use a two-letter country code.");approve({id:crypto.randomUUID(),name:name.value.trim(),country:country.value.toUpperCase(),product:product.value,corridor:"",monthlyCost:null,provenance:{kind:"document-reviewed",filename:draft.filename,approvedAt:new Date().toISOString(),facts:draft.facts.slice(0,100)}});button.disabled=true;draft=null;status.textContent="Approved dependency added. Analyze exposures, then explicitly save with the encrypted vault to retain it.";}catch(e){status.textContent=e.message;}};
 mount.append(file,status,preview,button);
 return {reset(){generation++;draft=null;file.value="";preview.textContent="";status.textContent="";button.disabled=true;name.value="";country.value="";product.value="";}};
}
