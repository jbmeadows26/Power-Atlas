export type ApiResult<T = any> = { data: T };
async function request<T = any>(path: string, method: 'GET' | 'POST', payload?: unknown): Promise<ApiResult<T>> {
  const res = await fetch(path, {
    method,
    credentials: 'same-origin',
    headers: { Accept: 'application/json', ...(method === 'POST' ? { 'Content-Type': 'application/json' } : {}) },
    ...(method === 'POST' ? { body: JSON.stringify(payload ?? {}) } : {}),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data?.error || data?.message || 'API request failed (' + res.status + ')');
  return { data: data as T };
}
export const api = {
  get: <T = any>(path: string) => request<T>(path, 'GET'),
  post: <T = any>(path: string, payload?: unknown) => request<T>(path, 'POST', payload),
};
