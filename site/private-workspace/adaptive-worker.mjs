// This worker is started only after explicit user consent.
import {MAX_QUERY,MAX_ITEMS,MAX_TEXT} from "./adaptive-core.mjs";
const assets=new URL("./adaptive-assets/",import.meta.url);
const allowed=new Set(["vendor/transformers.min.js","vendor/ort-wasm-simd-threaded.jsep.mjs","vendor/ort-wasm-simd-threaded.jsep.wasm",...["config.json","tokenizer.json","tokenizer_config.json","special_tokens_map.json","vocab.txt","onnx/model_quantized.onnx"].map(x=>"models/Xenova/all-MiniLM-L6-v2/"+x)].map(x=>new URL(x,assets).href));
let loading=true,extractor=null,busy=false;
const nativeFetch=self.fetch.bind(self);
self.fetch=(input,init={})=>{
 const url=new URL(typeof input==="string"||input instanceof URL?input:input.url,self.location.href);
 const method=init.method||(input instanceof Request?input.method:"GET");
 if(!loading||method.toUpperCase()!=="GET"||!allowed.has(url.href))return Promise.reject(Error("Network outside local asset loading disabled"));
 return nativeFetch(input,{...init,credentials:"omit",redirect:"error",referrerPolicy:"no-referrer"});
};
async function initialize(){
 const {env,pipeline}=await import("./adaptive-assets/vendor/transformers.min.js");
 env.allowRemoteModels=false;env.allowLocalModels=true;env.localModelPath=new URL("models/",assets).href;
 env.useBrowserCache=false;env.useFSCache=false;
 env.backends.onnx.wasm.wasmPaths=new URL("vendor/",assets).href;
 env.backends.onnx.wasm.numThreads=1;env.backends.onnx.wasm.proxy=false;
 extractor=await pipeline("feature-extraction","Xenova/all-MiniLM-L6-v2",{device:"wasm",dtype:"q8",local_files_only:true});
 // Force runtime initialization before accepting any private text.
 await extractor("Public model initialization",{pooling:"mean",normalize:true});
 loading=false;
}
async function vector(s){const t=await extractor(s,{pooling:"mean",normalize:true});const v=Array.from(t.data);if(v.length!==384||v.some(x=>!Number.isFinite(x)))throw Error("Invalid embedding");return v;}
self.onmessage=async({data:m})=>{
 if(!m||busy)return;
 if(m.type==="init"&&!extractor){busy=true;try{await initialize();self.postMessage({type:"ready"});}catch{loading=false;self.postMessage({type:"error",message:"Local model could not initialize"});}finally{busy=false;}return;}
 if(m.type!=="rank"||!extractor||loading)return;
 busy=true;try{
  if(typeof m.query!=="string"||!m.query.trim()||m.query.length>MAX_QUERY||!Array.isArray(m.items)||m.items.length>MAX_ITEMS||m.items.some(x=>!Number.isInteger(x.id)||typeof x.text!=="string"||x.text.length>MAX_TEXT))throw Error("Invalid request");
  const q=await vector(m.query),out=[];
  for(const x of m.items){const v=await vector(x.text);out.push({id:x.id,score:Math.max(-1,Math.min(1,q.reduce((a,n,i)=>a+n*v[i],0)))});}
  self.postMessage({type:"result",id:m.id,rows:out});
 }catch{self.postMessage({type:"error",id:m.id,message:"Local relevance analysis failed"});}finally{busy=false;}
};
