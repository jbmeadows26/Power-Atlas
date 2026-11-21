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
    {code:'US',name:'United States',region:'Americas',scope:'state-or-observer',relationship:'Domestic',isTreatyAlly:false,isMNNA:false,caseCount:0},
    {code:'AG',name:'Antigua & Barbuda',region:'Americas',scope:'state-or-observer',relationship:'Regional research',isTreatyAlly:false,isMNNA:false,caseCount:0},
  ],
  cases:[{id:'test-case',code:'RU',date:'2026-10-01',title:'Fixture case (not published)',topic:'Cyber',status:'Allegation',level:'Official release',summary:'Test data',impact:'US test impact',source:'https://www.justice.gov/',agency:'DOJ'}],
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
    else if(path.startsWith('/api/energy-supply/'))data={code:path.split('/').at(-1),status:'unavailable',indicators:[],warning:'Fixture: no observations',location:'Test-only',countryCount:0,checkedAt:null};
    else if(path.startsWith('/api/global-systems/'))data=globalData;
    return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify(data)});
  });
  // Independent resilience telemetry is fixture-backed: CI must not depend
  // on a live external collector to verify the drilldown behavior.
  await page.route('**/eastern-axis/public/telemetry/resilience.json*',route=>route.fulfill({
    status:200,contentType:'application/json',body:JSON.stringify({
      schemaVersion:1,checkedAt:'2026-11-20T05:00:00Z',status:'ok',
      summary:'Fixture-only probe sample',sampledCount:3,incidents:[],screeningSignals:[],
      observations:[{id:'fixture-probe',title:'Fixture endpoint health',category:'regional_http',
        checkedAt:'2026-11-20T05:00:00Z',source:'Test-only observation',
        status:'observed',scope:'Fixture: no external services sampled'}],
      capabilities:[{id:'gnss',title:'Fixture GNSS source',source:'Test harness',status:'sampled'}],
      limitations:['Fixtures are not operational evidence'],
      history:[{checkedAt:'2026-11-20T05:00:00Z',observed:3,alerts:0,errors:0}]
    })
  }));
  await page.route('https://cdn.jsdelivr.net/**',route=>route.abort());
  // No external form submission during QA. Test the integration, not a fake receipt.
  await page.route('https://tally.so/**',route=>route.fulfill({status:200,contentType:'text/html',body:'<!DOCTYPE html><title>QA form placeholder</title>'}));
  const pageErrors=[];
  page.on('pageerror',e=>pageErrors.push(String(e)));
  await page.goto(BASE_URL,{waitUntil:'domcontentloaded'});
  await page.getByRole('button',{name:'Choose country intelligence scope'}).waitFor({state:'visible',timeout:20000});
  assert.equal(await page.locator('.ea-ops').count(),0,'Obsolete repeated global statistics should not mount');
  const command=page.getByRole('region',{name:'Evidence-gated command alerts'});
  await command.waitFor({state:'visible',timeout:20000});
  assert.equal(await page.locator('.dr-root').count(),0,'Command must not repeat unelevated screening movements');
  if(width<=980)await page.getByRole('navigation',{name:'Mobile primary navigation'}).getByRole('button',{name:'More'}).click();
  await page.locator('#ea-primary-navigation button.nav-item').filter({hasText:'Early warning'}).click();
  const analyst=page.getByRole('region',{name:'AI analyst signal review'});
  await analyst.waitFor({state:'visible'});
  await analyst.locator('.sr-cover-row').first().waitFor({state:'visible',timeout:15000});
  const signalView=analyst.getByRole('button',{name:'Market & GNSS'});
  assert.equal(await signalView.getAttribute('aria-pressed'),'true','Measured movements must lead Early Warning');
  assert.ok(await analyst.locator('.sr-cover-row').count()===4,'Four independent source-category bars are required');
  await analyst.getByRole('button',{name:/Weather alerts/}).click();
  assert.equal(await analyst.locator('.sr-tabs [aria-pressed="true"]').count(),1,'Weather lane must be selected independently');
  await analyst.getByRole('button',{name:/Unreviewed/}).click();
  assert.equal(await analyst.locator('.sr-tabs [aria-pressed="true"]').count(),1,'Pending model reviews need a separate queue');
  await signalView.click();
  if(width<=980){
    assert.equal(await analyst.locator('.sr-rows').evaluate(el=>getComputedStyle(el).maxHeight),'none',
      'Mobile analyst list must not trap scrolling behind the fixed bottom nav');
  }
  const disclosure=page.locator('.pew-context-radar');
  await disclosure.waitFor({state:'visible'});
  await disclosure.locator('summary').click();
  const radar=page.getByRole('region',{name:'Decision radar by domain'});
  await radar.waitFor({state:'visible'});
  // Every individual reading opens an accessible, source-aware detail window.
  await radar.locator('.dr-move').first().waitFor({state:'visible',timeout:20000});
  const firstReading=await radar.locator('.dr-move-top strong').first().innerText();
  await radar.locator('.dr-move').first().locator('.dr-pair').click();
  let detail=page.getByRole('dialog',{name:firstReading});
  await detail.waitFor({state:'visible'});
  assert.ok(await detail.locator('.ea-detail-comparison').count()>=2,'Metric drilldown must retain both original observations');
  assert.ok(await detail.locator('.ea-detail-evidence a').count()>0,'Metric drilldown must link its exact source');
  await detail.getByRole('button',{name:'Close evidence detail'}).click();
  await detail.waitFor({state:'detached'});
  // Keyboard users get the same single-item popup, with Escape to return.
  await radar.locator('.dr-move').first().focus();
  await page.keyboard.press('Enter');
  detail=page.getByRole('dialog',{name:firstReading});
  await detail.waitFor({state:'visible'});
  await page.keyboard.press('Escape');
  await detail.waitFor({state:'detached'});
  await radar.locator('.dr-snapshot').first().click();
  detail=page.getByRole('dialog',{name:/Probe snapshot|screening\/correlated indicators/i});
  await detail.waitFor({state:'visible'});
  assert.ok(await detail.locator('.ea-detail-evidence a').count()>=1,'Probe source must not inherit a GNSS link');
  await detail.getByRole('button',{name:'Close evidence detail'}).click();
  assert.equal(await radar.locator('.dr-lane').count(),4,'First screen should show four decision-domain visualizations');
  assert.equal(await page.getByRole('navigation',{name:'Primary intelligence workspaces'}).count(),0,'Redundant horizontal workspace menu must not mount');
  if(width<=980) await page.getByRole('navigation',{name:'Mobile primary navigation'}).getByRole('button',{name:'More'}).click();
  const report=page.locator('#ea-primary-navigation').getByRole('button',{name:/Report a bug/i});
  await report.waitFor({state:'visible'});
  await report.click();
  const bug=page.getByRole('dialog',{name:'Report a bug'});
  await bug.waitFor({state:'visible'});
  const embedded=await bug.locator('iframe[title="Anonymous Eastern Axis bug report"]').getAttribute('src');
  assert.match(embedded||'',/^https:\/\/tally\.so\/embed\/LDKRaj\?/,'Bug form must be anonymous hosted form, not GitHub Issues');
  assert.match(embedded||'',/section=Early\+warning/,'Bug report should identify active section');
  assert.equal((embedded||'').includes('github.com'),false,'Bug reporter must not require GitHub membership');
  assert.match(await bug.getByRole('link',{name:/Open form separately/i}).getAttribute('href'),/^https:\/\/tally\.so\/r\/LDKRaj\?/);
  await bug.getByRole('button',{name:'Close bug report'}).click();
  await bug.waitFor({state:'detached'});

  // Regression: U.S. is an impacted country in the case record, not its origin code.
  // This used to show zero cards and an unusable "Select an investigation" panel.
  if(width<=980)await page.getByRole('navigation',{name:'Mobile primary navigation'}).getByRole('button',{name:'More'}).click();
  await page.locator('#ea-primary-navigation button.nav-item').filter({hasText:'Investigations'}).click();
  await page.locator('#ea-investigation-list .case-card').first().waitFor({state:'visible'});
  assert.equal(await page.locator('#ea-investigation-list .case-card').count(),1);
  assert.match(await page.locator('#ea-investigation-detail').innerText(),/Fixture case/,'A matching case should open by default');
  await page.getByRole('button',{name:'Choose country intelligence scope'}).click();
  await page.getByRole('combobox',{name:'Search country or code'}).fill('United States');
  await page.getByRole('option',{name:/United States/}).click();
  assert.equal(await page.locator('#ea-investigation-list .case-card').count(),1,'U.S. impact must not be confused with the foreign-case country tag');
  assert.match(await page.locator('.investigation-summary').innerText(),/U.S. impact view/);
  await page.locator('#ea-investigation-list .case-card').first().click();
  assert.match(await page.locator('#ea-investigation-detail .evidence-line').first().innerText(),/COUNTRY/);
  assert.match(await page.locator('#ea-investigation-detail .evidence-button').getAttribute('href'),/^https:\/\//);
  if(width<=980){
    await page.getByRole('button',{name:'Back to investigations'}).click();
    assert.equal(await page.locator('#ea-investigation-list').isVisible(),true);
  }
  await page.getByRole('button',{name:'Choose country intelligence scope'}).click();
  await page.getByRole('combobox',{name:'Search country or code'}).fill('China');
  await page.getByRole('option',{name:/China/}).click();
  await page.locator('.case-empty').waitFor({state:'visible'});
  assert.equal(await page.locator('#ea-investigation-detail:visible').count(),0,'No matching case should not display a ghost detail panel');
  await page.getByRole('button',{name:'View all investigations'}).click();
  assert.equal(await page.locator('#ea-investigation-list .case-card').count(),1,'Reset must restore all cases');
  assert.match(await page.getByRole('button',{name:'Choose country intelligence scope'}).innerText(),/Worldwide/);

  const nav=page.getByRole('navigation',{name:'Mobile primary navigation'});
  if(width>980){
    assert.equal(await nav.isVisible(),false,'Desktop must not display the mobile nav');
    assert.equal(await page.locator('.sidebar').isVisible(),true,'Desktop keeps its full sidebar');
  }else{
    assert.equal(await nav.isVisible(),true,'Mobile navigation must be visible');
    assert.deepEqual(await nav.locator('button span').allTextContents(),['Home','Countries','Risks','Systems','More']);
    await radar.getByRole('heading',{name:'Finance'}).waitFor({state:'visible'});
    await radar.locator('.dr-pair').first().waitFor({state:'visible',timeout:15000});
    // Networks is a Countries subview, not its own global navigation route.
    await nav.getByRole('button',{name:'Countries'}).click();
    const countriesViews=page.getByRole('group',{name:'Country intelligence views'});
    await countriesViews.getByRole('button',{name:'Networks'}).click();
    const network=page.getByRole('region',{name:'Sourced relationship networks'});
    await network.waitFor({state:'visible'});
    await network.locator('.nx-graph').waitFor({state:'visible'});
    assert.ok(await network.locator('.nx-connection').count()>=2,'Russia spotlight must expose sourced treaty relationships');
    assert.equal(await page.locator('.ip-sanction-source').count(),0,'Sanctions snapshots must not replace Networks');
    await network.locator('.nx-connection').first().click();
    const original=network.getByRole('link',{name:/Examine original evidence/});
    assert.match(await original.getAttribute('href'),/^https:\/\//,'Relationship needs original evidence link');
    // Selecting a zero-case, zero-link country must show an explicit coverage gap, not blank the app.
    await page.getByRole('button',{name:'Choose country intelligence scope'}).click();
    await page.getByRole('combobox',{name:'Search country or code'}).fill('Antigua');
    await page.getByRole('option',{name:/Antigua/}).click();
    await network.locator('.nx-empty').waitFor({state:'visible'});
    assert.equal(await page.locator('#root').isVisible(),true,'Unknown network country blanked the root');
    assert.deepEqual(pageErrors,[],'Country selection caused a React render error');
    await page.getByRole('button',{name:'Choose country intelligence scope'}).click();
    await page.getByRole('option',{name:/Worldwide/}).click();
    await page.getByRole('button',{name:'Choose country intelligence scope'}).click();
    await page.getByRole('combobox',{name:'Search country or code'}).fill('china');
    await page.getByRole('option',{name:/China/}).click();
    await nav.getByRole('button',{name:'Countries'}).click();
    await page.getByRole('heading',{name:/Country intelligence/i}).waitFor();
    await countriesViews.getByRole('button',{name:'Networks'}).click();
    assert.match(await page.getByRole('button',{name:'Choose country intelligence scope'}).innerText(),/China/,'Nested Networks lost China country scope');
    await countriesViews.getByRole('button',{name:'Country intelligence'}).click();
    await page.getByRole('heading',{name:/Country intelligence/i}).waitFor();
    await nav.getByRole('button',{name:'Systems'}).click();
    await page.locator('.gs-root').waitFor({state:'visible',timeout:15000});
    await page.getByRole('heading',{name:'The systems behind global power.'}).waitFor({state:'visible'});
    await nav.getByRole('button',{name:'Countries'}).click();
    assert.equal(await page.locator('#ea-country-scope').count(),1,'Country selector was unexpectedly unmounted: '+JSON.stringify(pageErrors));
    assert.match(await page.locator('#ea-country-scope').innerText(),/China/,'Country selection must persist between tabs');
    await nav.getByRole('button',{name:'Risks'}).click();
    await page.getByRole('region',{name:'Risk summary visual dashboard'}).getByRole('heading',{name:/Risk signals, at a glance/i}).waitFor();
    assert.match(await page.locator('#ea-country-scope').innerText(),/China/);
    await nav.getByRole('button',{name:'More'}).click();
    await page.locator('#ea-primary-navigation.sidebar-open').waitFor({state:'visible'});
    await page.locator('#ea-primary-navigation button.nav-item').filter({hasText:'Source library'}).click();
    await page.getByRole('heading',{name:/Sources, not secrets/i}).waitFor();
    // The old country dossiers and comparative sanctions snapshots still exist, in Source Library.
    const sourceInventory=page.locator('.source-index-disclosure');
    await sourceInventory.locator('summary').click();
    await sourceInventory.locator('.cx-root').waitFor({state:'visible'});
    await sourceInventory.locator('.ip-sanction-source').first().waitFor({state:'visible',timeout:15000});
    assert.equal(await sourceInventory.locator('.ip-sanction-source').count(),2,'UK and Canadian source snapshots must be preserved');

    assert.equal(await page.locator('#ea-primary-navigation').evaluate(el=>el.classList.contains('sidebar-open')),false,'Drawer should close after a selection');
    await nav.getByRole('button',{name:'Home'}).click();
    await page.getByRole('region',{name:'Evidence-gated command alerts'}).waitFor({state:'visible'});
    assert.equal(await page.locator('.mobile-brief:visible').count(),0,'Legacy oversized mobile hero still blocks the data first screen');
    await page.reload({waitUntil:'domcontentloaded'});
    await page.getByRole('region',{name:'Evidence-gated command alerts'}).waitFor({state:'visible'});
    assert.match(await page.locator('#ea-country-scope').innerText(),/China/,'Country selection survives reload');
    await nav.getByRole('button',{name:'Risks'}).click();
    const risk=page.getByRole('region',{name:'Risk summary visual dashboard'});
    await risk.waitFor({state:'visible'});
    assert.equal(await risk.locator('.rdb-chart').count(),4,'Risks should lead with four compact charts');
    await risk.locator('.rdb-headlines > div').first().click();
    const riskDetail=page.getByRole('dialog',{name:/INFRASTRUCTURE WATCHES/i});
    await riskDetail.waitFor({state:'visible'});
    await riskDetail.getByRole('button',{name:'Close evidence detail'}).click();
    await risk.locator('.rdb-pressure-row').first().click();
    await page.getByRole('dialog',{name:/Inflation/i}).waitFor({state:'visible'});
    await page.getByRole('button',{name:'Close evidence detail'}).click();
    assert.equal(await risk.locator('.rw-probe,.gs-signal').count(),0,'Raw risk data should start collapsed');
    await risk.getByRole('button',{name:'View source data'}).click();
    await risk.locator('.rw-probes').waitFor({state:'visible'});
    await risk.getByRole('button',{name:'Hide details'}).click();
    await nav.getByRole('button',{name:'Countries'}).click();
    await page.getByRole('button',{name:'Open map'}).click();
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
