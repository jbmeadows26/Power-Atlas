/** Vercel-native same-origin API transport; no AppDeploy dependency. */
async function request(method: 'GET' | 'POST', url: string, body?: unknown): Promise<{data: unknown}> {
  const response = await fetch(url, {method, headers: body===undefined ? undefined : {'Content-Type':'application/json'}, body: body===undefined ? undefined : JSON.stringify(body), cache: 'no-store'});
  let data: unknown;
  try {data = await response.json();} catch {throw new Error('API returned an invalid response');}
  if (!response.ok) throw new Error((data as {error?:string})?.error || 'API request failed');
  return {data};
}
export const api = {get: (url:string)=>request('GET',url),post: (url:string,body?:unknown)=>request('POST',url,body)};
