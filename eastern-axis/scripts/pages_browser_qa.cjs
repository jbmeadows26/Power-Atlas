const {chromium, request: createRequest} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const api = fs.readFileSync('eastern-axis/public-api-origin.txt','utf8').trim().replace(/\/$/,'');
const origin = (process.env.EA_BROWSER_ORIGIN || 'http://127.0.0.1:4173').replace(/\/$/, '');
const production = origin === 'https://jbmeadows26.github.io/Power-Atlas/eastern-axis';
if (origin.startsWith('https://') && !production) throw Error('Unexpected production QA origin: '+origin);
(async()=>{
  const browser=await chromium.launch({headless:true});
  const req=await createRequest.newContext({extraHTTPHeaders:{Origin:'https://jbmeadows26.github.io'}});
  async function connect(page) {
    await page.route(url=>url.toString().startsWith(api+'/api/'),async route=>{
      const url=route.request().url();
      const h={'access-control-allow-origin':'*','access-control-allow-methods':'GET, POST, OPTIONS','access-control-allow-headers':'content-type, authorization','content-type':'application/json'};
      if(route.request().method()==='OPTIONS')return route.fulfill({status:204,headers:h,body:''});
      try{
        const response=await req.fetch(url,{method:route.request().method(),data:route.request().postDataBuffer()||undefined,timeout:35000});
        await route.fulfill({status:response.status(),headers:h,body:await response.body()});
      }catch(e){
        console.warn('Backend proxy problem',url,String(e));
        await route.fulfill({status:503,headers:h,body:JSON.stringify({error:'Live API unreachable in browser test'})});
      }
    });
  }
  const errors=[];
  for(const viewport of [{width:1360,height:900},{width:390,height:844},{width:320,height:700}]){
    const context=await browser.newContext({viewport});
    const page=await context.newPage();
    page.on('pageerror',e=>errors.push(viewport.width+': '+e.message));
    const apiFailures=[];
    if (production) {
      page.on('requestfailed',request=>{
        if(request.url().startsWith(api+'/api/'))apiFailures.push(request.url()+': '+request.failure()?.errorText);
      });
      page.on('response',response=>{
        if(response.url().startsWith(api+'/api/') && response.status()>=400)
          apiFailures.push(response.url()+': HTTP '+response.status());
      });
    } else {
      // Candidate-only proxy. Production MUST use the browser's real CORS/network path.
      await connect(page);
    }
    await page.goto(origin+'/',{waitUntil:'domcontentloaded',timeout:30000});
    const scope = page.getByRole('button',{name:'Choose country intelligence scope'});
    await scope.waitFor({state:'visible',timeout:20000});
    // Every module inherits the same country-aware data-first application shell.
    const operations=page.getByRole('region',{name:'Persistent global intelligence data bar'});
    await operations.waitFor({state:'visible',timeout:20000});
    assert.equal(await operations.locator('.ea-ops-metric').count(),6,'Global statistics strip is missing');
    const workspace=page.getByRole('navigation',{name:'Primary intelligence workspaces'});
    await workspace.waitFor({state:'visible'});
    assert.ok((await workspace.locator('button').count())>=8,'New workspace navigation missing');
    if(viewport.width<600) assert.equal(await page.locator('.mobile-brief:visible').count(),0,'Obsolete mobile hero still hides the metrics');
    // The opening dashboard must expose evidence, not merely decorative charts.
    const decisionBoard=page.getByRole('region',{name:'Decision intelligence dashboard'});
    await decisionBoard.waitFor({state:'visible',timeout:20000});
    assert.equal(await decisionBoard.locator('.db-stat').count(),6,
      'Missing headline source-backed decision metrics');
    await decisionBoard.getByText('SUCCESSFUL SOURCE CHECKS',{exact:true}).waitFor({state:'visible'});
    await decisionBoard.getByText('COUNTRY-LEVEL INTELLIGENCE',{exact:true}).waitFor({state:'visible'});
    await decisionBoard.getByRole('button',{name:'Refresh feeds'}).waitFor({state:'visible'});
    const decisionWidth=await page.evaluate(()=>({width:window.innerWidth,scroll:document.documentElement.scrollWidth}));
    assert.ok(decisionWidth.scroll<=decisionWidth.width+2,
      'Decision dashboard overflows viewport '+viewport.width+'px: '+JSON.stringify(decisionWidth));
    // The first-screen country module must expose military and allied evidence,
    // not just the DOJ-only country comparison further down the page.
    const homeDefense=page.getByRole('region',{name:'Country-specific defense intelligence on Home'});
    await homeDefense.waitFor({state:'visible',timeout:20000});
    await homeDefense.getByRole('heading',{name:'Defense intelligence by country'}).waitFor({state:'visible'});
    await homeDefense.getByText('Military asset entries').first().waitFor({state:'visible'});
    const cardWithSource=homeDefense.locator('.hcd-country a[href^="https://"]').first();
    await cardWithSource.waitFor({state:'visible',timeout:20000});
    assert.ok((await homeDefense.locator('.hcd-country').count())>0,
      'No source-linked national intelligence card on the Home dashboard');
    // Country-selected Home must show the same national dossier as the other tabs.
    await homeDefense.getByRole('button',{name:'Focus dashboard on Russia'}).click();
    await homeDefense.getByRole('heading',{name:'Russia: military & allied intelligence'}).waitFor({state:'visible'});
    assert.ok((await homeDefense.locator('.cds-references a[href^="https://"]').count())>0,
      'Country Home is missing original allied/military evidence links');
    await homeDefense.getByRole('button',{name:/Return to worldwide/}).click();
    await homeDefense.getByRole('heading',{name:'Defense intelligence by country'}).waitFor({state:'visible'});
    // Test the public map's evidence layers and legend before narrowing country scope.
    const mapPanel=page.locator('.cc-map-panel');
    await mapPanel.waitFor({state:'visible',timeout:18000});
    await mapPanel.getByLabel('Country-area legend').getByText('U.S. + indexed treaty allies').waitFor({state:'visible'});
    await mapPanel.getByLabel('Current data-layer legend').getByText('Curated case', {exact:false}).waitFor({state:'visible'});
    await page.locator('svg.cc-world-svg .cc-country-shape').first().waitFor({state:'attached',timeout:20000});
    const usClass=await page.locator('svg.cc-world-svg .cc-country-shape').evaluateAll(els=>{
      const shape=els.find(el=>el.querySelector('title')?.textContent?.startsWith('United States'));
      return shape?.getAttribute('class')||'';
    });
    assert.match(usClass,/country-ally/,'U.S. should appear in the blue U.S./treaty-ally area key');
    assert.equal(await page.locator('svg.cc-world-svg a').count(),0,'Default curated-case layer must not embed unrelated hazard source links');
    await mapPanel.getByRole('button',{name:'OFAC program entries'}).click();
    await mapPanel.getByLabel('Current data-layer legend').getByText('OFAC program entries',{exact:false}).waitFor({state:'visible'});
    assert.equal(await page.locator('svg.cc-world-svg a').count(),0,'OFAC layer contains unexpected hazard hyperlinks');
    // Prevent tiny/offscreen mobile layer tabs and ambiguous overlapping event hyperlinks.
    for(const label of ['Curated cases','OFAC program entries','USGS earthquakes','NASA natural hazards']){
      const button=mapPanel.getByRole('button',{name:label});
      const bounds=await button.boundingBox();
      assert.ok(bounds && bounds.x>=-1 && bounds.x+bounds.width<=viewport.width+1,
        'Map layer clipped or inaccessible on '+viewport.width+'px: '+label+' '+JSON.stringify(bounds));
    }
    const skippedShapes=await page.locator('svg.cc-world-svg .cc-country-shape:not(.selectable)').evaluateAll(nodes=>
      nodes.map(el=>({role:el.getAttribute('role'),tab:el.getAttribute('tabindex'),cursor:getComputedStyle(el).cursor}))
    );
    assert.ok(skippedShapes.every(x=>x.role===null&&x.tab===null&&x.cursor==='default'),
      'Map has pointer-looking geography without a country dossier');
    await mapPanel.getByRole('button',{name:'USGS earthquakes'}).click();
    assert.equal(await page.locator('svg.cc-world-svg a').count(),0,
      'Map dots must select event details, never directly open an overlapping link');
    const quakes=mapPanel.locator('svg.cc-world-svg .cc-hazard-marker');
    if(await quakes.count()){
      await quakes.first().click();
      await mapPanel.locator('.cc-map-event-selected').waitFor({state:'visible',timeout:10000});
      for(const href of await mapPanel.locator('.cc-map-event-selected a').evaluateAll(nodes=>nodes.map(el=>el.getAttribute('href')))){
        assert.match(href||'',/^https:\/\/earthquake\.usgs\.gov\/earthquakes\/eventpage\//,'Nonofficial USGS selected source');
      }
    }
    await mapPanel.getByRole('button',{name:'NASA natural hazards'}).click();
    assert.equal(await page.locator('svg.cc-world-svg a').count(),0,'NASA markers must not jump directly to raw JSON');
    const nasa=mapPanel.locator('svg.cc-world-svg .cc-hazard-marker');
    if(await nasa.count()){
      await nasa.first().click();
      await mapPanel.locator('.cc-map-event-selected').waitFor({state:'visible',timeout:10000});
      for(const href of await mapPanel.locator('.cc-map-event-selected a').evaluateAll(nodes=>nodes.map(el=>el.getAttribute('href')))){
        assert.match(href||'',/^https:\/\/eonet\.gsfc\.nasa\.gov\/api\/v3\/events\//,'Nonofficial NASA selected source');
      }
    }
    await mapPanel.getByRole('button',{name:'Curated cases'}).click();
    // Catch zero-DOJ country crashes and missing all-allied publisher links.
    // Prior to the Nov 19 fix, selecting Canada or Antigua & Barbuda blanked
    // the root when a worldwide sanctions snapshot contained null regimeRecordCount.
    if(viewport.width<600){
      await page.getByRole('navigation',{name:'Mobile primary navigation'}).getByRole('button',{name:'Networks'}).click();
    }else{
      await page.locator('nav[aria-label="Main navigation"] .nav-item').filter({hasText:'Connections'}).click();
    }
    await page.locator('.cx-directory').waitFor({state:'visible',timeout:15000});
    for(const testCountry of ['Canada','Antigua & Barbuda']){
      const card=page.locator('.cx-country-grid button.cx-country').filter({has:page.getByText(testCountry,{exact:true})});
      await card.click();
      await page.locator('.cx-center h2').getByText(testCountry,{exact:true}).waitFor({state:'visible',timeout:15000});
      assert.equal(await page.locator('#root').isVisible(),true,testCountry+' blanked the React root');
      await page.getByRole('button',{name:/U.S. \+ allied source network/}).click();
      await page.locator('.cx-branch a[href^="https://"]').first().waitFor({state:'visible',timeout:15000});
      assert.ok((await page.locator('.cx-branch a[href^="https://"]').count())>=5,
        testCountry+' should expose multiple U.S. and allied government source references');
      await scope.click();
      await page.getByRole('option',{name:/Worldwide/}).click();
      await page.locator('.cx-directory').waitFor({state:'visible',timeout:15000});
    }
    await scope.click();
    await page.getByRole('combobox',{name:'Search country or code'}).fill('russ');
    await page.getByRole('option',{name:/Russia/}).click();
    assert.equal(await page.evaluate(()=>localStorage.getItem('ea.country.scope')),'RU');
    assert.match(await scope.innerText(),/Russia/);
    for(const target of ['Global systems','Supply chain','Connections']){
      if(viewport.width<600)await page.getByRole('button',{name:'Open navigation'}).click();
      await page.locator('nav[aria-label="Main navigation"] .nav-item').filter({hasText:target}).click();
      assert.match(await scope.innerText(),/Russia/,target+' lost selected scope');
      await operations.getByText('Russia',{exact:true}).first().waitFor({state:'visible'});
    }
    await page.reload({waitUntil:'domcontentloaded'});
    const afterReload = page.getByRole('button',{name:'Choose country intelligence scope'});
    await afterReload.waitFor({state:'visible',timeout:20000});
    await page.getByRole('button',{name:'Choose country intelligence scope'}).getByText('Russia').waitFor({state:'visible',timeout:20000});
    assert.match(await afterReload.innerText(),/Russia/,'scope not persistent after reload');
    await afterReload.click();
    const combo = page.getByRole('combobox',{name:'Search country or code'});
    await combo.fill('china');
    await combo.press('Enter');
    assert.match(await afterReload.innerText(),/China/);
    assert.equal(await page.evaluate(()=>localStorage.getItem('ea.country.scope')),'CN');
    if(viewport.width<600) await page.getByRole('button',{name:'Open navigation'}).click();
    await page.locator('nav[aria-label="Main navigation"] .nav-item').filter({hasText:'Command center'}).click();
    await page.getByText('China–DPRK mutual-assistance treaty (1961)',{exact:false}).first().waitFor({state:'visible',timeout:15000});
    await page.locator('.cc-security-sources a[href="https://www.everycrsreport.com/reports/R49319.html"]').waitFor({state:'visible',timeout:15000});
    assert.equal(await page.getByText('No NATO / listed bilateral alliance').count(),0,'obsolete US-only relationship label persisted');
    if(viewport.width<600)await page.getByRole('button',{name:'Open navigation'}).click();
    await page.locator('nav[aria-label="Main navigation"] .nav-item').filter({hasText:'Risk watch'}).click();
    const resilience=page.getByRole('region',{name:'Independent systemic resilience monitoring'});
    await resilience.waitFor({state:'visible',timeout:15000});
    await resilience.getByRole('heading',{name:'Early signs of cascading failure'}).waitFor({state:'visible',timeout:15000});
    await resilience.getByText('Source observations',{exact:true}).waitFor({state:'visible',timeout:25000});
    assert.match(await scope.innerText(),/China/,'Risk watch lost selected country scope');
    const dims=await page.evaluate(()=>({width:window.innerWidth,scroll:document.documentElement.scrollWidth}));
    assert.ok(dims.scroll <= dims.width+2,'Risk watch overflow at '+viewport.width+'px: '+JSON.stringify(dims));
    // Assurance runs are assessed separately from the build: unknown is not healthy.
    if(viewport.width<600)await page.getByRole('button',{name:'Open navigation'}).click();
    await page.locator('nav[aria-label="Main navigation"] .nav-item').filter({hasText:'Coverage audit'}).click();
    const assurance=page.getByRole('region',{name:'Operational assurance checks'});
    await assurance.waitFor({state:'visible',timeout:15000});
    assert.equal(await assurance.locator('.oa-card').count(),4,'Expected four independent operational assurance checks');
    await assurance.getByText('Live production browser QA',{exact:true}).waitFor({state:'visible'});
    await assurance.getByText('Not independently connected:',{exact:false}).waitFor({state:'visible'});
    const assuranceDims=await page.evaluate(()=>({width:window.innerWidth,scroll:document.documentElement.scrollWidth}));
    assert.ok(assuranceDims.scroll<=assuranceDims.width+2,'Assurance panel overflow at '+viewport.width+'px: '+JSON.stringify(assuranceDims));
    // Navigation-wide release gate: inspect all 16 sections on every viewport,
    // retaining the active country selector and catching empty routes or overflow.
    const allSections=[
      'Command center','Countries','World Factbook','Global systems','Supply chain',
      'Early warning','Risk watch','AI analyst','Coverage audit','Connections',
      'Defense intelligence','Investigations','Collection desk','Verification lab',
      'Source library','Methodology'
    ];
    const inspected=[];
    for(const sectionName of allSections){
      if(viewport.width<600)await page.getByRole('button',{name:'Open navigation'}).click();
      const navItem=page.locator('nav[aria-label="Main navigation"] .nav-item').filter({hasText:sectionName});
      await navItem.click();
      const active=page.locator('nav[aria-label="Main navigation"] .nav-item.active').first();
      assert.ok((await active.innerText()).includes(sectionName),'Wrong active tab after selecting '+sectionName);
      const countryLabel=await page.getByRole('button',{name:'Choose country intelligence scope'}).innerText();
      assert.match(countryLabel,/China/,sectionName+' lost country scope');
      await page.waitForTimeout(120);
      const mainText=await page.locator('.content').innerText();
      assert.ok(mainText.length>90,sectionName+' rendered an empty content panel');
      const layout=await page.evaluate(()=>({viewport:innerWidth,document:document.documentElement.scrollWidth}));
      assert.ok(layout.document<=layout.viewport+2,sectionName+' overflows '+viewport.width+'px: '+JSON.stringify(layout));
      if(viewport.width===390){
        const slug=sectionName.toLowerCase().replace(/[^a-z0-9]+/g,'-');
        await page.screenshot({path:'audit-output/eastern-axis-tab-'+slug+'-390.png'});
      }
      inspected.push(sectionName);
    }
    assert.equal(inspected.length,16,'Not every navigation section was inspected');
    console.log('ALL TABS QA',viewport.width,inspected.join(' | '));
    if(production) assert.equal(apiFailures.length,0,'Real browser-to-Neon API failures: '+apiFailures.join('; '));
    await page.screenshot({path:'audit-output/eastern-axis-'+viewport.width+'.png',fullPage:true});
    console.log('Browser QA passed',viewport.width,production?'published Pages with direct Neon browser requests':'candidate build', 'country scope, treaty facts, resilience telemetry, assurance and responsive layout');
    await context.close();
  }
  await browser.close();
  await req.dispose();
  if(errors.length){console.error('Uncaught browser exceptions',errors);process.exitCode=1;}
})().catch(e=>{console.error(e);process.exit(1)});
