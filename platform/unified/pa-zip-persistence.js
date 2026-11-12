/* Power Atlas: locally retained ZIP for the canonical one-origin visitor journey.
   Only the five ZIP digits are saved, never a name, household profile or issue.
   No server-side persistence, cookies, telemetry or location inference. */
(()=>{
 "use strict";
 if(window.PowerAtlasZIP)return;
 const KEY="power-atlas:visitor-zip:v1";
 const valid=zip=>typeof zip==="string"&&/^\\d{5}$/.test(zip);
 function read(){try{const zip=window.localStorage.getItem(KEY);return valid(zip)?zip:null}catch(_){return null}}
 function emit(){window.dispatchEvent(new CustomEvent("poweratlas:zip-preference",{detail:{zip:read()}}));refresh();}
 function save(zip){if(!valid(zip))return false;try{window.localStorage.setItem(KEY,zip)}catch(_){/* Private browsing may block storage */}emit();return true}
 function clear(){try{window.localStorage.removeItem(KEY)}catch(_){}emit();}
 const api=Object.freeze({get:read,save,clear,valid});
 window.PowerAtlasZIP=api;
 function refresh(){
  const header=document.getElementById("pa-global-header");
  const inner=header?.querySelector(".pa-global-inner");
  if(!inner)return;
  let badge=inner.querySelector(".pa-remembered-zip");
  const zip=read();
  if(!zip){badge?.remove();return;}
  if(!badge){
    badge=document.createElement("a");
    badge.className="pa-remembered-zip";
    badge.setAttribute("data-pa-zip-control","true");
    badge.href=location.hostname.startsWith("power-atlas-unified")||
      ["localhost","127.0.0.1"].includes(location.hostname)
      ?"my-life.html#where":"https://power-atlas-unified.vercel.app/my-life.html#where";
    const brand=inner.querySelector(".pa-global-brand");
    if(brand)brand.insertAdjacentElement("afterend",badge);else inner.append(badge);
  }
  badge.textContent="ZIP "+zip+" · Change";
  badge.setAttribute("aria-label","Using ZIP "+zip+". Change or clear saved ZIP.");
 }
 if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",refresh,{once:true});else refresh();
 window.addEventListener("storage",e=>{if(e.key===KEY)emit()});
 window.addEventListener("poweratlas:zip-preference",refresh);
})();
