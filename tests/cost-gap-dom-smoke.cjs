/* Zero-dependency DOM/fetch smoke test for the Cost Gap interactive explorer. */
const fs=require("fs"),vm=require("vm"),assert=require("assert"),path=require("path");
const root=path.resolve(__dirname,"..");
function el(dataset={}){return {dataset,value:"",innerHTML:"",textContent:"",listeners:{},attrs:{},classList:{toggle(){}},addEventListener(k,fn){this.listeners[k]=fn},setAttribute(k,v){this.attrs[k]=v},scrollIntoView(){},querySelector(){return {disabled:false}},querySelectorAll(sel){if(sel==="[data-bedroom]"){return this.bedItems||(this.bedItems=[0,1,2,3,4].map(x=>el({bedroom:String(x)})));}return [];}}}
const ids=Object.fromEntries(["cg-form","cg-zip-a","cg-zip-b","cg-view","cg-status","cg-scope","cg-period","cg-comparison"].map(id=>[id,el()]));
const presets=[el({a:"10001",b:"19103"})];
const topics=["housing","transport","groceries","utilities","health","schools"].map(topic=>el({topic}));
const document={getElementById(id){return ids[id]||(ids[id]=el())},querySelectorAll(sel){return sel===".cg-presets button"?presets:sel===".cg-topic"?topics:[]}};
const postal={"10001":["New York","NY"],"19103":["Philadelphia","PA"]};
async function fetchMock(url){
 if(url.startsWith("https://api.zippopotam.us/us/")){const z=url.split("/").pop(),loc=postal[z];return loc?{ok:true,json:async()=>({places:[{"place name":loc[0],"state abbreviation":loc[1]}]})}:{ok:false};}
 const m=url.match(/bedroom-rents\/([A-Z]{2})\.json$/);if(!m)throw Error("Unexpected URL "+url);
 return {ok:true,json:async()=>JSON.parse(fs.readFileSync(path.join(root,"data/housing/bedroom-rents",m[1]+".json"),"utf8"))};
}
const source=fs.readFileSync(path.join(root,"platform/unified/cost-gap.js"),"utf8");
vm.runInNewContext(source,{document,fetch:fetchMock,Intl,console,encodeURIComponent,Number,Math,Promise});
async function settle(){for(let i=0;i<30&&!ids["cg-status"].textContent.startsWith("Evidence loaded");i++)await new Promise(r=>setImmediate(r));}
(async()=>{
 assert.match(ids["cg-view"].innerHTML,/Compare two places first/);
 presets[0].listeners.click();
 await settle();
 assert.match(ids["cg-status"].textContent,/Evidence loaded/);
 assert.match(ids["cg-view"].innerHTML,/\$4,460/);
 assert.match(ids["cg-view"].innerHTML,/\$2,790/);
 assert.match(ids["cg-view"].innerHTML,/\$1,670/);
 topics.find(t=>t.dataset.topic==="transport").listeners.click();
 assert.match(ids["cg-view"].innerHTML,/Data gap/);
 assert.doesNotMatch(ids["cg-view"].innerHTML,/\$1,670/);
 topics[0].listeners.click();
 assert.match(ids["cg-view"].innerHTML,/\$1,670/);
 ids["cg-view"].querySelectorAll("[data-bedroom]")[1].listeners.click();
 assert.match(ids["cg-view"].innerHTML,/\$1,760/);
 assert.match(ids["cg-view"].innerHTML,/\$4,100/);
 console.log("cost gap DOM and data smoke: PASS");
})().catch(e=>{console.error(e);process.exit(1)});
