import {test} from "node:test";
import assert from "node:assert/strict";
import {cents,parseStatement,reviewRows,validReview,summarize,reconcile,recurring,suggest} from "../site/personal-intelligence/transaction-engine.mjs";
const opts={account:"Checking",mode:"negative-out",start:"2026-09-01",end:"2026-11-30"};
const parsed=csv=>parseStatement(csv,opts);
const review=(t,category,extra={})=>({...t,category,reviewed:true,...extra});
test("signed amounts and explicit statement convention",()=>{
 assert.equal(cents("($1,234.50)"),-123450);assert.equal(cents("1.001"),null);
 const r=parseStatement("date,description,amount\n2026-09-01,Store,30\n2026-09-02,Card payment,-40",{...opts,mode:"positive-out"});
 assert.deepEqual(r.transactions.map(t=>t.amount),[-3000,4000]);
 const q=parseStatement("date,description,debit,credit\n2026-09-01,Store,30,\n2026-09-02,Payroll,,40",{...opts,mode:"debit-credit"});
 assert.deepEqual(q.transactions.map(t=>t.amount),[-3000,4000]);
});
test("invalid currency, dates, malformed amounts, missing columns fail closed",()=>{
 const r=parsed("date,description,amount,currency\n2026-09-01,Store,10,CAD\n2026-12-01,Store,10,USD\n2026-09-01,Store,1.123,USD");
 assert.equal(r.transactions.length,0);assert.equal(r.issues.length,3);
 assert.throws(()=>parsed("date,date,description,amount\n2026-09-01,2026-09-01,Store,10"),/Ambiguous/);
 assert.throws(()=>parsed("date,description\n2026-09-01,Store"),/Missing/);
});
test("review gates and transfers/refunds/income kept separate",()=>{
 const r=parsed("date,description,amount\n2026-09-01,Groceries,-50\n2026-09-02,Payroll,100\n2026-09-03,Transfer,-20\n2026-09-04,Refund,10\n2026-09-05,Unknown,-7");
 assert.equal(summarize(r.transactions).spend,0);
 const rows=r.transactions.map((t,i)=>review(t,["Groceries","Income","Transfer","Refund","Other expense"][i]));
 const s=summarize(rows);assert.equal(s.spend,5700);assert.equal(s.income,10000);assert.equal(s.refunds,1000);assert.equal(s.transfer,1);assert.equal(s.net,3300);
 assert.equal(reconcile(rows,10000,13300).status,"matched");assert.equal(reconcile(rows,10000,13301).difference,1);
 assert.equal(reconcile(r.transactions,10000,13300).status,"incomplete review");assert.equal(reconcile(rows,null,null).status,"not provided");
});
test("overlap is excluded only from combined spending, not statement balance",()=>{
 const row=parsed("date,description,amount\n2026-09-01,Groceries,-50").transactions[0],first=review(row,"Groceries");
 const [overlap]=reviewRows({transactions:[row]},[first]);assert.equal(overlap.duplicate,true);assert.equal(overlap.overlap,true);
 assert.equal(validReview(review(overlap,"Exclude")),false);
 const second=review(overlap,"Exclude",{exclusion:"overlap"});assert.equal(validReview(second),true);
 assert.equal(summarize([first,second]).spend,5000);assert.equal(reconcile([second],10000,5000).status,"matched");
 assert.equal(reconcile([review(row,"Exclude",{exclusion:"within"})],10000,10000).status,"matched");
 assert.equal(validReview(review(row,"Exclude",{exclusion:"overlap"})),false);
});
test("possible duplicates remain candidates, never removed automatically",()=>{
 const r=parsed("date,description,amount,transaction id\n2026-09-01,Groceries,-50,A\n2026-09-01,Groceries,-50,B\n2026-09-03,Other,-20,A");
 assert.deepEqual(r.transactions.map(t=>t.duplicate),[false,true,true]);assert.equal(r.transactions.length,3);
});
test("recurrence requires three reviewed monthly charges on same account",()=>{
 const rows=parsed("date,description,amount\n2026-09-01,Netflix,-15\n2026-10-01,Netflix,-15\n2026-11-01,Netflix,-15").transactions.map(t=>review(t,"Entertainment",{account:"checking"}));
 assert.equal(recurring(rows).length,1);assert.equal(recurring(rows.slice(0,2)).length,0);assert.equal(recurring(rows.map((r,i)=>i===2?{...r,account:"other"}:r)).length,0);
 assert.equal(suggest("Credit card payment",-10000),"Transfer");assert.equal(suggest("Unknown",10000),"Unclassified");
});
