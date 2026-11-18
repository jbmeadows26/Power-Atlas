(()=>{'use strict';
const STORAGE='ea-country-focus-v1';
const ROOT=document.body.classList.contains('ea-main');
const IS_REVIEW=/^\/collection\/review\//.test(location.pathname);const IS_CUSTOM_SCOPED=/^\/global-influence(?:\/|$)/.test(location.pathname);
let catalog=[],selected='',curated={},archives=[],geo={regionalGroups:[],priorityCountries:[],briefTags:{},archiveCountryTags:{}},ready=false,open=false,highlight=0;
const $=id=>document.getElementById(id);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','"':'&quot;',"'":'&#39;'}[c]));
const norm=v=>String(v??'').normalize('NFKD').toLowerCase().replace(/[\u0300-\u036f]/g,'').replace(/[^a-z0-9]/g,'');
const safeUrl=v=>{try{const u=new URL(v,location.origin);return u.protocol==='https:'?u.href:null}catch{return null}};
const regionNames={RUS:['Russia'],CHN:['China','People\'s Republic of China'],UKR:['Ukraine'],IRN:['Iran'],CUB:['Cuba'],USA:['United States','United States of America'],GBR:['United Kingdom','Great Britain'],PRK:['North Korea','Democratic People\'s Republic of Korea'],VEN:['Venezuela'],BLR:['Belarus']};
const countryBriefs={
 RUS:['russian-cyber','defense|Russia–Ukraine','map|Russia'],
 CHN:['china-cyber','cases|Chinese contract hackers & officials'],
 UKR:['defense|Russia–Ukraine']
};
function country(){return catalog.find(x=>x.iso===selected)||null}
function name(){return country()?.name||selected||'All countries'}
function isPriority(){return country()?.analysis_tier==='priority-country'}
function group(){return (geo.regionalGroups||[]).find(x=>x.id===country()?.intelligence_region_id)||null}
function scopeLabel(){return !selected?'GLOBAL INTELLIGENCE · ALL COUNTRIES':isPriority()?'COUNTRY DOSSIER · '+name():'REGIONAL INTELLIGENCE · '+(group()?.name||country()?.intelligence_region||'Region')}
function reportName(){return isPriority()?name():(group()?.name||country()?.intelligence_region||'region')}
function geoRecord(d){const countryCodes=geo.archiveCountryTags?.[d.id]?.iso||[];return {countryCodes,regionLabels:Array.isArray(d.regions)?d.regions:[]}}
function regionMatchesDoc(d){const g=group();if(!g)return false;const rd=geoRecord(d);if(rd.regionLabels.some(r=>(g.explicit_region_labels||[]).some(label=>norm(label)===norm(r))))return true;return rd.countryCodes.some(iso=>(g.members||[]).includes(iso))}
function section(){if(ROOT)return location.hash.slice(1).split('?')[0]||'overview';const p=location.pathname;if(p.startsWith('/resources'))return 'resources';if(p.startsWith('/declassified'))return 'declassified';if(p.startsWith('/risk'))return 'risk';if(p.startsWith('/collection/evidence'))return 'evidence';if(p.startsWith('/collection'))return 'collection';return 'other'}
function dataFor(area){
 const allowed=(d)=>{
 const th=(d.themes||[]).map(x=>String(x).toLowerCase());
 if(['overview','countries','sources','collection','declassified','evidence','map'].includes(area))return true;
 if(area==='resources')return th.some(x=>['resources','trade','energy','government','diplomacy'].includes(x));
 if(area==='defense')return th.some(x=>['conflict','security','military'].includes(x));
 if(area==='cases')return th.some(x=>['espionage','cyber','intelligence'].includes(x));
 if(area==='government')return th.some(x=>['government','diplomacy'].includes(x));
 return false;
 };
 const priorityMode=isPriority();
 const matchingBriefs=priorityMode?Object.entries(geo.briefTags||{}).filter(([key,t])=>Array.isArray(t.countries)&&t.countries.includes(selected)&&(
  ['overview','countries','sources','collection','declassified','evidence'].includes(area)||
  (area==='defense'&&Array.isArray(t.themes)&&t.themes.some(x=>['defense','conflict','cyber','security'].includes(x)))||
  (area==='cases'&&Array.isArray(t.themes)&&t.themes.some(x=>['cases','cyber'].includes(x)))
 )).map(([key])=>({key,...curated[key]})).filter(x=>x.title&&Array.isArray(x.evidence)&&x.evidence.length):[];
 const seen=new Set(),briefs=matchingBriefs.map(b=>({...b,evidence:b.evidence.filter(e=>{const url=String(e.url||'');if(!url||seen.has(url))return false;seen.add(url);return true})})).filter(x=>x.evidence.length);
 const docs=archives.filter(d=>allowed(d)&&(priorityMode?geoRecord(d).countryCodes.includes(selected):regionMatchesDoc(d)));
 return {briefs,docs};
}
const titleFor={overview:'Intelligence overview',map:'Country map',countries:'Country dossier',defense:'Defense & conflicts',assets:'Military assets',cases:'Investigations',sanctions:'Sanctions / OFAC',government:'Governments & alliances',sources:'Source records',collection:'Collection intelligence',risk:'Risk & flashpoints',resources:'Resources & Power',declassified:'Declassified archive',evidence:'Official evidence registry',original:'Original archive'};
function briefHTML(brief){
 const evidence=brief.evidence||[];return '<article class="ea-country-record"><div class="ea-country-tags"><span>Official-source briefing</span><span>'+esc(brief.status||'Dated research')+'</span></div><h3>'+esc(brief.title)+'</h3><p>'+esc(brief.summary||'')+'</p><details><summary>Inspect '+evidence.length+' attributed source'+(evidence.length===1?'':'s')+'</summary>'+evidence.map(e=>{const url=safeUrl(e.url);return '<div class="ea-country-evidence"><b>'+esc(e.title||'Official document')+'</b><small>'+esc(e.agency||'Official publisher')+' · '+esc(e.published||'Date not supplied')+' · '+esc(e.classification||'Document')+'</small><p>'+esc(e.finding||'')+'</p>'+(url?'<a href="'+esc(url)+'" target="_blank" rel="noopener noreferrer">Open original document</a>':'<em>Document link unavailable</em>')+'</div>'}).join('')+'</details><p class="ea-country-caveat">'+esc(brief.uncertainty||'These published sources do not prove a current operational situation.')+'</p></article>';
}
function archivalHTML(d){const url=safeUrl(d.url);return '<article class="ea-country-record"><div class="ea-country-tags"><span>Historical record</span><span>'+esc(d.year||d.original||'')+'</span></div><h3>'+esc(d.title)+'</h3><p>'+esc(d.summary||'')+'</p><p class="ea-country-caveat">Historical source · '+esc(d.kind||d.release||'Archive')+' · geography explicitly tagged '+esc((d.regions||[]).join(', '))+'</p>'+(url?'<a href="'+esc(url)+'" target="_blank" rel="noopener noreferrer">Open official archive record</a>':'')+'</article>'}
function renderPanel(area){
 const data=dataFor(area),priorityMode=isPriority(),regional=!priorityMode,reg=group(),current=titleFor[area]||area;
 const count=data.briefs.length+data.docs.length;
 const scope=priorityMode?'COUNTRY INTELLIGENCE · '+esc(selected):'REGIONAL INTELLIGENCE · '+esc(reg?.id||'other');
 const geoLine=priorityMode?'All entries below are explicitly tagged to '+name()+'. Related global information is not automatically assigned to this country.':'Regional group: '+(reg?.name||'Region')+'. You opened it via '+name()+'. Findings about other countries in the region remain attributed to those countries, not to '+name()+'.';
 const limitation=area==='assets'?'No country/region-specific military inventory has been verified in the existing public research registry. General naval, aircraft and logistics directories are hidden because they are not evidence of this country or region.':area==='sanctions'?'OFAC/FARA entries in the live intake lack independently verified location, citizenship and state-actor attribution. Those entries are deliberately withheld from geographic filters until reviewed.':area==='risk'?'The risk register contains global scenarios, not substantiated region-specific probability estimates. Global risk values are not assigned to countries or regions.':area==='resources'?'Only archive sources explicitly tagged to this geography and resource themes are displayed; live global resource prices and claims cannot be attributed to this geography.':area==='government'?'An alliance, geographic proximity or political bloc membership alone is not evidence of coordinated misconduct.':area==='cases'?'Legal allegations and registered activity are not proof of criminal conduct or foreign state direction.':'All results have explicit source-level geographic tags. The absence of a record is a coverage gap, not evidence of safety or wrongdoing.';
 return '<section class="ea-scope-panel" data-ea-scoped="'+esc(area)+'"><div class="ea-scope-kicker">'+scope+'</div><h2>'+esc(reportName())+' <span>· '+esc(current)+'</span></h2><p class="ea-scope-summary">'+esc(geoLine)+'</p><div class="ea-scope-count">'+count+' geographically attributed source reference'+(count===1?'':'s')+'</div><p class="ea-scope-caveat">'+esc(limitation)+'</p>'+(count?'<div class="ea-scope-results">'+data.briefs.map(briefHTML).join('')+data.docs.map(d=>archivalHTML(d)).join('')+'</div>':'<div class="ea-scope-empty"><b>No source-supported '+(regional?'regional':'country')+' intelligence records available for this tab.</b><p>The filter has withheld untagged global content; it does not infer that no relevant activity exists.</p></div>')+'<div class="ea-scope-actions"><button type="button" data-ea-clear class="ea-country-reset">View all countries</button><a href="/#map">Open country map</a></div></section>';
}
function renderView(){
 const area=section(),isFiltered=!!selected;
 document.body.classList.toggle('ea-country-filtered',isFiltered);
 document.body.classList.toggle('ea-country-unfiltered',!isFiltered);
 const scope=$('ea-country-scope-banner');
 if(scope){
  const label=scopeLabel();
  scope.innerHTML='<span class="ea-scope-indicator">'+esc(label)+'</span><span class="ea-scope-description">'+(isFiltered?(isPriority()?'Filtered to the selected priority-country dossier.':'Regional view opened via '+name()+'. Records retain their actual country attribution.'):'Global overview and source catalog. Select a country to filter the tabs.')+'</span>';
 }
 if(IS_CUSTOM_SCOPED&&scope){scope.innerHTML='<span class="ea-scope-indicator">'+esc(scopeLabel())+'</span><span class="ea-scope-description">'+(selected?'International investigations and World Bank evidence filtered to '+esc(name())+'. Records keep their original jurisdiction and dates.':'Choose a country to read its in-dashboard economic briefing; global evidence remains separately labeled.')+'</span>'}
 if(ROOT){
  document.querySelectorAll('.view[data-page]').forEach(v=>{const a=v.dataset.page;let p=v.querySelector(':scope > .ea-scope-panel');if(!p){p=document.createElement('div');p.className='ea-scope-panel';v.prepend(p)}if(selected&&a!=='map')p.outerHTML=renderPanel(a);else p.innerHTML='';p.hidden=!selected||a==='map'});
  const map=document.querySelector('[data-page="map"]');if(map){let n=map.querySelector(':scope > .ea-map-scope');if(!n){n=document.createElement('p');n.className='ea-map-scope';map.prepend(n)}n.textContent=selected?(isPriority()?'Country map focused on '+name()+'. The other tabs show that country dossier.':'Country map focused on '+name()+'. Other tabs show '+(group()?.name||'regional')+' intelligence with source countries distinguished.'):'World map · No country selected. Select a country or browse regional intelligence.'}
 }else if(!IS_REVIEW&&!IS_CUSTOM_SCOPED){
  const root=document.querySelector('main');if(!root)return;root.classList.add('ea-scope-main');let n=root.querySelector(':scope > .ea-scope-panel');if(!n){n=document.createElement('div');n.className='ea-scope-panel';root.prepend(n)}
  if(selected){n.outerHTML=renderPanel(area);n=root.querySelector(':scope > .ea-scope-panel');n.hidden=false}else{n.hidden=true;n.innerHTML=''}
 }
}
function updateWidget(){
 const b=$('ea-country-trigger'),lab=$('ea-country-current');if(!b)return;const text=selected?(isPriority()?name():name()+' · '+(group()?.name||'Region')):'All countries';lab.textContent=text;b.setAttribute('aria-label','Country filter: '+text+'. Change country');b.setAttribute('title','Country filter: '+text);
 const live=$('ea-country-announcement');if(live)live.textContent=selected?(isPriority()?'Showing '+name()+' dossier':'Showing '+(group()?.name||'regional')+' intelligence via '+name()):'Showing all countries';
}
function fireSelect(iso,origin){
 if(iso&&!catalog.some(c=>c.iso===iso))return;
 selected=iso||'';try{localStorage.setItem(STORAGE,selected||'ALL')}catch{}try{const u=new URL(location.href);if(selected)u.searchParams.set('country',selected);else u.searchParams.delete('country');history.replaceState(history.state,'',u.pathname+u.search+u.hash)}catch{}
 updateWidget();close();renderView();
 if(origin!=='map')dispatchEvent(new CustomEvent('ea-country-set',{detail:{iso:selected||null,name:name()}}));
 dispatchEvent(new CustomEvent('ea-country-filtered',{detail:{iso:selected||null,name:name()}}));
}
function entries(term){
 const q=norm(term);
 const list=catalog.filter(c=>!q||norm(c.name).includes(q)||norm(c.iso).includes(q)).slice(0,35);
 return (!q?[{iso:'',name:'All countries',region:'Global'}]:[{iso:'',name:'Clear selection · All countries',region:'Global'}]).concat(list)
}
function showList(){
 const box=$('ea-country-list'),q=$('ea-country-search').value,items=entries(q);highlight=Math.min(highlight,items.length-1);box.innerHTML=items.map((c,i)=>'<button type="button" class="ea-country-option" role="option" aria-selected="'+(c.iso===selected)+'" data-iso="'+esc(c.iso)+'" id="ea-country-opt-'+i+'" data-active="'+(i===highlight)+'"><span>'+esc(c.name)+'</span><small>'+esc(c.iso||'WORLD')+' · '+esc(c.analysis_tier==='priority-country'?'Country dossier':(c.intelligence_region||c.region||'Region'))+'</small></button>').join('')||'<p>No matches</p>';return items
}
function openList(){
 open=true;$('ea-country-menu').hidden=false;$('ea-country-trigger').setAttribute('aria-expanded','true');highlight=0;$('ea-country-search').value='';showList();$('ea-country-search').focus();
}
function close(){open=false;const el=$('ea-country-menu');if(el)el.hidden=true;$('ea-country-trigger')?.setAttribute('aria-expanded','false')}
function mount(){
 const host=document.querySelector('#ea-appbar'),desk=document.querySelector('body.ea-main .topbar .actions');if(!host)return;
 const widget=document.createElement('div');widget.id='ea-country-scope';widget.className='ea-country-scope';
 widget.innerHTML='<button type="button" id="ea-country-trigger" aria-haspopup="listbox" aria-expanded="false" aria-controls="ea-country-list"><span class="ea-country-globe">◎</span><span id="ea-country-current">All countries</span><span aria-hidden="true">▾</span></button><div id="ea-country-menu" hidden><label for="ea-country-search">Filter countries</label><input type="search" id="ea-country-search" role="combobox" aria-autocomplete="list" aria-controls="ea-country-list" aria-expanded="true" autocomplete="off" placeholder="Type a country or code"><div id="ea-country-list" role="listbox" aria-label="Country choices"></div><p>Priority-country dossiers; other countries open regional intelligence. Unverified associations remain excluded.</p></div><span class="ea-only-screenreader" role="status" aria-live="polite" id="ea-country-announcement"></span>';
 host.appendChild(widget);
 const move=()=>{if(desk&&matchMedia('(min-width:901px)').matches){desk.insertBefore(widget,desk.firstChild)}else host.insertBefore(widget,$('ea-toggle')||null)};
 move();addEventListener('resize',move,{passive:true});
 const banner=$('ea-country-scope-banner')||document.createElement('div');banner.id='ea-country-scope-banner';banner.className='ea-scope-banner';
 if(ROOT){const main=document.querySelector('body.ea-main .shell main');main?.prepend(banner)}else{const sub=document.querySelector('body.ea-sub main');sub?.before(banner)}
 $('ea-country-trigger').onclick=()=>open?close():openList();
 $('ea-country-search').oninput=()=>{highlight=0;showList()};
 $('ea-country-search').onkeydown=e=>{
  let items=entries($('ea-country-search').value);
  if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();highlight=(highlight+(e.key==='ArrowDown'?1:-1)+items.length)%items.length;showList();const chosen=$('ea-country-opt-'+highlight);chosen?.scrollIntoView({block:'nearest'})}
  if(e.key==='Enter'){e.preventDefault();fireSelect(items[highlight]?.iso||'')}
  if(e.key==='Escape'){e.preventDefault();close();$('ea-country-trigger').focus()}
 };
 $('ea-country-list').onclick=e=>{const b=e.target.closest('[data-iso]');if(b)fireSelect(b.dataset.iso)};
 document.addEventListener('pointerdown',e=>{if(open&&!widget.contains(e.target))close()});
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&open){close();$('ea-country-trigger').focus()}});
 document.addEventListener('click',e=>{if(e.target.closest('[data-ea-clear]'))fireSelect('')});
 addEventListener('ea-country-picked',e=>fireSelect(e.detail?.iso||'', 'map'));
 addEventListener('ea-route',renderView);addEventListener('hashchange',renderView);addEventListener('popstate',renderView);
 updateWidget();renderView();
 if(ROOT){dispatchEvent(new CustomEvent('ea-country-catalog',{detail:{countries:catalog}}));dispatchEvent(new CustomEvent('ea-country-set',{detail:{iso:selected||null,name:name()}}));}
}
async function init(){
 try{catalog=await fetch('/data/ea-country-catalog.json',{cache:'force-cache'}).then(r=>{if(!r.ok)throw Error('country catalog unavailable');return r.json()}).then(j=>j.countries||[])}catch{catalog=Array.from(document.querySelectorAll('path.country[data-iso]')).map(x=>({iso:x.dataset.iso,name:x.dataset.name,region:'World'}));}
 if(!catalog.length)return;
 try{const query=new URLSearchParams(location.search).get('country');const value=query||localStorage.getItem(STORAGE);selected=value&&value!=='ALL'&&catalog.some(x=>x.iso===value)?value:''}catch{}
 const [brief,archive,geog]=await Promise.allSettled([fetch('/data/evidence-briefs.json').then(x=>x.json()),fetch('/data/declassified-index.json').then(x=>x.json()),fetch('/data/ea-intelligence-geography.json').then(x=>x.json())]);
 curated=brief.status==='fulfilled'&&brief.value&&brief.value.curated||{};
 archives=archive.status==='fulfilled'&&Array.isArray(archive.value?.records)?archive.value.records:[];geo=geog.status==='fulfilled'&&geog.value||{regionalGroups:[],priorityCountries:[],briefTags:{},archiveCountryTags:{}};
 ready=true;mount();
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();