import {parseStatement,reviewRows,allowedCategory,categories,cents,summarize,reconcile,recurring} from "./transaction-engine.mjs";
import {MAX_BYTES} from "./import-engine.mjs";
const $=id=>document.getElementById(id);
const el=(tag,text,cls)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;};
const dollars=n=>new Intl.NumberFormat("en-US",{style:"currency",currency:"USD"}).format(n/100);
const inputIds=["tx-account","tx-start","tx-end","tx-mode","tx-opening","tx-closing","tx-file"];
export function setupTransactions({onChange}){
 let statements=[],draft=null,generation=0;
 const status=s=>$("tx-status").textContent=s;
 const allRows=()=>statements.flatMap(s=>s.rows);
 function reviewState(){
  const rows=draft?.rows||[],pending=rows.filter(r=>!r.reviewed||r.category==="Unclassified").length,invalid=draft?.issues.length||0;
  const rec=draft?reconcile(rows,draft.opening,draft.closing,invalid):null;
  $("tx-review-status").textContent=draft?pending+" of "+rows.length+" rows awaiting confirmation; "+invalid+" invalid. Balance check: "+rec.status+(rec.difference===null?"":" ("+dollars(rec.difference)+" difference)")+".":"";
  $("tx-approve").disabled=!draft||!rows.some(r=>!r.reviewed&&!r.duplicate&&r.suggestion!=="Unclassified"&&r.suggestion!=="Transfer"&&r.suggestion!=="Refund");
  $("tx-commit").disabled=!draft||invalid>0||pending>0||!rows.length;
 }
 function renderReview(){
  const box=$("tx-review"),issues=$("tx-issues");box.replaceChildren();issues.replaceChildren();
  if(!draft){reviewState();return;}
  if(draft.issues.length){issues.append(el("p","Correct the source CSV before adding this statement.","muted"));for(const issue of draft.issues.slice(0,20))issues.append(el("p","Row "+issue.row+": "+issue.reason,"tx-note"));}
  for(const t of draft.rows){
   const row=el("div",undefined,"tx-row"),title=el("h3",t.description),amount=el("p",t.date+" · "+dollars(t.amount));
   row.append(title,amount,el("small",(t.duplicate?"Possible duplicate — review against previous statement. ":"")+"Suggested: "+t.suggestion,"tx-note"));
   const select=el("select");select.setAttribute("aria-label","Category for row "+t.row);
   for(const cat of categories.filter(c=>allowedCategory(c,t.amount))){const option=el("option",cat);option.value=cat;select.append(option);}
   select.value=t.category;
   const label=el("label",undefined,"consent"),check=el("input");check.type="checkbox";check.checked=t.reviewed;check.disabled=t.category==="Unclassified";label.append(check,el("span","Confirm row "+t.row));
   select.onchange=()=>{t.category=select.value;t.reviewed=false;check.checked=false;check.disabled=t.category==="Unclassified";reviewState();};
   check.onchange=()=>{t.reviewed=check.checked&&t.category!=="Unclassified";reviewState();};
   row.append(select,label);box.append(row);
  }
  reviewState();
 }
 function invalidate(){generation++;draft=null;$("tx-extract").disabled=false;renderReview();}
 function discard(){invalidate();for(const id of inputIds)$(id).value="";status("Draft discarded. Reviewed statements remain.");}
 function renderSummary(){
  const rows=allRows(),s=summarize(rows),box=$("tx-summary");box.replaceChildren();
  const periods=statements.map(x=>x.start+" – "+x.end),start=statements.map(x=>x.start).sort()[0],end=statements.map(x=>x.end).sort().at(-1);
  $("tx-coverage").textContent=statements.length?statements.length+" reviewed statement(s) · "+new Set(statements.map(x=>x.account)).size+" account(s) · "+start+" to "+end+". Periods may overlap or have gaps; not total household finances.":"No reviewed statements. Not a complete household budget.";
  for(const [name,value] of [["Gross categorized outflows",s.spend],["Refunds / credits",s.refunds],["Identified income",s.income],["Other inflows",s.otherInflow]]){const item=el("div");item.append(el("small",name),el("strong",statements.length?dollars(value):"—"));box.append(item);}
  const cats=$("tx-categories");cats.replaceChildren();for(const [cat,amount] of Object.entries(s.byCategory).sort((a,b)=>b[1]-a[1])){const line=el("div",undefined,"measure"),heading=el("div");heading.append(el("span",cat),el("strong",dollars(amount)));const bar=el("progress");bar.max=s.spend||1;bar.value=amount;bar.setAttribute("aria-label",cat);line.append(heading,bar);cats.append(line);}
  if(statements.length)cats.append(el("p",s.transfer+" reviewed transfer(s); "+s.excluded+" excluded row(s).","tx-note"));
  const list=$("tx-statements");list.replaceChildren();if(!statements.length)list.append(el("p","No statements reviewed.","muted"));
  statements.forEach((x,i)=>{const card=el("div",undefined,"tx-row");card.append(el("h3",x.account),el("p",periods[i]+" · "+x.rows.length+" rows"),el("small","Balance check: "+x.balance.status+(x.balance.difference===null?"":" · difference "+dollars(x.balance.difference)),"muted"));const b=el("button","Remove statement","secondary");b.type="button";b.onclick=()=>{statements.splice(i,1);invalidate();renderSummary();onChange();};card.append(b);list.append(card);});
  const rec=$("tx-recurring");rec.replaceChildren();const candidates=recurring(rows);if(!candidates.length)rec.append(el("p","No reviewed recurring candidates yet.","muted"));for(const x of candidates){const card=el("div",undefined,"tx-row");card.append(el("h3",x.description),el("p",dollars(x.amount)+" latest observed · "+x.count+" charges"),el("small",x.account+" · "+x.category+" · last "+x.latest,"muted"));rec.append(card);}
 }
 for(const id of inputIds)$(id).addEventListener("input",()=>{invalidate();status("Source changed. Review again.");});
 $("tx-extract").onclick=async()=>{invalidate();const token=generation;$("tx-extract").disabled=true;try{
  const file=$("tx-file").files?.[0];if(!file||!file.name.toLowerCase().endsWith(".csv")||file.size>MAX_BYTES)throw Error("Choose a CSV within 10 MB.");
  const opening=$("tx-opening").value.trim()===""?null:cents($("tx-opening").value),closing=$("tx-closing").value.trim()===""?null:cents($("tx-closing").value);
  if(($("tx-opening").value.trim()&&opening===null)||($("tx-closing").value.trim()&&closing===null))throw Error("Invalid signed balance.");
  if((opening===null)!==(closing===null))throw Error("Enter both balances or leave both blank.");
  const text=await file.text();if(token!==generation)return;
  const parsed=parseStatement(text,{account:$("tx-account").value,mode:$("tx-mode").value,start:$("tx-start").value,end:$("tx-end").value});
  draft={...parsed,opening,closing,rows:reviewRows(parsed,allRows()).map(t=>({...t,account:parsed.account}))};
  status(parsed.rowCount+" rows read; "+draft.rows.filter(t=>t.duplicate).length+" possible duplicates. Review before adding.");renderReview();
 }catch(e){if(token===generation)status("Import unavailable. "+e.message);}finally{if(token===generation)$("tx-extract").disabled=false;}};
 $("tx-approve").onclick=()=>{if(!draft)return;for(const t of draft.rows)if(!t.reviewed&&!t.duplicate&&t.suggestion!=="Unclassified"&&t.suggestion!=="Transfer"&&t.suggestion!=="Refund"){t.category=t.suggestion;t.reviewed=true;}renderReview();};
 $("tx-commit").onclick=()=>{if(!draft||$("tx-commit").disabled)return;if(statements.length>=30||allRows().length+draft.rows.length>5000){status("Tab limit reached: 30 statements / 5,000 rows. Remove a statement first.");return;}
  const balance=reconcile(draft.rows,draft.opening,draft.closing,draft.issues.length);
  if(balance.status==="mismatch"&&!confirm("Statement balances do not match. Keep the reviewed rows with the mismatch clearly marked?"))return;
  statements.push({account:draft.account,start:draft.start,end:draft.end,rows:draft.rows.map(t=>({...t})),balance});discard();status("Reviewed statement added in this tab only.");renderSummary();onChange();
 };
 $("tx-discard").onclick=discard;$("tx-clear").onclick=()=>{statements=[];discard();renderSummary();onChange();};renderSummary();reviewState();
 return {reset(){statements=[];discard();renderSummary();},findings(){
  if(!statements.length)return [];
  const rows=allRows(),s=summarize(rows),out=[{key:"transaction",title:"Reviewed transaction spending",status:"User-reviewed statements",value:dollars(s.spend),detail:"Gross categorized outflows across "+statements.length+" imported statement(s); refunds "+dollars(s.refunds)+". Transfers excluded from consumption. Not a complete household budget. Check coverage and balance reconciliation in Transaction Intelligence.",date:null,source:null}];
  for(const r of recurring(rows))out.push({key:"transaction",title:"Review possible recurring payment",status:"Observed recurrence candidate",value:dollars(r.amount),detail:r.description+" · "+r.count+" observed approximately monthly charges in "+r.account+". Verify continued service and billing before acting.",date:r.latest,source:null});
  return out;
 }};
}
