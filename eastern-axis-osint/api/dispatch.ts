import { handler } from '../backend/index.js';
export default function dispatch(request:any,response:any) {
  const base=new URL(request.url||'/', 'https://eastern-axis.invalid');
  const requested=base.searchParams.get('requested');
  if(requested){
    const clean=requested.replace(/^\/+/, '');
    base.searchParams.delete('requested');
    request.url='/api/'+clean+(base.searchParams.size?'?'+base.searchParams.toString():'');
  }
  return handler(request,response);
}
