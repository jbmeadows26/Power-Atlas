/* Read-only mobile UX smoke against a locally served, fixture-backed Vite build.
   No production APIs, secrets, or source collectors are used in this check. */
const {spawn}=require('node:child_process');
const {resolve}=require('node:path');
const {setTimeout:delay}=require('node:timers/promises');
const assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');

const ROOT=resolve(__dirname,'..');
const URL='http://127.0.0.1:4173/';
const overview={
  countries:[
    {code:'RU',name:'Russia',region:'Europe',scope:'state-or-observer',relationship:'Outside primary U.S. alliances',isTreatyAlly:false,isMNNA:false,caseCount:1},
    {code:'CN',name:'China',region:'Asia',scope:'state-or-observer',relationship:'Outside primary U.S. alliances',isTreatyAlly:false,isMNNA:false,caseCount:0},
  ],
  cases:[{id:'test-case',code:'RU',date:'2026-10-01',title:'Fixture case (not published)',topic:'Cyber',status:'Allegation',level:'Official release',summary:'Test data',impact:'Test impact',source:'https://www.justice.gov/',agency:'DOJ'}],
  sources:[{id:'doj',name:'DOJ',category:'Government',mode:'Scheduled intake',cost:'Free',url:'https://www.justice.gov/',description:'Official source'}],
  snapshot:null,classificationAsOf:'2026-10-01',scopeDefinition:'Fixture only',classificationSources:[],
};
const globalData={
  code:'WLD',checkedAt:'',status:'unavailable',covered:0,requested:0,
  indicators:[],warning:null,source:'World Bank',sourceUrl:'https://data.worldbank.org/',method:'Fixture',
};
async function waitForServer(){
  for(let attempt=0;attempt<80;attempt++){
    try{const response=await fetch(URL);if(response.ok)return;}
    catch(_){}
    await delay(300);
  }
  throw Error('Local Vite server did not start');
}
async function qa(page,width){
  await page.route('**/api/**',route=>{
    const path=new URL(route.request().url()).pathname;
    let data={};
    if(path==='/api/overview')data=overview;
    else if(path.startsWith('/api/brief/'))data={code:path.split('/').at(-1),updatedAt:'',mode:'unavailable',metrics:{}};
    else if(path==='/api/intelligence')data={sources:[],records:[],sampled:0,resultsNote:'Fixture-only test',ofac:null};
    else if(path==='/api/world-signals')data={status:'unavailable',count:0,events:[],naturalEvents:[]};
    else if(path.startsWith('/api/global-systems/'))data=globalData;
    return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(data)});
  });
  await page.route('https://cdn.jsdelivr.net/**',route=>route.abort());
  const pageErrors=[];
  page.on('pageerror',e=>pageErrors.push(String(e)));
  await page.goto(URL,{waitUntil:'domcontentloaded'});
  await page.locator('#ea-country-scope option[value="RU"]').waitFor({state:'attached',timeout:20000});
  const nav=page.getByRole('navigation',{name:'Mobile primary navigation'});
  if(width>980){
    assert.equal(await nav.isVisible(),false,'Desktop must not display the mobile nav');
    assert.equal(await page.locator('.sidebar').isVisible(),true,'Desktop keeps its full sidebar');
  }else{
    assert.equal(await nav.isVisible(),true,'Mobile navigation must be visible');
    assert.deepEqual(await nav.locator('button span').allTextContents(),['Home','Countries','Risks','Networks','More']);
    await page.locator('.mobile-brief').waitFor({state:'visible'});
    await page.locator('#ea-country-scope').selectOption('CN');
    await nav.getByRole('button',{name:'Countries'}).click();
    await page.getByRole('heading',{name:/Country intelligence/i}).waitFor();
    assert.equal(await page.locator('#ea-country-scope').inputValue(),'CN','Country selection must persist between tabs');
    await nav.getByRole('button',{name:'Risks'}).click();
    await page.getByRole('heading',{name:/Pressure points/i}).waitFor();
    assert.equal(await page.locator('#ea-country-scope').inputValue(),'CN');
    await nav.getByRole('button',{name:'More'}).click();
    await page.locator('#ea-primary-navigation.sidebar-open').waitFor({state:'visible'});
    await page.locator('#ea-primary-navigation button.nav-item').filter({hasText:'Source library'}).click();
    await page.getByRole('heading',{name:/Sources, not secrets/i}).waitFor();
    assert.equal(await page.locator('#ea-primary-navigation').evaluate(el=>el.classList.contains('sidebar-open')),false,'Drawer should close after a selection');
    await nav.getByRole('button',{name:'Home'}).click();
    await page.locator('.mobile-brief').waitFor({state:'visible'});
    assert.match(await page.locator('.mobile-brief p').innerText(),/Focused on China/);
    await page.reload({waitUntil:'domcontentloaded'});
    await page.locator('.mobile-brief').waitFor({state:'visible'});
    assert.equal(await page.locator('#ea-country-scope').inputValue(),'CN','Country selection survives reload');
    await page.locator('.cc-map-actions button').first().waitFor({state:'visible'});
  }
  const geometry=await page.evaluate(()=>({page:document.documentElement.scrollWidth,viewport:window.innerWidth}));
  assert.ok(geometry.page<=geometry.viewport+2,'Unexpected horizontal scrolling: '+JSON.stringify(geometry));
  assert.deepEqual(pageErrors,[],'Uncaught browser errors');
  console.log('PASS responsive navigation '+width+'px');
}
(async()=>{
  const server=spawn('npm',['run','dev','--','--host','127.0.0.1','--port','4173','--strictPort'],{
    cwd:ROOT,stdio:'ignore',env:{...process.env,BROWSER:'none'},
  });
  let browser;
  try{
    await waitForServer();
    browser=await chromium.launch({headless:true,args:['--no-sandbox']});
    for(const width of [320,390,1440]){
      const context=await browser.newContext({viewport:{width,height:844},deviceScaleFactor:1});
      try{await qa(await context.newPage(),width);}finally{await context.close();}
    }
  }finally{
    if(browser)await browser.close();
    server.kill('SIGTERM');
  }
})().catch(e=>{console.error(e);process.exitCode=1;});
