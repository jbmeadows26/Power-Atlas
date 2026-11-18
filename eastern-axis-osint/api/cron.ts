import { timingSafeEqual } from 'node:crypto';
import { runCollectorCron } from '../backend/collector.js';
import { checkOfficialReportChanges } from '../backend/militaryMonitor.js';
import { scheduledGlobalSources, refreshEconomicSnapshot } from '../backend/index.js';

export const config = { maxDuration: 60 };

export default async function handler(req:any,res:any) {
  const actual = String(req.headers?.authorization || '');
  const secret = process.env.CRON_SECRET;
  if (req.method !== 'GET' || !secret) return res.status(401).json({error:'Unauthorized'});
  const a = Buffer.from(actual);
  const b = Buffer.from('Bearer '+secret);
  if (a.length !== b.length || !timingSafeEqual(a,b)) return res.status(401).json({error:'Unauthorized'});
  // FARA updates via a separate daily DOJ snapshot workflow; avoid 429 from serverless egress.
  const sources = ['doj','cisa','ofac'];
  const tasks = [
    ...sources.map(sourceId=>({name:sourceId,work:()=>runCollectorCron({payload:{sourceId}})})),
    {name:'military',work:()=>checkOfficialReportChanges()},
    {name:'international',work:()=>scheduledGlobalSources({scheduledTime:new Date().toISOString()})},
    {name:'worldbank-snapshot',work:()=>refreshEconomicSnapshot()}
  ];
  const results=await Promise.allSettled(tasks.map(task=>task.work()));
  const details=results.map((result,i)=>{
    if(result.status==='rejected')return {name:tasks[i].name,status:'failed',reason:'source sync failed'};
    const value=result.value as {status?:string;statusCode?:number;checks?:Array<{name:string;status:string}>};
    const bad=!!(value.status==='failed'||value.status==='error'||value.status==='partial'||
      (typeof value.statusCode==='number'&&value.statusCode>=207)||
      value.checks?.some(c=>c.status!=='ok'));
    return {name:tasks[i].name,status:bad?'degraded':'ok',
      ...(value.checks?{checks:value.checks}:{}),
      ...(bad?{reason:'See source-specific health for details'}:{})};
  });
  const status=details.every(x=>x.status==='ok')?'ok':'partial';
  if(status==='partial')console.warn('Daily Eastern Axis source sync had failures',details);
  else console.info('Daily Eastern Axis source ingestion complete',details);
  return res.status(200).json({service:'Eastern Axis',status,jobs:details});
}
