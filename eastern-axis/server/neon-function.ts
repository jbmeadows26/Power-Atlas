import { handler as application } from '../backend/index';

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
