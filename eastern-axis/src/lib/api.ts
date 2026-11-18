export type ApiResult<T = any> = { data: T };

const apiOrigin = String(import.meta.env.VITE_EA_API_ORIGIN || '').trim().replace(/\/$/, '');
const pagesTarget = import.meta.env.VITE_EA_TARGET === 'github-pages';

/**
 * Pages serves static assets only. Its API must live on a separate origin.
 * Never fall back to Vercel or a repository /api path for a Pages release.
 */
async function request<T = any>(path: string, method: 'GET' | 'POST', payload?: unknown): Promise<ApiResult<T>> {
  if (!path.startsWith('/api/')) throw new Error('Unexpected API path');
  if (pagesTarget && !apiOrigin) {
    throw new Error('Eastern Axis live API is not connected yet. Source data is unavailable, not zero.');
  }
  const url = apiOrigin ? apiOrigin + path : path;
  const res = await fetch(url, {
    method,
    credentials: apiOrigin ? 'omit' : 'same-origin',
    headers: { Accept: 'application/json', ...(method === 'POST' ? { 'Content-Type': 'application/json' } : {}) },
    ...(method === 'POST' ? { body: JSON.stringify(payload ?? {}) } : {}),
    cache: 'no-store',
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data?.error || data?.message || 'API request failed (' + res.status + ')');
  return { data: data as T };
}

export const api = {
  get: <T = any>(path: string) => request<T>(path, 'GET'),
  post: <T = any>(path: string, payload?: unknown) => request<T>(path, 'POST', payload),
};
