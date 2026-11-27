// Local-only, deliberately conservative extraction. Never infer household totals from individual bills.
export const MAX_BYTES=10*1024*1024, MAX_TEXT=300000, MAX_PAGES=50;
export const fields={
 gross:{label:"Annual gross household income",profile:true},
 net:{label:"Monthly household take-home income",profile:true},
 expenses:{label:"Total monthly household expenses",profile:true},
 lines:{label:"Wireless voice lines",profile:true},
 due:{label:"Amount due",profile:false},
 monthly:{label:"Explicit monthly charge",profile:false},
 balance:{label:"Statement balance",profile:false},
 dueDate:{label:"Due date (as printed)",profile:false},
 renewal:{label:"Renewal / expiration date",profile:false}
};
const numeric=(v)=>typeof v==="number"&&Number.isFinite(v)&&v>=0&&v<=1e9;
export function validValue(key,v){
 if(key==="dueDate"||key==="renewal"){if(typeof v!=="string"||!/^\d{4}-\d{2}-\d{2}$/.test(v))return false;const d=new Date(v+"T00:00:00Z");return Number.isFinite(+d)&&d.toISOString().slice(0,10)===v;}
 return numeric(v)&&(key!=="lines"||(Number.isInteger(v)&&v>=1&&v<=1000));
}
export function parseAmount(s){
 const t=String(s).trim().replace(/^\$\s*/,"");
 if(!/^(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d{1,2})?$/.test(t))return null;
 const n=Number(t.replaceAll(",",""));return numeric(n)?n:null;
}
function dateValue(s){
 const t=s.trim();let d=t;const m=t.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);if(m)d=m[3]+"-"+m[1].padStart(2,"0")+"-"+m[2].padStart(2,"0");
 return validValue("dueDate",d)?d:null;
}
const rules=[
 ["gross",/^(?:annual gross household income|gross annual household income)\s*[:=]?\s*(.+)$/i],
 ["net",/^(?:monthly household take-home income|monthly household net income|monthly take-home household income)\s*[:=]?\s*(.+)$/i],
 ["expenses",/^(?:total monthly household expenses|monthly household expenses|total monthly household spending)\s*[:=]?\s*(.+)$/i],
 ["lines",/^(?:wireless voice lines|total voice lines|number of voice lines|wireless lines)\s*[:=]?\s*(.+)$/i],
 ["due",/^(?:total amount due|amount due|payment due amount|total due)\s*[:=]?\s*(.+)$/i],
 ["monthly",/^(?:monthly recurring charge|monthly charge|monthly premium|monthly rent|monthly service charge|monthly payment|monthly subscription fee)\s*[:=]?\s*(.+)$/i],
 ["balance",/^(?:statement balance|ending balance|closing balance|new balance)\s*[:=]?\s*(.+)$/i],
 ["dueDate",/^(?:payment due date|due date|payment due on)\s*[:=]?\s*(.+)$/i],
 ["renewal",/^(?:renewal date|lease expiration date|policy expiration date|contract expiration date)\s*[:=]?\s*(.+)$/i]
];
function bounded(t){if(typeof t!=="string"||t.length>MAX_TEXT)throw Error("Text exceeds the local extraction limit.");return t;}
export function extractText(text){
 const rows=[];const lines=bounded(text).split(/\r?\n/).map(x=>x.trim()).filter(Boolean);
 for(let i=0;i<lines.length;i++){
  // Only explicit labels and complete numeric/date values; ambiguous lines remain unparsed.
  for(const [key,re] of rules){
   const match=lines[i].match(re);if(!match)continue;
   const raw=match[1].trim(),v=key==="dueDate"||key==="renewal"?dateValue(raw):parseAmount(raw);
   if(v!==null&&validValue(key,v))rows.push({key,value:v,evidence:"Line "+(i+1)+": "+lines[i].slice(0,180)});
  }
 }
 return rows.slice(0,100);
}
export function extractJSON(text){
 const x=JSON.parse(bounded(text));if(!x||typeof x!=="object"||Array.isArray(x))throw Error("Expected an object with recognized profile fields.");
 return ["gross","net","expenses","lines"].filter(k=>Object.hasOwn(x,k)&&validValue(k,x[k])).map(key=>({key,value:x[key],evidence:"Profile export field: "+key}));
}
// CSV parser handles quoted fields and escaped quotes, rejects malformed and oversized input.
export function parseCSV(text){
 const s=bounded(text).replace(/^\uFEFF/,"");let rows=[],row=[],cell="",quoted=false,closed=false;
 const push=()=>{row.push(cell);cell="";closed=false;if(row.length>100)throw Error("CSV has too many columns.");};
 for(let i=0;i<s.length;i++){
  const ch=s[i];
  if(quoted){if(ch==='"'){if(s[i+1]==='"'){cell+='"';i++;}else{quoted=false;closed=true;}}else cell+=ch;continue;}
  if(ch==='"'){if(cell||closed)throw Error("Malformed CSV quotation.");quoted=true;}
  else if(ch===",")push();
  else if(ch==="\n"||ch==="\r"){if(ch==="\r"&&s[i+1]==="\n")i++;push();if(row.some(v=>v.trim()))rows.push(row);row=[];if(rows.length>10000)throw Error("CSV row limit exceeded.");}
  else {if(closed)throw Error("Malformed CSV field.");cell+=ch;}
 }
 if(quoted)throw Error("Unclosed CSV quotation.");push();if(row.some(v=>v.trim()))rows.push(row);return rows;
}
export function extractCSV(text){
 const rows=parseCSV(text);if(!rows.length)return {candidates:[],note:"Empty CSV."};
 const h=rows[0].map(x=>x.trim().toLowerCase());
 if(h.length===2&&["field","label"].includes(h[0])&&h[1]==="value")return {candidates:extractText(rows.slice(1).filter(r=>r.length===2).map(r=>r.join(": ")).join("\n")),note:"Field/value CSV."};
 const amount=h.indexOf("amount"),date=h.indexOf("date");
 if(amount>=0&&date>=0){return {candidates:[],note:"Detected "+(rows.length-1)+" statement rows. Transaction signs, transfers, duplicates and statement periods need reconciliation; no income or expense total was inferred."};}
 return {candidates:[],note:"Unrecognized CSV layout. Use a field/value export or paste explicitly labeled totals."};
}
export function confirmedProfile(rows){
 const out={};for(const r of rows){if(!fields[r.key]?.profile||!validValue(r.key,r.value))continue;if(Object.hasOwn(out,r.key))throw Error("Choose only one value for each profile field.");out[r.key]=r.value;}return out;
}
