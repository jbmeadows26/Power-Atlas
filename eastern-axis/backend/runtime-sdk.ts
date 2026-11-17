import { neon } from '@neondatabase/serverless';

type Scope = { params: Record<string,string>; query: Record<string,string>; body: any; headers: Record<string,string|undefined> };
type RequestScope = { method: string; path: string; query?: Record<string,string>; body?: any; headers?: Record<string,string|undefined> };
type Route = (ctx: Scope) => Promise<Response> | Response;
const asJson = (data: unknown, status: number) => new Response(JSON.stringify(data), {
  status, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' }
});
export const json = (data: unknown) => asJson(data, 200);
export const error = (message: string, status = 500) => asJson({ error: message }, status);

export function router(routes: Record<string, Route[]>) {
  const mapped = Object.entries(routes).map(([route, handlers]) => {
    const first = route.indexOf(' ');
    const method = route.slice(0, first);
    const path = route.slice(first + 1);
    const names: string[] = [];
    const matcher = new RegExp('^' + path.split('/').map(segment => {
      if (segment.startsWith(':')) { names.push(segment.slice(1)); return '([^/]+)'; }
      return segment;
    }).join('/') + '/?$');
    return { method, matcher, names, handlers };
  });
  return async (request: RequestScope): Promise<Response> => {
    for (const route of mapped) {
      if (route.method !== request.method.toUpperCase()) continue;
      const match = route.matcher.exec(request.path);
      if (!match) continue;
      const params: Record<string,string> = {};
      route.names.forEach((name, index) => { params[name] = decodeURIComponent(match[index + 1]); });
      const context: Scope = { params, query: request.query || {}, body: request.body, headers: request.headers || {} };
      try {
        let response: Response = error('Endpoint handler returned no response', 500);
        for (const handler of route.handlers) response = await handler(context);
        return response;
      } catch (e) {
        console.error('Eastern Axis API handler failed', request.method, request.path, e);
        return error('Source temporarily unavailable', 503);
      }
    }
    return error('Not found', 404);
  };
}

type RecordEntry = { id: string; record?: any; [key: string]: any };
let dbInitialization: Promise<void> | null = null;
function connection() {
  const url = process.env.EA_DATABASE_URL;
  if (!url) throw new Error('EA_DATABASE_URL is not configured');
  return neon(url);
}
async function ready() {
  if (!dbInitialization) dbInitialization = connection().query(
    'CREATE TABLE IF NOT EXISTS eastern_axis_v2_records (collection text NOT NULL, id text NOT NULL, payload jsonb NOT NULL, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY (collection, id))'
  ).then(() => undefined).catch(e => { dbInitialization = null; throw e; });
  await dbInitialization;
}
export const db = {
  async get<T>(collection: string, ids: string[], _options?: unknown): Promise<Array<T|null>> {
    if (!ids.length) return [];
    await ready();
    const rows = await connection().query(
      'SELECT id,payload FROM eastern_axis_v2_records WHERE collection=$1 AND id = ANY($2::text[])', [collection, ids]
    );
    const byId = new Map(rows.map((row: any) => [String(row.id), row.payload]));
    return ids.map(id => (byId.get(String(id)) as T) ?? null);
  },
  async list<T>(collection: string, opts?: { limit?: number }): Promise<{ items: T[] }> {
    await ready();
    const limit = Math.min(1000, Math.max(1, Number(opts?.limit || 100)));
    const rows = await connection().query(
      'SELECT payload FROM eastern_axis_v2_records WHERE collection=$1 ORDER BY created_at DESC LIMIT $2', [collection, limit]
    );
    return { items: rows.map((row: any) => row.payload as T) };
  },
  tx: {
    async add(collection: string, records: RecordEntry[]): Promise<boolean[]> {
      await ready();
      const results: boolean[] = [];
      for (const item of records) {
        if (!item.id) { results.push(false); continue; }
        const rows = await connection().query(
          'INSERT INTO eastern_axis_v2_records (collection,id,payload) VALUES ($1,$2,$3::jsonb) ON CONFLICT DO NOTHING RETURNING id',
          [collection, String(item.id), JSON.stringify(item)]
        );
        results.push(rows.length > 0);
      }
      return results;
    },
    async update(collection: string, records: RecordEntry[]): Promise<boolean[]> {
      await ready();
      const results: boolean[] = [];
      for (const item of records) {
        if (!item.id) { results.push(false); continue; }
        const payload = item.record ?? item;
        const rows = await connection().query(
          'INSERT INTO eastern_axis_v2_records (collection,id,payload) VALUES ($1,$2,$3::jsonb) ON CONFLICT(collection,id) DO UPDATE SET payload=EXCLUDED.payload,updated_at=now() RETURNING id',
          [collection, String(item.id), JSON.stringify(payload)]
        );
        results.push(rows.length > 0);
      }
      return results;
    }
  }
};

// No fake evidence archiving: WARC capture must be wired to durable object storage.
export const storage = { async write(items: unknown[]): Promise<boolean[]> {
  console.warn('WARC object storage not configured; archive state remains false');
  return items.map(() => false);
} };
// AI synthesis deliberately unavailable until an independent, reviewed provider is configured.
export const ai = { async generate(_input: unknown): Promise<{ text: string }> {
  throw new Error('AI analysis provider is not configured; no generated analysis is returned');
} };
