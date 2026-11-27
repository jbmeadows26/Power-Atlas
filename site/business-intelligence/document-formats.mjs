// Fixed same-origin parser assets only. Imported documents are never URLs or instructions.
const MAX=10*1024*1024, TEXT_MAX=200000;
const assets='../private-workspace/document-assets/';
function bounded(text){if(text.length>TEXT_MAX)throw Error('Document text exceeds 200 KB. Split the document locally.');return text;}
export function assertSafeXML(text){if(/<!DOCTYPE|<!ENTITY/i.test(text))throw Error('Spreadsheet DTD and entities are unsupported.');}
function xml(text){assertSafeXML(text);const doc=new DOMParser().parseFromString(text,'application/xml');if(doc.querySelector('parsererror'))throw Error('Invalid spreadsheet XML.');return doc;}
export function normalizeCell(value){return String(value).replace(/[\r\n]+/g,' ');}
export function zipEntryFilter(){let bytes=0,count=0;return entry=>{
 if(!Number.isSafeInteger(entry.size)||entry.size<0||!Number.isSafeInteger(entry.originalSize)||entry.originalSize<0||![0,8].includes(entry.compression))throw Error('Invalid or unsupported ZIP entry.');
 if(entry.compression===0&&entry.size!==entry.originalSize)throw Error('Stored ZIP size mismatch.');
 if(++count>2000||entry.size>5*1024*1024||entry.originalSize>5*1024*1024||(bytes+=entry.originalSize)>20*1024*1024)throw Error('Spreadsheet expanded size exceeds local limits.');
 return /^(xl\/worksheets\/sheet\d+\.xml|xl\/sharedStrings\.xml|xl\/workbook\.xml|xl\/_rels\/workbook.xml.rels)$/.test(entry.name);
};}
export function validateDecodedEntries(entries){let bytes=0;for(const data of Object.values(entries)){if(!(data instanceof Uint8Array)||data.length>5*1024*1024||(bytes+=data.length)>20*1024*1024)throw Error('Decoded spreadsheet exceeds local limits.');}return entries;}
export async function readBusinessDocument(file){
 if(!file||file.size>MAX)throw Error('Document exceeds the 10 MB local processing limit.');
 const extension=file.name.split('.').pop().toLowerCase();
 if(['txt','csv'].includes(extension))return {text:bounded(await file.text()),locations:[],format:extension,status:'text-extracted'};
 if(extension==='pdf'){
  const pdfjs=await import(assets+'pdf.mjs');pdfjs.GlobalWorkerOptions.workerSrc=new URL(assets+'pdf.worker.mjs',import.meta.url).href;
  const task=pdfjs.getDocument({data:new Uint8Array(await file.arrayBuffer()),isEvalSupported:false,useSystemFonts:false,disableFontFace:true,stopAtErrors:true});
  try{const pdf=await task.promise;if(pdf.numPages>100)throw Error('PDF exceeds 100 pages. Split the document locally.');
   const lines=[],locations=[];let chars=0;
   for(let page=1;page<=pdf.numPages;page++){const p=await pdf.getPage(page),content=await p.getTextContent();let line='',lastY=null;
    const flush=()=>{if(line.trim()){chars+=line.length;if(chars>TEXT_MAX)throw Error('Document text exceeds 200 KB.');lines.push(line.trim());locations.push({page,line:lines.length});line='';}};
    for(const item of content.items){if(typeof item.str!=='string')continue;const y=item.transform?.[5];if(lastY!==null&&Math.abs(y-lastY)>2)flush();line+=(line?' ':'')+item.str;lastY=y;if(item.hasEOL)flush();}flush();p.cleanup();}
   if(!lines.length)return {text:'',locations:[],format:'pdf',status:'scanned-or-no-text-unsupported',limitation:'No embedded text found. Scanned PDF OCR is not supported locally; provide a text-based PDF or manually enter verified facts.'};
   return {text:bounded(lines.join('\n')),locations,format:'pdf',status:'text-extracted',limitation:'PDF reading order may differ from visual layout; verify each extracted fact against its source page.'};
  }finally{await task.destroy();}
 }
 if(extension==='xlsx'){
  const {unzipSync,strFromU8}=await import(assets+'fflate.mjs');
  const entries=validateDecodedEntries(unzipSync(new Uint8Array(await file.arrayBuffer()),{filter:zipEntryFilter()}));
  const read=name=>entries[name]?xml(strFromU8(entries[name])):null;
  const shared=Array.from(read('xl/sharedStrings.xml')?.getElementsByTagName('si')||[],n=>Array.from(n.getElementsByTagName('t'),t=>t.textContent).join(''));
  const workbook=read('xl/workbook.xml'),rels=read('xl/_rels/workbook.xml.rels');if(!workbook||!rels)throw Error('Unsupported or malformed XLSX workbook.');
  const targets=new Map(Array.from(rels.getElementsByTagName('Relationship'),r=>[r.getAttribute('Id'),r.getAttribute('Target')]));
  const lines=[],locations=[];let cells=0;
  for(const sheet of workbook.getElementsByTagName('sheet')){const name=sheet.getAttribute('name'),target=targets.get(sheet.getAttribute('r:id'));if(!target||target.includes('..'))throw Error('Unsupported worksheet path.');const path=target.startsWith('/')?target.slice(1):'xl/'+target;const doc=read(path);if(!doc)throw Error('Worksheet unavailable or unsupported.');
   for(const row of doc.getElementsByTagName('row')){const values=[],refs=[];for(const cell of row.getElementsByTagName('c')){if(++cells>50000)throw Error('Spreadsheet exceeds 50,000 cells.');const ref=cell.getAttribute('r');if(cell.getElementsByTagName('f').length)continue;const raw=cell.getElementsByTagName('v')[0]?.textContent||'',type=cell.getAttribute('t');const value=type==='s'?shared[Number(raw)]??'':type==='inlineStr'?Array.from(cell.getElementsByTagName('t'),t=>t.textContent).join(''):raw;values.push(normalizeCell(value));refs.push(ref);}
    if(values.some(Boolean)){lines.push(values.join(','));locations.push({sheet:name,cells:refs.join(':'),line:lines.length});bounded(lines.join('\n'));}}
  }
  return {text:lines.join('\n'),locations,format:'xlsx',status:'text-extracted',limitation:'Cell line breaks are normalized to spaces to preserve row locations. Formula cells are excluded and never executed. Dates and currency formatting are not inferred from numeric cells. Review source sheet and cell references.'};
 }
 throw Error('Unsupported format. Use TXT, CSV, text-based PDF or XLSX. Scanned documents require manual entry; OCR is unavailable.');
}
