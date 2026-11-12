/* Power Atlas privacy-first runtime QA.
   The public PostHog token is supplied by /api/qa-config, not source control.
   No ZIP, submitted messages, political preferences, form fields or session video.
   Missing config, network blocks or analytics errors NEVER block the website. */
(()=>{"use strict";
const path=(location.pathname.split("/").pop()||"home").replace(/[^a-z0-9.\-]/gi,"").slice(0,65);
function redacted(event){
  if(!event)return null;
  const clean=obj=>{
    if(!obj||typeof obj!=="object")return;
    Object.keys(obj).forEach(k=>{
      // Keep only numeric Core Web Vitals; the general "value" scrubber must
      // never remove their measurement payloads. No user text or URLs survive.
      if(event.event==="$web_vitals" &&
         /^\$web_vitals_(LCP|INP|CLS|FCP)_value$/.test(k) &&
         typeof obj[k]==="number" && Number.isFinite(obj[k])) return;
      if(/url|referr|href|path|query|search|email|zip|postal|form|element|text|input|value|selector|person|address/i.test(k)){
        delete obj[k];
      }else if(typeof obj[k]==="string"){
        obj[k]=obj[k].replace(/\b\d{5}(?:-\d{4})?\b/g,"[location redacted]").slice(0,1200);
      }
    });
  };
  clean(event.properties);clean(event.$set);clean(event.$set_once);
  if(event.event==="$web_vitals" && event.properties)event.properties.pa_page=path;
  return event;
}
async function init(){
  if(location.hostname==="localhost"||location.hostname==="127.0.0.1")return;
  let conf;
  try{
    const response=await fetch("/api/qa-config",{cache:"no-store",credentials:"same-origin"});
    if(!response.ok)return;
    conf=await response.json();
  }catch(_){return;}
  if(!conf||!conf.enabled||!/^phc_[A-Za-z0-9_-]+$/.test(conf.token)||
      !/^https:\/\/(us|eu)\.i\.posthog\.com$/.test(conf.host))return;
  try{
    /* Official PostHog browser loader; allows events before SDK finishes loading. */
    !function(t,e){var o,n,p,r;e.__SV||(window.posthog&&window.posthog.__loaded)||(window.posthog=e,e._i=[],e.init=function(i,s,a){function g(t,e){var o=e.split(".");2==o.length&&(t=t[o[0]],e=o[1]),t[e]=function(){t.push([e].concat(Array.prototype.slice.call(arguments,0)))}}p||((p=t.createElement("script")).type="text/javascript",p.crossOrigin="anonymous",p.async=!0,p.src=s.api_host.replace(".i.posthog.com","-assets.i.posthog.com")+"/static/array.js",p.onerror=function(){p=null},(r=t.getElementsByTagName("script")[0]).parentNode.insertBefore(p,r));var u=e;for(void 0!==a?u=e[a]=[]:a="posthog",u.people=u.people||[],Object.defineProperty(u,"toString",{configurable:!0,enumerable:!0,writable:!0,value:function(t){var e="posthog";return"posthog"!==a&&(e+="."+a),t||(e+=" (stub)"),e}}),Object.defineProperty(u.people,"toString",{configurable:!0,enumerable:!0,writable:!0,value:function(){return u.toString(1)+".people (stub)"}}),o="init capture register register_once register_for_session unregister unregister_for_session getFeatureFlag getFeatureFlagResult isFeatureEnabled reloadFeatureFlags updateEarlyAccessFeatureEnrollment getEarlyAccessFeatures on onFeatureFlags onSessionId getSurveys getActiveMatchingSurveys renderSurvey canRenderSurvey getNextSurveyStep identify setPersonProperties group resetGroups reset get_distinct_id getGroups get_session_id get_session_replay_url alias set_config startSessionRecording stopSessionRecording sessionRecordingStarted captureException opt_in_capturing opt_out_capturing has_opted_in_capturing has_opted_out_capturing clear_opt_in_out_capturing debug".split(" "),n=0;n<o.length;n++)g(u,o[n]);e._i.push([i,s,a])},e.__SV=1)}(document,window.posthog||[]);
    window.posthog.init(conf.token,{
      api_host:conf.host,defaults:"2026-08-30",autocapture:false,
      capture_pageview:false,capture_performance:true,
      disable_session_recording:true,disable_surveys:true,
      person_profiles:"identified_only",persistence:"memory",before_send:redacted
    });
    window.posthog.capture("pa_qa_monitor_loaded",{pa_page:path,pa_surface:"power-atlas"});
    // Detect browser and asset failures without reporting URLs, exception
    // messages, form contents, ZIP codes, selectors or session recordings.
    let failures=0;
    function failure(kind){
      if(failures++>=3)return;
      try{window.posthog.capture("pa_qa_browser_error",
        {pa_page:path,pa_kind:kind,pa_surface:"power-atlas"});}catch(_){}
    }
    window.addEventListener("error",e=>{
      const tag=e.target&&e.target!==window?e.target.tagName:"";
      if(tag==="SCRIPT"||tag==="LINK")failure("asset");
      else if(!tag)failure("javascript");
    },true);
    window.addEventListener("unhandledrejection",()=>failure("promise"));
  }catch(_){/* Monitoring cannot change page behavior. */}
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init,{once:true});
else init();
})();
