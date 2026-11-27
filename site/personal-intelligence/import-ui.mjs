import {localRecognizer,imageCanvas,recognitionCanvas,MAX_SCAN_PAGES} from "./local-ocr.mjs";
import {MAX_BYTES,MAX_TEXT,MAX_PAGES,fields,validValue,extractText,extractJSON,extractCSV,confirmedProfile} from "./import-engine.mjs";
const $=id=>document.getElementById(id);
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
const fmt=(k,v)=>typeof v==="string"?v:k==="lines"?String(v):new Intl.NumberFormat("en-US",{style:"currency",currency:"USD"}).format(v);
async function pdfText(file,{signal,progress,force}){
 const pdf=await import("./vendor/pdf.mjs");
 pdf.GlobalWorkerOptions.workerSrc=new URL("./vendor/pdf.worker.mjs",import.meta.url).href;
 const task=pdf.getDocument({data:new Uint8Array(await file.arrayBuffer()),isEvalSupported:false,useWasm:false,disableFontFace:true,stopAtErrors:true});
 const abort=()=>{Promise.resolve(task.destroy()).catch(()=>{});};signal.addEventListener("abort",abort,{once:true});if(signal.aborted)abort();
 const ocr=localRecognizer(signal,progress);
 try{
  const doc=await task.promise;if(doc.numPages>MAX_PAGES)throw Error("PDF exceeds the 50-page limit.");
  if(force&&doc.numPages>MAX_SCAN_PAGES)throw Error("Forced OCR is limited to 10 pages. Split the document first.");
  let text="",scans=0;
  for(let p=1;p<=doc.numPages;p++){
   if(signal.aborted)throw Error("Recognition cancelled.");
   const page=await doc.getPage(p);let pageText="",lastY=null;
   try{
    if(!force){
     const data=await page.getTextContent();
     for(const item of data.items){if(typeof item.str!=="string")continue;const y=item.transform?.[5];if(lastY!==null&&Math.abs(y-lastY)>3)pageText+="\n";pageText+=item.str+" ";if(item.hasEOL)pageText+="\n";lastY=y;if(pageText.length>MAX_TEXT)throw Error("PDF text exceeds the extraction limit.");}
    }
    if(force||!pageText.trim()){
     if(++scans>MAX_SCAN_PAGES)throw Error("A maximum of 10 scanned pages can be recognized per import. Split the document first.");
     progress("Preparing scanned PDF page "+p+" of "+doc.numPages+"…");
     const initial=page.getViewport({scale:2.5}),canvas=recognitionCanvas(initial.width,initial.height);
     try{const viewport=page.getViewport({scale:2.5*canvas.width/initial.width});await page.render({canvas,canvasContext:canvas.getContext("2d"),viewport}).promise;
      if(signal.aborted)throw Error("Recognition cancelled.");pageText=await ocr.recognize(canvas);
     }finally{canvas.width=canvas.height=1;}
    }
    text+=pageText+"\n";if(text.length>MAX_TEXT)throw Error("PDF text exceeds the extraction limit.");
   }finally{page.cleanup();}
  }
  if(!text.trim())throw Error("No readable text found. Try a clearer scan or paste relevant text.");
  return {text,scans};
 }finally{signal.removeEventListener("abort",abort);ocr.close();await task.destroy();}
}
async function photoText(file,signal,progress){
 const canvas=await imageCanvas(file);const ocr=localRecognizer(signal,progress);
 try{return await ocr.recognize(canvas);}finally{ocr.close();canvas.width=canvas.height=1;}
}
export function setupImports({apply,onChange}){
 let candidates=[],records=[],generation=0,meta=null,controller=null;
 function status(s){$("import-status").textContent=s;}
 function discard(){controller?.abort();controller=null;generation++;candidates=[];meta=null;$("import-file").value="";$("import-text").value="";$("import-label").value="";$("import-force-ocr").checked=false;$("import-review").replaceChildren();$("import-confirm").disabled=true;$("import-extract").disabled=false;status("Source discarded. Confirmed profile values remain.");}
 function list(){
  const box=$("import-records");box.replaceChildren();
  if(!records.length)box.append(el("p","No reviewed documents in this tab.","muted"));
  records.forEach((r,i)=>{const div=el("div",undefined,"import-document");div.append(el("h3",r.label||r.kind),el("small","User-reviewed · "+r.reviewedAt.slice(0,10)));const ul=el("ul");for(const v of r.values)ul.append(el("li",fields[v.key].label+": "+fmt(v.key,v.value)));div.append(ul);
   const remove=el("button","Remove document","secondary");remove.type="button";remove.onclick=()=>{records.splice(i,1);list();onChange();};div.append(remove);box.append(div);});
 }
 function review(){
  const box=$("import-review");box.replaceChildren();$("import-confirm").disabled=true;
  for(const [i,r] of candidates.entries()){
   const row=el("div",undefined,"import-row"),label=el("label",undefined,"consent"),check=el("input");check.type="checkbox";check.dataset.index=String(i);
   label.append(check,el("span",fields[r.key].label+" — "+fmt(r.key,r.value)));row.append(label,el("small",r.evidence,"evidence-line"));
   check.onchange=()=>{$("import-confirm").disabled=!box.querySelector("input:checked");};box.append(row);
  }
 }
 $("import-extract").onclick=async()=>{
  controller?.abort();controller=new AbortController();const signal=controller.signal,token=++generation;candidates=[];meta=null;review();$("import-extract").disabled=true;status("Extracting locally…");
  try{
   const file=$("import-file").files?.[0],paste=$("import-text").value;
   if(file&&paste.trim())throw Error("Choose a file or pasted text, not both.");
   if(!file&&!paste.trim())throw Error("Select a file or paste text.");
   if(file&&file.size>MAX_BYTES)throw Error("File exceeds 10 MB.");
   let rows=[],note="",kind=$("import-kind").value,label=$("import-label").value.trim();
   if(file){const ext=file.name.split(".").pop().toLowerCase();
    if(ext==="pdf"){const x=await pdfText(file,{signal,force:$("import-force-ocr").checked,progress:s=>{if(token===generation)status(s);}});rows=extractText(x.text);if(x.scans){note="OCR used on "+x.scans+" page(s). Check every candidate against the original.";rows=rows.map(r=>({...r,evidence:"OCR or PDF text · "+r.evidence}));}}
    else if(["jpg","jpeg","png","webp"].includes(ext)){const text=await photoText(file,signal,s=>{if(token===generation)status(s);});rows=extractText(text).map(r=>({...r,evidence:"OCR · "+r.evidence}));note="Photo OCR may misread characters or amounts. Verify against the original.";}
    else if(ext==="json")rows=extractJSON(await file.text());
    else if(ext==="csv"){const x=extractCSV(await file.text());rows=x.candidates;note=x.note;}
    else if(ext==="txt")rows=extractText(await file.text());
    else throw Error("Unsupported file format.");
   }else rows=extractText(paste);
   if(token!==generation)return;candidates=rows;meta={kind,label};review();
   status(rows.length?rows.length+" candidate facts. Review and select only accurate values. "+note:("No supported labeled facts found. "+note+" You may paste explicitly labeled amounts."));
  }catch(e){if(token===generation)status("Extraction unavailable. "+String(e.message||e).slice(0,220));}
  finally{if(token===generation){controller=null;$("import-extract").disabled=false;}}
 };
 $("import-confirm").onclick=()=>{
  try{
   const selected=[...$("import-review").querySelectorAll("input:checked")].map(x=>candidates[Number(x.dataset.index)]).filter(x=>x&&validValue(x.key,x.value));
   if(!selected.length||!meta)return;
   if(records.length>=50)throw Error("Remove an old reviewed document before adding another.");
   const patch=confirmedProfile(selected);if(!apply(patch))return;
   records.push({...meta,reviewedAt:new Date().toISOString(),values:selected.map(({key,value})=>({key,value}))});
   discard();status("Selected facts applied. Raw source discarded. Review your decisions.");list();onChange();
  }catch(e){status(e.message);}
 };
 // Editing a source invalidates any earlier extraction or in-flight result.
 for(const id of ["import-file","import-text","import-kind","import-label","import-force-ocr"]){$(id).addEventListener("input",()=>{controller?.abort();controller=null;generation++;candidates=[];meta=null;review();$("import-extract").disabled=false;status("Source changed. Extract facts again before confirming.");});}
 $("import-discard").onclick=discard;
 $("import-clear").onclick=()=>{records=[];discard();list();onChange();};
 list();
 return {reset(){records=[];discard();list();},findings(){
  return records.flatMap(r=>r.values.filter(v=>!fields[v.key].profile).map(v=>({key:"document",title:(r.label||r.kind)+" · "+fields[v.key].label,status:"User-reviewed document",value:fmt(v.key,v.value),date:null,source:null,detail:"Confirmed from your imported document on "+r.reviewedAt.slice(0,10)+". Not independently verified; payment status, coverage and current terms are unknown."})));
 }};
}
