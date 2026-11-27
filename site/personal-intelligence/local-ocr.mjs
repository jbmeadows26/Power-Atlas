// Browser-only OCR. No remote document uploads, language CDN, or persisted cache.
const base=new URL("./vendor/ocr/",import.meta.url);
let library;
function loadLibrary(){
 if(!library)library=new Promise((resolve,reject)=>{
  const script=document.createElement("script");script.src=new URL("tesseract.min.js",base).href;
  script.onload=()=>globalThis.Tesseract?.createWorker?resolve(globalThis.Tesseract):reject(Error("OCR library unavailable."));
  script.onerror=()=>reject(Error("Local OCR assets unavailable."));document.head.append(script);
 }).catch(e=>{library=null;throw e;});
 return library;
}
function abortError(){return Error("Recognition cancelled.");}
function bounded(promise,signal,ms,onTimeout=()=>{}){
 return new Promise((resolve,reject)=>{
  let done=false;const finish=(fn,v)=>{if(done)return;done=true;clearTimeout(timer);signal?.removeEventListener("abort",abort);fn(v);};
  const abort=()=>{finish(reject,abortError());onTimeout();};
  const timer=setTimeout(()=>{finish(reject,Error("Local recognition timed out. Try a smaller or clearer image."));onTimeout();},ms);
  signal?.addEventListener("abort",abort,{once:true});if(signal?.aborted)abort();
  Promise.resolve(promise).then(v=>finish(resolve,v),e=>finish(reject,e));
 });
}
export const MAX_SCAN_PAGES=10, MAX_IMAGE_PIXELS=40000000;
export function recognitionCanvas(width,height){
 if(!Number.isFinite(width)||!Number.isFinite(height)||width<1||height<1||width*height>MAX_IMAGE_PIXELS)throw Error("Image dimensions exceed the local processing limit.");
 const scale=Math.min(1,2600/Math.max(width,height),Math.sqrt(5000000/(width*height)));
 const canvas=document.createElement("canvas");canvas.width=Math.max(1,Math.floor(width*scale));canvas.height=Math.max(1,Math.floor(height*scale));
 const ctx=canvas.getContext("2d",{alpha:false});if(!ctx)throw Error("Canvas unavailable.");ctx.fillStyle="#fff";ctx.fillRect(0,0,canvas.width,canvas.height);
 return canvas;
}
export async function imageCanvas(file){
 let bitmap;
 try{
  bitmap=await createImageBitmap(file);
  const canvas=recognitionCanvas(bitmap.width,bitmap.height);canvas.getContext("2d").drawImage(bitmap,0,0,canvas.width,canvas.height);return canvas;
 }catch(e){throw Error("Unable to decode this image within the local limits. Use a clear JPEG, PNG or WebP image.");}
 finally{bitmap?.close();}
}
export function localRecognizer(signal,progress=()=>{}){
 let worker=null,closed=false,pending=null,initError=null;
 function close(){closed=true;if(worker){const w=worker;worker=null;Promise.resolve(w.terminate()).catch(()=>{});}}
 signal?.addEventListener("abort",close,{once:true});
 async function init(){
  const T=await bounded(loadLibrary(),signal,30000,close);
  if(closed||signal?.aborted)throw abortError();
  // Error callbacks must not throw asynchronously into the page.
  const created=T.createWorker("eng",1,{
   workerPath:new URL("worker.min.js",base).href,
   corePath:new URL("core/",base).href,
   langPath:new URL("lang/",base).href,
   workerBlobURL:false,cacheMethod:"none",gzip:true,
   logger:m=>{if(!closed&&!signal?.aborted)progress(m.status==="recognizing text"?"Recognizing text locally · "+Math.round((m.progress||0)*100)+"%":"Preparing local OCR…");},
   errorHandler:()=>{initError=Error("Local OCR worker failed.");close();}
  });
  created.then(w=>{if(closed||signal?.aborted)Promise.resolve(w.terminate()).catch(()=>{});else worker=w;},()=>{});
  const w=await bounded(created,signal,60000,close);
  if(initError)throw initError;if(closed||signal?.aborted)throw abortError();return w;
 }
 return {
  async recognize(canvas){
   if(closed||signal?.aborted)throw abortError();if(!pending)pending=init();
   const w=await pending;
   const r=await bounded(w.recognize(canvas),signal,90000,close);
   if(initError)throw initError;
   const text=r?.data?.text;if(typeof text!=="string")throw Error("Recognition returned no text.");
   return text;
  },
  close(){signal?.removeEventListener("abort",close);close();}
 };
}
