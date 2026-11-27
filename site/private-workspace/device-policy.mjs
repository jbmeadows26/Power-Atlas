// No hardware probe downloads a model. Memory is reported capacity, not free RAM.
export function deviceModes(c,{manifestAvailable=false,initializationMs=null,lastInferenceMs=null}={}){
 const compatible=c.secure&&c.wasm&&c.worker&&(c.memory===null||c.memory>=2);
 const measured=Number.isFinite(lastInferenceMs)&&lastInferenceMs>=0;
 return {selected:'Standard',recommended:compatible&&manifestAvailable&&!c.saveData&&measured&&lastInferenceMs<5000?'Adaptive':'Standard',measurements:{initializationMs,lastInferenceMs,memoryGB:c.memory,webgpu:c.gpu},modes:[
  {name:'Standard',available:true,reason:'Deterministic matching and calculations; no model download.'},
  {name:'Adaptive',available:compatible&&manifestAvailable,reason:compatible&&manifestAvailable?'Optional MiniLM q8 semantic ranking, explicit download consent. '+(measured?`Last local query: ${Math.round(lastInferenceMs)} ms.`:'Performance not measured until consent and execution.'):'Browser or local model assets unavailable; deterministic fallback.'},
  {name:'Performance',available:false,reason:'No larger model/runtime has passed memory, licensing and browser acceptance gates.'},
  {name:'Advanced',available:false,reason:c.gpu?'WebGPU detected, but no generative GPU model is implemented or validated.':'No validated generative GPU runtime. WebGPU unavailable.'}
 ]};
}
