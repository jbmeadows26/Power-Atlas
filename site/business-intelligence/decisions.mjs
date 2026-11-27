// Local-only decision journal. No networking, model calls or automatic persistence.
const text=(v,max=2000)=>{if(typeof v!=="string"||!v.trim()||v.length>max)throw Error("Provide a valid bounded text value.");return v.trim();};
const date=v=>{if(typeof v!=="string"||!Number.isFinite(Date.parse(v)))throw Error("Invalid record date.");return new Date(v).toISOString();};
function snapshot(f){
 if(!f||!Array.isArray(f.evidence)||!f.evidence.length||f.evidence.length>20)throw Error("A decision requires supporting evidence.");
 const dependencyId=f.dependencyId==null?null:text(f.dependencyId,100);
 const relationshipPath=f.relationshipPath??[];if(!Array.isArray(relationshipPath)||relationshipPath.length>500)throw Error("Invalid finding path.");
 return {dependencyId,relationshipPath:relationshipPath.map(id=>text(id,100)),domain:text(f.domain,100),dependency:f.dependency===null?null:text(f.dependency,200),title:text(f.title,500),status:text(f.status,200),detail:text(f.detail,5000),action:text(f.action,2000),evidence:f.evidence.map(e=>{const url=new URL(text(e.url,2000));if(url.protocol!=="https:"||url.username||url.password)throw Error("Invalid evidence URL.");return {label:text(e.label,500),source:text(e.source,500),date:text(e.date,200),url:url.href};})};
}
export const decisionStates=["considered","accepted","rejected","deferred","acted"];
export function createDecision({finding,option,status="considered",decidedAt=new Date().toISOString()}){
 if(!decisionStates.includes(status))throw Error("Invalid decision status.");
 return {version:1,id:crypto.randomUUID(),decidedAt:date(decidedAt),status,statusHistory:[{status,at:date(decidedAt)}],finding:snapshot(finding),option:text(option),outcomes:[]};
}
export function recordOutcome(decision,{description,amount=null,currency=null,reportedAt=new Date().toISOString()}){
 const checked=validateDecisions([decision])[0],stamp=date(reportedAt);
 if(stamp<checked.decidedAt)throw Error("Outcome date precedes decision.");
 if(amount!==null&&(!Number.isFinite(amount)||Math.abs(amount)>1e12))throw Error("Invalid reported amount.");
 if(amount!==null&&(typeof currency!=="string"||!/^[A-Z]{3}$/.test(currency)))throw Error("Provide a three-letter currency for the reported amount.");
 if(checked.outcomes.length>=50)throw Error("Outcome limit reached.");
 return {...checked,outcomes:[...checked.outcomes,{description:text(description),amount,currency:amount===null?null:currency,reportedAt:stamp,verification:"user-reported"}]};
}
export function validateDecisions(records){
 if(!Array.isArray(records)||records.length>100)throw Error("Invalid decision journal.");
 const ids=new Set();return records.map(r=>{
  if(!r||r.version!==1||typeof r.id!=="string"||!/^[a-f0-9-]{36}$/.test(r.id)||ids.has(r.id)||!Array.isArray(r.outcomes)||r.outcomes.length>50)throw Error("Invalid decision record.");ids.add(r.id);
  const decidedAt=date(r.decidedAt),status=r.status??'considered';if(!decisionStates.includes(status))throw Error('Invalid decision status.');
  const history=r.statusHistory??[{status,at:decidedAt}];if(!Array.isArray(history)||!history.length||history.length>100)throw Error('Invalid status history.');
  let previous=decidedAt;const statusHistory=history.map(h=>{if(!h||!decisionStates.includes(h.status)||date(h.at)<previous)throw Error('Invalid status history.');previous=date(h.at);return {status:h.status,at:previous};});if(statusHistory.at(-1).status!==status)throw Error('Status/history mismatch.');
  return {version:1,id:r.id,decidedAt,status,statusHistory,finding:snapshot(r.finding),option:text(r.option),outcomes:r.outcomes.map(o=>{
   if(!o||o.verification!=="user-reported"||date(o.reportedAt)<decidedAt||!(o.amount===null||Number.isFinite(o.amount)&&Math.abs(o.amount)<=1e12)||!(o.amount===null?o.currency===null:typeof o.currency==="string"&&/^[A-Z]{3}$/.test(o.currency)))throw Error("Invalid reported outcome.");
   return {description:text(o.description),amount:o.amount,currency:o.currency,reportedAt:date(o.reportedAt),verification:"user-reported"};
  })};
 });
}
export function exportDecisions(records){return JSON.stringify({schema:"eastern-axis.private-decisions.v1",verification:"user-reported",decisions:validateDecisions(records)},null,2);}

export function updateDecisionStatus(decision,status,at=new Date().toISOString()){
 const r=validateDecisions([decision])[0];if(!decisionStates.includes(status))throw Error('Invalid decision status.');
 if(date(at)<r.statusHistory.at(-1).at||r.statusHistory.length>=100)throw Error('Invalid status date or history limit.');
 return validateDecisions([{...r,status,statusHistory:[...r.statusHistory,{status,at:date(at)}]}])[0];
}
