import { handler as application } from '../backend/index';
export default async function endpoint(req: any, res: any) {
  const raw = req.query?.ea_route;
  const segments = Array.isArray(raw) ? raw : typeof raw === 'string' ? raw.split('/') : [];
  const path = '/api/' + segments.map(String).join('/');
  const u = new URL(req.url || path, 'https://eastern-axis-unified.vercel.app');
  const query = Object.fromEntries(u.searchParams.entries());
  delete query.ea_route;
  const result = await application({ method: req.method || 'GET', path, query, body: req.body, headers: req.headers });
  res.status(result.status);
  res.setHeader('Content-Type', result.headers.get('content-type') || 'application/json; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');
  res.send(await result.text());
}

export const config = { maxDuration: 300 };
