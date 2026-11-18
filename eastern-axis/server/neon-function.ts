import { handler as application, invokeScheduledJob } from '../backend/index';

/**
 * Public cross-origin adapter for Neon Functions.
 * Neon injects DATABASE_URL; the existing database adapter expects EA_DATABASE_URL.
 * This is a compatibility step. Next optimization should replace HTTP-per-query
 * connections with a pooled pg client, as recommended for long-lived Neon Functions.
 */
const defaultAllowedOrigins = ['https://jbmeadows26.github.io'];

function allowedOrigin(request: Request): string | null {
  const origin = request.headers.get('origin');
  if (!origin) return null;
  const allowed = new Set([
    ...defaultAllowedOrigins,
    ...(process.env.EA_ALLOWED_ORIGINS || '').split(',').map(s => s.trim()).filter(Boolean),
  ]);
  return allowed.has(origin) ? origin : null;
}

export default {
  async fetch(request: Request): Promise<Response> {
    const origin = request.headers.get('origin');
    const allowed = allowedOrigin(request);
    if (origin && !allowed) return Response.json({ error: 'Origin not allowed' }, { status: 403 });
    const cors: Record<string, string> = {
      'Vary': 'Origin',
      ...(allowed ? { 'Access-Control-Allow-Origin': allowed } : {}),
      'Access-Control-Allow-Headers': 'content-type, authorization',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Cache-Control': 'no-store',
    };
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });
    if (!['GET', 'POST'].includes(request.method)) {
      return Response.json({ error: 'Method not allowed' }, { status: 405, headers: cors });
    }
    const url = new URL(request.url);
    // Neon removes any client-supplied X-Neon-* headers at the edge.
    // Only a real Neon Function Trigger may enter this private scheduler route.
    if (url.pathname.startsWith('/_neon/cron/')) {
      const job = url.pathname.slice('/_neon/cron/'.length);
      const allowed = ['doj','fara','cisa','ofac','uk','canada','energy','military','worldbank'];
      if (!allowed.includes(job)) return Response.json({error:'Not found'},{status:404,headers:cors});
      if (request.method !== 'POST') return Response.json({error:'Method not allowed'},{status:405,headers:cors});
      const attestedId = request.headers.get('x-neon-trigger-invocation-id');
      if (!attestedId) return Response.json({error:'Unauthorized'},{status:401,headers:cors});
      let payload: any;
      try { payload = await request.json(); }
      catch { return Response.json({error:'Invalid scheduled payload'},{status:400,headers:cors}); }
      if (payload?.version !== 1 || payload?.invocation_id !== attestedId ||
          payload?.trigger?.type !== 'schedule' || payload?.trigger?.name !== 'ea-collect-' + job ||
          !Number.isFinite(Date.parse(payload?.data?.scheduled_at || ''))) {
        return Response.json({error:'Invalid scheduled trigger'},{status:403,headers:cors});
      }
      if (!process.env.EA_DATABASE_URL && process.env.DATABASE_URL) {
        process.env.EA_DATABASE_URL = process.env.DATABASE_URL;
      }
      try {
        await invokeScheduledJob(job);
        console.log('Neon scheduled collection completed',job,payload.invocation_id);
        return Response.json({ok:true,job,invocationId:payload.invocation_id,
          note:'Check persisted source health; invocation is not evidence that every upstream feed succeeded.'},
          {status:200,headers:cors});
      } catch (error) {
        console.error('Neon collection trigger failed',job,payload.invocation_id,error);
        return Response.json({error:'Scheduled collection failed',job},{status:503,headers:{...cors,'Retry-After':'120'}});
      }
    }
    if (!url.pathname.startsWith('/api/')) {
      return Response.json({ error: 'Not found' }, { status: 404, headers: cors });
    }
    if (!process.env.EA_DATABASE_URL && process.env.DATABASE_URL) {
      process.env.EA_DATABASE_URL = process.env.DATABASE_URL;
    }
    let body: unknown;
    if (request.method === 'POST') {
      if (!request.headers.get('content-type')?.toLowerCase().startsWith('application/json')) {
        return Response.json({ error: 'JSON required' }, { status: 415, headers: cors });
      }
      try {
        const text = await request.text();
        if (text.length > 65536) return Response.json({ error: 'Request too large' }, { status: 413, headers: cors });
        body = JSON.parse(text || '{}');
      } catch {
        return Response.json({ error: 'Invalid JSON' }, { status: 400, headers: cors });
      }
    }
    try {
      const result = await application({
        method: request.method,
        path: url.pathname,
        query: Object.fromEntries(url.searchParams.entries()),
        body,
        headers: Object.fromEntries(request.headers.entries()),
      });
      const headers = new Headers(result.headers);
      for (const [k, v] of Object.entries(cors)) headers.set(k, v);
      return new Response(result.body, { status: result.status, headers });
    } catch (error) {
      console.error('Eastern Axis Neon adapter failed', error);
      return Response.json({ error: 'Intelligence service temporarily unavailable' }, { status: 503, headers: cors });
    }
  },
};
