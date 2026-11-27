// Dedicated bounded decompression worker. Private bytes never enter a URL.
import {unzipSync,strFromU8} from '../private-workspace/document-assets/fflate.mjs';
import {zipEntryFilter,validateDecodedEntries} from './document-formats.mjs';
self.fetch=()=>Promise.reject(Error('Document worker network disabled.'));
self.onmessage=({data})=>{try{const entries=validateDecodedEntries(unzipSync(new Uint8Array(data),{filter:zipEntryFilter()}));self.postMessage({entries:Object.fromEntries(Object.entries(entries).map(([k,v])=>[k,strFromU8(v)]))});}catch(e){self.postMessage({error:String(e.message||'Invalid workbook')});}};
