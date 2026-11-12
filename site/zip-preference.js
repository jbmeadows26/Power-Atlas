/* Power Atlas: one private, browser-only home ZIP preference across canonical pages.
   Never place ZIP in navigation URLs, analytics events, or Power Atlas servers. */
(()=>{
"use strict";
const KEY="poweratlas.homeZip.v1";
const valid=value=>typeof value==="string"&&/^[0-9]{5}$/.test(value);
function read(){
 try{const value=localStorage.getItem(KEY);return valid(value)?value:null;}
 catch(_){return null;}
}
function announce(value){
 window.dispatchEvent(new CustomEvent("poweratlas:zip-preference-change",{detail:{zip:value}}));
}
function save(value){
 if(!valid(value))return false;
 try{localStorage.setItem(KEY,value);}catch(_){return false;}
 announce(value);return true;
}
function clear(){
 try{localStorage.removeItem(KEY);}catch(_){return false;}
 announce(null);return true;
}
function fillSavedZIP(){
 const zip=read();
 const ids=["zipInput","zip","cg-zip-a"];
 for(const id of ids){
  const field=document.getElementById(id);
  if(!field||document.activeElement===field)return;
  if(zip&&!field.value)field.value=zip;
 }
 const reset=document.getElementById("clearSavedZIP");
 if(reset)reset.hidden=!zip;
}
window.PowerAtlasZIP={read,save,clear,key:KEY};
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",fillSavedZIP,{once:true});
else fillSavedZIP();
window.addEventListener("pageshow",fillSavedZIP);
window.addEventListener("storage",event=>{
 if(event.key!==KEY&&event.key!==null)return;
 const zip=read();
 for(const id of ["zipInput","zip","cg-zip-a"]){
  const field=document.getElementById(id);
  if(field&&document.activeElement!==field)field.value=zip||"";
 }
 const reset=document.getElementById("clearSavedZIP");
 if(reset)reset.hidden=!zip;
 announce(zip);
});
})();
