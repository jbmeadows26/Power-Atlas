import {parseCSV,parseAmount,validValue} from "./import-engine.mjs";
export const MAX_ROWS=1500;
export const categories=["Unclassified","Groceries","Dining","Housing","Utilities","Telecom","Transport","Insurance","Healthcare","Shopping","Entertainment","Fees","Education","Other expense","Income","Other inflow","Refund","Transfer","Exclude"];
const outflows=new Set(categories.slice(1,14)),inflows=new Set(["Income","Other inflow","Refund"]);
const date=s=>{s=s.trim();const m=s.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);if(m)s=m[3]+"-"+m[1].padStart(2,"0")+"-"+m[2].padStart(2,"0");return validValue("dueDate",s)?s:null;};
export function cents(s){let t=String(s).trim(),sign=1;if(t.startsWith("(")&&t.endsWith(")")){sign=-1;t=t.slice(1,-1).trim();}else if(t[0]==="-"||t[0]==="+"){sign=t[0]==="-"?-1:1;t=t.slice(1).trim();}const n=parseAmount(t);return n===null?null:sign*Math.round(n*100);}
const aliases={date:["date","transaction date","posted date","posting date"],description:["description","merchant","payee","memo","name"],amount:["amount","transaction amount"],debit:["debit","withdrawal","withdrawals"],credit:["credit","deposit","deposits"],id:["transaction id","transaction_id","reference id","reference"],currency:["currency","currency code"]};
const header=s=>s.trim().toLowerCase().replace(/\s+/g," ");
export function suggest(description,amount){
 const s=description.toLowerCase();
 if(/\b(transfer|credit card payment|card payment|autopay payment|payment thank you|payment received)\b/.test(s))return "Transfer";
 if(amount>0){if(/\b(refund|return credit|reversal)\b/.test(s))return "Refund";if(/\b(payroll|salary|direct deposit payroll)\b/.test(s))return "Income";return "Unclassified";}
 if(amount>=0)return "Unclassified";
 for(const [cat,re] of [
 ["Groceries",/\b(grocery|groceries|supermarket|aldi|whole foods|trader joe'?s|kroger|shoprite)\b/],
 ["Dining",/\b(restaurant|coffee|cafe|doordash|ubereats|starbucks|pizza)\b/],
 ["Housing",/\b(rent payment|mortgage payment)\b/],
 ["Utilities",/\b(electric bill|water bill|natural gas bill|electric utility|pseg)\b/],
 ["Telecom",/\b(verizon|t-mobile|at&t|comcast|xfinity|spectrum)\b/],
 ["Transport",/\b(gas station|fuel|shell|exxon|uber trip|lyft|ezpass|parking)\b/],
 ["Insurance",/\b(insurance|geico|progressive insurance)\b/],
 ["Healthcare",/\b(pharmacy|medical|dental|hospital|cvs pharmacy)\b/],
 ["Entertainment",/\b(netflix|spotify|hulu|disney plus|cinema)\b/],
 ["Shopping",/\b(amazon|target|walmart|retail)\b/],
 ["Fees",/\b(overdraft fee|service fee|late fee|interest charge|bank fee)\b/],
 ["Education",/\b(tuition|school fee)\b/]
 ])if(re.test(s))return cat;
 return "Unclassified";
}
export function allowedCategory(cat,amount){return cat==="Unclassified"||cat==="Transfer"||cat==="Exclude"||(amount<0&&outflows.has(cat))||(amount>0&&inflows.has(cat));}
export function parseStatement(text,{account,mode,start,end}){
 if(typeof account!=="string"||!account.trim()||account.length>60)throw Error("Enter a short account nickname, not an account number.");
 account=account.trim().toLowerCase();
 if(!date(start)||date(start)!==start||!date(end)||date(end)!==end||start>end)throw Error("Enter the actual statement start and end dates.");
 if(!["negative-out","positive-out","debit-credit"].includes(mode))throw Error("Select the statement's amount convention.");
 const rows=parseCSV(text);if(rows.length<2)throw Error("CSV contains no transaction rows.");if(rows.length-1>MAX_ROWS)throw Error("At most 1,500 rows per statement.");
 const h=rows[0].map(header),col={};for(const [k,a] of Object.entries(aliases)){const matches=h.map((x,i)=>a.includes(x)?i:-1).filter(i=>i>=0);if(matches.length>1)throw Error("Ambiguous "+k+" columns. Keep one.");col[k]=matches[0]??-1;}
 if(col.date<0||col.description<0||(mode==="debit-credit"?(col.debit<0||col.credit<0):col.amount<0))throw Error("Missing required CSV headers for the selected convention.");
 const seen=new Map(),transactions=[],issues=[];
 for(let i=1;i<rows.length;i++){const r=rows[i],row=i+1,fail=reason=>issues.push({row,reason});if(r.length!==h.length){fail("Column count mismatch");continue;}const d=date(r[col.date]),desc=r[col.description].trim();
 if(!d||d<start||d>end){fail("Invalid or outside-period date");continue;}if(!desc||desc.length>250){fail("Missing or excessively long description");continue;}
 if(col.currency>=0&&r[col.currency].trim().toUpperCase()!=="USD"){fail("Currency not USD");continue;}
 let amount;if(mode==="debit-credit"){const a=r[col.debit].trim()===""?0:cents(r[col.debit]),b=r[col.credit].trim()===""?0:cents(r[col.credit]);if(a===null||b===null||a<0||b<0||(a!==0&&b!==0)){fail("Ambiguous debit/credit");continue;}amount=b-a;}else{const a=cents(r[col.amount]);if(a===null){fail("Invalid amount");continue;}amount=mode==="positive-out"?-a:a;}
 if(!Number.isSafeInteger(amount)||amount===0){fail("Zero or invalid amount");continue;}
 const id=col.id<0?"":r[col.id].trim().slice(0,120),fingerprint=JSON.stringify([account,d,desc.toLowerCase().replace(/\s+/g," "),amount]),identity=id?JSON.stringify([account,id]):fingerprint;
 const duplicate=seen.has(identity)||seen.has(fingerprint);seen.set(identity,row);seen.set(fingerprint,row);
 transactions.push({row,date:d,description:desc,amount,identity,fingerprint,duplicate,suggestion:suggest(desc,amount),category:"Unclassified",reviewed:false});
 }
 return {account,start,end,transactions,issues,rowCount:rows.length-1};
}
export function reviewRows(statement,prior=[]){
 const known=new Set(prior.flatMap(x=>[x.identity,x.fingerprint]));
 return statement.transactions.map(t=>({...t,duplicate:t.duplicate||known.has(t.identity)||known.has(t.fingerprint)}));
}
export function summarize(rows){
 const totals={spend:0,refunds:0,income:0,otherInflow:0,transfer:0,excluded:0,unclassified:0,net:0,byCategory:{}};
 for(const t of rows){if(!t.reviewed||!allowedCategory(t.category,t.amount)||t.category==="Unclassified"){totals.unclassified++;continue;}
 if(t.category==="Exclude"){totals.excluded++;continue;}totals.net+=t.amount;
 if(t.category==="Transfer"){totals.transfer++;continue;}if(t.category==="Refund"){totals.refunds+=t.amount;continue;}if(t.category==="Income"){totals.income+=t.amount;continue;}if(t.category==="Other inflow"){totals.otherInflow+=t.amount;continue;}
 totals.spend-=t.amount;totals.byCategory[t.category]=(totals.byCategory[t.category]||0)-t.amount;}
 return totals;
}
export function reconcile(rows,opening,closing,invalidCount=0){
 if(opening===null||closing===null)return {status:"not provided",difference:null};
 if(invalidCount||rows.some(t=>!t.reviewed||t.category==="Unclassified"))return {status:"incomplete review",difference:null};
 // Excluded rows (duplicates or non-posted entries) are not counted; all posted transfers still affect balance.
 const movement=rows.filter(t=>t.category!=="Exclude").reduce((a,t)=>a+t.amount,0);
 const difference=closing-opening-movement;return {status:difference===0?"matched":"mismatch",difference};
}
export function recurring(rows){
 const groups=new Map();
 for(const t of rows){if(!t.reviewed||!outflows.has(t.category))continue;const merchant=t.description.toLowerCase().replace(/\s+/g," ").trim();const key=JSON.stringify([t.account,merchant,t.category]);if(!groups.has(key))groups.set(key,[]);groups.get(key).push(t);}
 const out=[];
 for(const group of groups.values()){group.sort((a,b)=>a.date.localeCompare(b.date));const dates=new Set(group.map(t=>t.date));if(group.length<3||dates.size!==group.length||new Set(group.map(t=>t.date.slice(0,7))).size!==group.length)continue;
 const amounts=group.map(t=>-t.amount),min=Math.min(...amounts),max=Math.max(...amounts);if(max-min>Math.max(100,min*.1))continue;
 const intervals=group.slice(1).map((t,i)=>(Date.parse(t.date)-Date.parse(group[i].date))/86400000);if(intervals.some(n=>n<25||n>35))continue;
 out.push({description:group[0].description,category:group[0].category,account:group[0].account,count:group.length,latest:group.at(-1).date,amount:-group.at(-1).amount});
 }
 return out;
}
