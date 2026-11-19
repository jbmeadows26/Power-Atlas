/* Read-only mobile UX smoke against a locally served, fixture-backed Vite build.
   No production APIs, secrets, or source collectors are used in this check. */
const {spawn}=require('node:child_process');
const {resolve}=require('node:path');
const {setTimeout:delay}=require('node:timers/promises');
const assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');

const ROOT=resolve(__dirname,'..');
const BASE_URL='http://127.0.0.1:4173/';
const overview={
  countries:[
    {code:'RU',name:'Russia',region:'Europe',scope:'state-or-observer',relationship:'Outside primary U.S. alliances',isTreatyAlly:false,isMNNA:false,caseCount:1},
    {code:'CN',name:'China',region:'Asia',scope:'state-or-observer',relationship:'Outside primary U.S. alliances',isTreatyAlly:false,isMNNA:false,caseCount:0},
    {code:'CA',name:'Canada',region:'Americas',scope:'state-or-observer',relationship:'NATO treaty ally',isTreatyAlly:true,isMNNA:false,caseCount:0},
    {code:'AG',name:'Antigua & Barbuda',region:'Americas',scope:'state-or-observer',relationship:'Regional research',isTreatyAlly:false,isMNNA:false,caseCount:0},
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
    try{const response=await fetch(BASE_URL);if(response.ok)return;}
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
    else if(path==='/api/defense-intel')data={reviewedAsOf:'2026-11-15',mode:'fixture',assessments:[{id:'russian-assessment',title:'Fixture allied assessment',agency:'Canadian source',government:'Canada',countries:['RU'],published:'2026-08',url:'https://www.canada.ca/'}],operations:[{id:'russian-operations',title:'Fixture operation',roles:[{code:'RU',role:'Participant'}],published:'2026-09',url:'https://www.un.org/'}],assets:[{id:'russian-asset',code:'RU',name:'Fixture aircraft estimate',quantity:'100 (test)',published:'2026',url:'https://www.mod.go.jp/'}],sources:[
      {id:'canada',name:'Canadian CSIS',group:'Five Eyes',what:'Public reports',url:'https://www.canada.ca/'},
      {id:'nato',name:'NATO',group:'EU / NATO',what:'Alliance analysis',url:'https://www.nato.int/'},
      {id:'japan',name:'Japan Ministry of Defense',group:'Indo-Pacific allies',what:'Defense references',url:'https://www.mod.go.jp/'}
    ],caveats:[]};
    else if(path.startsWith('/api/allied-sanctions/'))data={scope:path.split('/').at(-1),checkedAt:'',policy:'Fixture only',graphPolicy:'Fixture only',sources:[
      {id:'uk',name:'UK Sanctions List',sourceUrl:'https://www.gov.uk/',status:'snapshot',checkedAt:'',publicationDate:null,listedUniqueDesignations:100,regimeRecordCount:null,samples:[],regimes:[],warning:'Fixture'},
      {id:'canada',name:'Canada Sanctions List',sourceUrl:'https://www.canada.ca/',status:'snapshot',checkedAt:'',publicationDate:null,listedUniqueDesignations:100,regimeRecordCount:null,samples:[],regimes:[],warning:'Fixture'}
    ]};
    else if(path==='/api/intelligence')data={sources:[],records:[],sampled:0,resultsNote:'Fixture only',reviewPolicy:'Fixture only'};
    else if(path==='/api/source-monitor')data={feeds:[],records:[],mode:'fixture',explanation:'Test-only data',nextScan:''};
    else if(path.startsWith('/api/global-systems/'))data=globalData;
    return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(data)});
  });
  await page.route('https://cdn.jsdelivr.net/**',route=>route.abort());
  const pageErrors=[];
  page.on('pageerror',e=>pageErrors.push(String(e)));
  await page.goto(BASE_URL,{waitUntil:'domcontentloaded'});
  await page.getByRole('button',{name:'Choose country intelligence scope'}).waitFor({state:'visible',timeout:20000});
  assert.equal(await page.locator('.ea-ops').count(),0,'Obsolete repeated global statistics should not mount');
  const radar=page.getByRole('region',{name:'Decision radar by domain'});
  await radar.waitFor({state:'visible'});
  assert.equal(await radar.locator('.dr-lane').count(),4,'First screen should show four decision-domain visualizations');
  await page.getByRole('navigation',{name:'Primary intelligence workspaces'}).waitFor({state:'visible'});
  const nav=page.getByRole('navigation',{name:'Mobile primary navigation'});
  if(width>980){
    assert.equal(await nav.isVisible(),false,'Desktop must not display the mobile nav');
    assert.equal(await page.locator('.sidebar').isVisible(),true,'Desktop keeps its full sidebar');
  }else{
    assert.equal(await nav.isVisible(),true,'Mobile navigation must be visible');
    assert.deepEqual(await nav.locator('button span').allTextContents(),['Home','Countries','Risks','Networks','More']);
    await radar.getByRole('heading',{name:'Finance'}).waitFor({state:'visible'});
    await radar.locator('.dr-pair').first().waitFor({state:'visible',timeout:15000});
    // Regression: zero-DOJ country with null allied-sanctions counts must never blank the app.
    await nav.getByRole('button',{name:'Networks'}).click();
    await page.locator('.cx-country').filter({hasText:'Antigua & Barbuda'}).click();
    await page.locator('.cx-center h2').getByText('Antigua & Barbuda').waitFor();
    await page.locator('.ip-sanction-source').first().waitFor();
    await page.locator('.cx-branch-tabs button').filter({hasText:'U.S. + allied source network'}).click();
    await page.getByText('Canadian CSIS').waitFor();
    // Each country carries its own sourced defense dossier, independent of DOJ case counts.
    await page.getByRole('button',{name:'Choose country intelligence scope'}).click();
    await page.getByRole('option',{name:/Worldwide/}).click();
    const russiaCard=page.locator('.cx-country').filter({hasText:'Russia'});
    await russiaCard.getByText('1 allied reports').waitFor();
    await russiaCard.getByText('1 operations').waitFor();
    await russiaCard.getByText('1 asset entries').waitFor();
    await russiaCard.click();
    const dossier=page.locator('.cx-root .cds-root');
    await dossier.getByText('Russia: military & allied intelligence').waitFor();
    await dossier.getByText('Fixture allied assessment').waitFor();
    await dossier.getByText('Fixture operation').waitFor();
    await dossier.getByText('100 (test) Fixture aircraft estimate').waitFor();
    assert.equal(await dossier.locator('.cds-references a').count(),3,'Every indexed defense domain must link its original source');
    await dossier.getByRole('button',{name:/Military operations/}).click();
    await page.locator('.cx-branch-title h2').getByText('Reported conflict context').waitFor();
    assert.equal((await page.locator('#root').innerText()).length>100,true,'Zero-case country blanked the page');
    assert.deepEqual(pageErrors,[],'Country selection caused a React render error');
    await page.getByRole('button',{name:'Choose country intelligence scope'}).click();
    await page.getByRole('option',{name:/Worldwide/}).click();
    await page.getByRole('button',{name:'Choose country intelligence scope'}).click();
    await page.getByRole('combobox',{name:'Search country or code'}).fill('china');
    await page.getByRole('option',{name:/China/}).click();
    await nav.getByRole('button',{name:'Countries'}).click();
    await page.getByRole('heading',{name:/Country intelligence/i}).waitFor();
    assert.equal(await page.locator('#ea-country-scope').count(),1,'Country selector was unexpectedly unmounted: '+JSON.stringify(pageErrors));
    assert.match(await page.locator('#ea-country-scope').innerText(),/China/,'Country selection must persist between tabs');
    await nav.getByRole('button',{name:'Risks'}).click();
    await page.getByRole('heading',{name:/Pressure points/i}).waitFor();
    assert.match(await page.locator('#ea-country-scope').innerText(),/China/);
    await nav.getByRole('button',{name:'More'}).click();
    await page.locator('#ea-primary-navigation.sidebar-open').waitFor({state:'visible'});
    await page.locator('#ea-primary-navigation button.nav-item').filter({hasText:'Source library'}).click();
    await page.getByRole('heading',{name:/Sources, not secrets/i}).waitFor();
    assert.equal(await page.locator('#ea-primary-navigation').evaluate(el=>el.classList.contains('sidebar-open')),false,'Drawer should close after a selection');
    await nav.getByRole('button',{name:'Home'}).click();
    await page.getByRole('region',{name:'Decision radar by domain'}).getByText('Country focus: China',{exact:false}).waitFor({state:'visible'});
    assert.equal(await page.locator('.mobile-brief:visible').count(),0,'Legacy oversized mobile hero still blocks the data first screen');
    await page.reload({waitUntil:'domcontentloaded'});
    await page.getByRole('region',{name:'Decision radar by domain'}).getByText('Country focus: China',{exact:false}).waitFor({state:'visible'});
    assert.match(await page.locator('#ea-country-scope').innerText(),/China/,'Country selection survives reload');
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
