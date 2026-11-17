import { timingSafeEqual } from 'node:crypto';
import { runCollectorCron } from '../backend/collector.js';
import { checkOfficialReportChanges } from '../backend/militaryMonitor.js';
import { scheduledGlobalSources } from '../backend/index.js';

export const config = { maxDuration: 60 };

export default async function handler(req:any,res:any) {
  const actual = String(req.headers?.authorization || '');
  const secret = process.env.CRON_SECRET;
  if (req.method !== 'GET' || !secret) return res.status(401).json({error:'Unauthorized'});
  const a = Buffer.from(actual);
  const b = Buffer.from('Bearer '+secret);
  if (a.length !== b.length || !timingSafeEqual(a,b)) return res.status(401).json({error:'Unauthorized'});
  const sources = ['doj','fara','cisa','ofac'];
  const tasks = [
    ...sources.map(sourceId=>({name:sourceId,work:()=>runCollectorCron({payload:{sourceId}})})),
    {name:'military',work:()=>checkOfficialReportChanges()},
    {name:'global',work:()=>scheduledGlobalSources({scheduledTime:new Date().toISOString()})}
  ];
  const results=await Promise.allSettled(tasks.map(task=>task.work()));
  const details=results.map((result,i)=>({name:tasks[i].name,status:result.status,reason:result.status==='rejected'?'source sync failed':undefined}));
  console.info('Daily Eastern Axis source ingestion summary',details);
  return res.status(200).json({service:'Eastern Axis',jobs:details});
}
