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
  async function closeMobileFilters(page){
    if(await page.evaluate(()=>innerWidth<=980)&&await page.locator('.ea-global-filters.open').count())
      await page.getByRole('button',{name:'Close global filters'}).click();
  }
  async function openCountryPicker(page){
    if(await page.evaluate(()=>innerWidth<=980)&&!await page.locator('.ea-global-filters.open').count())
      await page.getByRole('button',{name:'Edit Country filter'}).click();
    await page.locator('#ea-country-scope').click();
  }
  async function openWorkspace(page,domain,tab){
    await closeMobileFilters(page);
    if(await page.evaluate(()=>innerWidth<=980)){
      await page.getByRole('navigation',{name:'Mobile primary navigation'}).getByRole('button',{name:'Domains'}).click();
      const grid=page.getByRole('region',{name:'Eight intelligence domains'});
      assert.equal(await grid.locator('button').count(),8,'Mobile grid lost a primary domain');
      await grid.getByRole('button',{name:domain,exact:true}).click();
    }else await page.locator('#ea-primary-navigation button.nav-item').filter({hasText:domain}).click();
    if(tab)await page.locator('.ea-domain-tabs').getByRole('button',{name:tab,exact:true}).click();
  }
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
        // Navigating between 16 modules intentionally unmounts React effects.
        // Chromium aborts their in-flight GETs; this is not an upstream outage.
        // Continue to fail on every HTTP 4xx/5xx and non-aborted network error.
        const reason=request.failure()?.errorText||'unknown network error';
        if(request.url().startsWith(api+'/api/') && reason!=='net::ERR_ABORTED')
          apiFailures.push(request.url()+': '+reason);
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
    const scope = page.locator('#ea-country-scope');
    await page.locator('.ea-unfiltered-command').waitFor({state:'attached',timeout:20000});
    assert.equal(await scope.count(),0,'Worldwide command workspaces must not display a country filter');
    assert.equal(await page.locator('.ea-mobile-filter-pills').count(),0,'No redundant mobile filter chips in Command');
    // Report a bug lives in the existing menu and never redirects visitors to GitHub.
    if(viewport.width<=980)await page.getByRole('navigation',{name:'Mobile primary navigation'}).getByRole('button',{name:'Briefcase'}).click();
    const bugTrigger=viewport.width<=980?page.getByRole('button',{name:/Report a bug · no login required/}):
      page.locator('#ea-primary-navigation').getByRole('button',{name:/Report a bug/});
    await bugTrigger.waitFor({state:'visible'});
    await bugTrigger.click();
    const bugDialog=page.getByRole('dialog',{name:'Report a bug'});
    await bugDialog.waitFor({state:'visible'});
    const formSrc=await bugDialog.locator('iframe').getAttribute('src');
    assert.match(formSrc||'',/^https:\/\/tally\.so\/embed\/LDKRaj\?/);
    assert.match(formSrc||'',/section=Command\+center/);
    assert.equal((formSrc||'').includes('github.com'),false,'No GitHub login allowed for bug reports');
    await bugDialog.getByRole('button',{name:'Close bug report'}).click();
    await bugDialog.waitFor({state:'detached'});
    if(viewport.width<=980)await page.getByRole('navigation',{name:'Mobile primary navigation'}).getByRole('button',{name:'Home'}).click();
    assert.equal(await page.locator('.ea-bug-dialog').count(),0,'Bug dialog failed to close');
    // Core release invariant: no global stat ribbon repeated on every page.
    assert.equal(await page.locator('.ea-ops').count(),0,'Repeated monitoring stats should not render anywhere');
    assert.equal(await page.locator('.ea-module-context').count(),0,'Generic duplicate page context should be removed');
    assert.equal(await page.getByRole('navigation',{name:'Primary intelligence workspaces'}).count(),0,'Horizontal duplicate navigation must be removed');
    const command=page.getByRole('region',{name:'Evidence-gated command alerts'});
    await command.waitFor({state:'visible',timeout:20000});
    assert.equal(await page.locator('.dr-root').count(),0,
      'Raw movement screens must not appear on Command without analyst escalation');
    assert.ok(await command.locator('.sr-head').count()>0,'Command analyst report header missing');
    // A visually safe UI must not conceal a still-unsafe underlying JSON
    // artifact. Reject any release that publishes advisory-only promotions.
    const triageResponse=await page.request.get(origin+'/analysis/early-warning-triage.json',{
      headers:{'Cache-Control':'no-cache','Pragma':'no-cache'},timeout:20000});
    assert.equal(triageResponse.status(),200,'Published analyst triage JSON is not available');
    const triage=await triageResponse.json();
    assert.ok(triage&&Array.isArray(triage.alerts)&&Array.isArray(triage.reviews),
      'Published analyst triage JSON lacks verified review records');
    assert.equal(triage.summary.elevated,triage.alerts.length,
      'Published triage summary disagrees with alerts array');
    assert.equal(triage.summary.monitoring,triage.reviews.length-triage.alerts.length,
      'Published triage monitoring count disagrees with record total');
    const byId=new Map(triage.reviews.map(r=>[r.id,r]));
    for(const finding of triage.alerts){
      assert.equal(finding.kind,'metric',
        'Official local weather warnings must not be published as Command alerts');
      const sourceRow=byId.get(finding.id);
      assert.ok(sourceRow&&sourceRow.status==='elevated'&&sourceRow.modelReviewed&&
        sourceRow.anomalous&&sourceRow.corroborated&&sourceRow.fresh,
        'Published Command alert lacks full independent evidence gate');
    }
    assert.equal(triage.reviews.filter(r=>r.status==='elevated'&&r.kind!=='metric').length,0,
      'Underlying JSON still contains an incorrectly elevated advisory');
    // A NOAA severe warning alone is never a verified strategic anomaly.
    // Compare the actual displayed cards and count, not just React mounting.
    await command.locator('.sr-stats strong').first().waitFor({state:'visible',timeout:20000});
    const promoted=Number((await command.locator('.sr-stats strong').first().innerText()).trim());
    const commandRows=command.locator('.sr-rows .sr-item');
    assert.ok(Number.isFinite(promoted),'Command elevated count is not numeric');
    assert.equal(promoted,await commandRows.count(),'Command alert count differs from visible promoted records');
    assert.deepEqual(await commandRows.evaluateAll(els=>els
      .filter(el=>/Special Marine Warning|Coastal Flood Warning/i.test(el.textContent||'')).map(el=>el.textContent)),
      [],'Local NWS warnings must never appear as strategic Command findings');
    assert.equal(await commandRows.filter({hasText:'Jupiter Inlet'}).count(),0,
      'Formerly elevated Jupiter Inlet marine warning still appears in Command');
    await openWorkspace(page,'Macroeconomics & Markets','Markets & early warning');
    const disclosure=page.locator('.pew-context-radar');
    await disclosure.waitFor({state:'visible',timeout:20000});
    assert.equal(await disclosure.getAttribute('open'),null,'Cross-domain screening should be collapsed by default');
    await disclosure.locator('summary').click();
    const radar=page.getByRole('region',{name:'Decision radar by domain'});
    await radar.waitFor({state:'visible',timeout:20000});
    assert.equal(await radar.locator('.dr-lane').count(),4,'Early Warning must preserve four cross-domain contexts');
    for(const domain of ['Finance','Trade & essential goods','Infrastructure & survival','Military & intelligence'])
      await radar.getByRole('heading',{name:domain}).waitFor({state:'visible'});
    await radar.locator('.dr-pair').first().waitFor({state:'visible',timeout:20000});
    assert.ok(await radar.locator('.dr-move-foot a[href^="https://"]').count()>0,
      'Measured comparisons must retain original sources');
    await radar.getByRole('button',{name:'Review triggers'}).click();
    assert.ok((await radar.locator('.dr-lane').count())<=4,'Review filter not applied');
    await radar.getByRole('button',{name:'Blind spots'}).click();
    await radar.getByRole('button',{name:'All domains'}).click();
    assert.equal(await radar.locator('.dr-lane').count(),4,'All domains filter did not restore cards');
    const decisionWidth=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth}));
    assert.ok(decisionWidth.scroll<=decisionWidth.width+2,
      'Early Warning radar overflows viewport '+viewport.width+'px: '+JSON.stringify(decisionWidth));
    await radar.getByRole('button',{name:'Analyze'}).first().waitFor({state:'visible'});
    await radar.locator('.dr-finance footer button').click();
    const fundingTab=page.getByRole('button',{name:'Overnight funding'});
    await fundingTab.waitFor({state:'visible',timeout:15000});
    await page.waitForFunction(()=>Array.from(document.querySelectorAll('button')).some(b=>
      b.textContent.trim()==='Overnight funding'&&b.getAttribute('aria-pressed')==='true'),null,{timeout:15000});
    assert.equal(await fundingTab.getAttribute('aria-pressed'),'true','Finance card did not select funding comparisons');
    await openWorkspace(page,'Command & Situation Room','Situation room');
    await command.waitFor({state:'visible',timeout:15000});
    assert.equal(await page.locator('.dr-root').count(),0,'Command must not repeat unscreened radar data');
    assert.equal(await page.locator('.cc-map-panel').count(),0,'Command still contains geospatial map');
    assert.equal(await page.locator('.cc-stream-panel,.cc-connect-panel,.cc-live-panel').count(),0,'Command repeats source data');
    await openWorkspace(page,'Macroeconomics & Markets','Systemic risk');
    const risk=page.getByRole('region',{name:'Risk summary visual dashboard'});
    await risk.waitFor({state:'visible',timeout:20000});
    assert.equal(await risk.locator('.rdb-chart').count(),4,'Risk needs four compact visual panels');
    assert.equal(await risk.locator('.rw-probe,.gs-signal').count(),0,'Risks shows raw evidence before user requests it');
    await risk.getByRole('button',{name:'View source data'}).click();
    await risk.locator('.rw-probes').waitFor({state:'visible',timeout:20000});
    await risk.getByRole('button',{name:'Hide details'}).click();
    assert.equal(await risk.locator('.rw-probe,.gs-signal').count(),0,'Risk evidence did not collapse');
    await openWorkspace(page,'Geopolitics & Intelligence','Country dossiers');
    // Regression: selecting the United States must not make the country index empty,
    // even when the directory's optional allied-state filter is switched off.
    await openCountryPicker(page);
    await page.getByRole('combobox',{name:'Search country or code'}).fill('United States');
    await page.getByRole('option',{name:/United States/}).click();
    await closeMobileFilters(page);
    const usDirectoryRow=page.locator('.country-directory .country-row').filter({hasText:'United States'});
    await usDirectoryRow.waitFor({state:'visible',timeout:15000});
    const includeAllies=page.getByRole('checkbox',{name:'Include U.S. primary treaty allies'});
    await includeAllies.uncheck();
    await usDirectoryRow.waitFor({state:'visible',timeout:10000});
    assert.equal(await usDirectoryRow.count(),1,'Selected United States disappeared when allied countries were excluded');
    await includeAllies.check();
    await openCountryPicker(page);
    await page.getByRole('combobox',{name:'Search country or code'}).fill('Worldwide');
    await page.getByRole('option',{name:/Worldwide/}).click();
    await closeMobileFilters(page);
    await page.waitForFunction(()=>document.querySelectorAll('.country-directory .country-row').length>10,null,{timeout:15000});
    await page.getByRole('button',{name:'Open map'}).click();
    // Test source-linked map layers only inside Countries.
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
    // Networks belongs to Countries. Source inventories remain in Source Library.
    assert.equal(await page.locator('.mobile-bottom-nav').count(),0,'Legacy duplicate mobile navigation must stay absent');
    assert.equal(await page.locator('.ea-mobile-primary').count(),1,'Four-route nav must mount only once');
    await openWorkspace(page,'Geopolitics & Intelligence','Country dossiers');
    assert.equal(await page.getByRole('group',{name:'Country intelligence views'}).count(),0,
      'Country and network routes must be consolidated into one view');
    await page.getByRole('button',{name:'Explore relationships'}).click();
    const network=page.getByRole('region',{name:'Sourced relationship networks'});
    await network.waitFor({state:'visible',timeout:15000});
    await network.locator('.nx-graph').waitFor({state:'visible'});
    assert.ok(await network.locator('.nx-connection').count()>=2,'Global network spotlight should show sourced ties');
    assert.equal(await network.locator('.ip-sanction-source').count(),0,'Sanctions inventories must not replace Networks');
    assert.match(await network.locator('.nx-source').getAttribute('href'),/^https:\/\//,'Network evidence must link to original publisher');
    for(const countryName of ['Canada','Antigua & Barbuda']){
      await openCountryPicker(page);
      await page.getByRole('combobox',{name:'Search country or code'}).fill(countryName);
      await page.getByRole('option',{name:countryName,exact:false}).click();
    await closeMobileFilters(page);
      if(countryName==='Canada'){
        await network.locator('.nx-connection').filter({hasText:'NATO'}).first().waitFor({state:'visible',timeout:15000});
      }else{
        await network.locator('.nx-empty').waitFor({state:'visible',timeout:15000});
      }
      assert.equal(await page.locator('#root').isVisible(),true,countryName+' blanked the React root');
    }
    await openCountryPicker(page);
    await page.getByRole('combobox',{name:'Search country or code'}).fill('russ');
    await page.getByRole('option',{name:/Russia/}).click();
    await closeMobileFilters(page);
    assert.equal(await page.evaluate(()=>localStorage.getItem('ea.country.scope')),'RU');
    assert.match(await scope.textContent(),/Russia/);
    for(const target of [
      {name:'Growth & labor',domain:'Macroeconomics & Markets',tab:'Growth & labor'},
      {name:'Supply chains',domain:'Trade & Supply Chains',tab:'Supply chains'},
      {name:'Countries',domain:'Geopolitics & Intelligence',tab:'Country dossiers'}
    ]){
      await openWorkspace(page,target.domain,target.tab);
      assert.match(await scope.textContent(),/Russia/,target.name+' lost selected scope');
      assert.equal(await page.locator('.ea-ops').count(),0,'Shared stats strip returned on '+target.name);
      if(target.name==='Growth & labor')await page.locator('.gs-root').waitFor({state:'visible'});
      if(target.name==='Supply chains')await page.locator('.sc-root').waitFor({state:'visible'});
      if(target.name==='Countries'){
        if(await page.getByRole('button',{name:'Explore relationships'}).count())
          await page.getByRole('button',{name:'Explore relationships'}).click();
        await network.locator('.nx-graph').waitFor({state:'visible',timeout:15000});
        assert.match(await scope.textContent(),/Russia/,'Integrated network analysis lost country scope');
      }
    }
    await page.reload({waitUntil:'domcontentloaded'});
    const afterReload = page.locator('#ea-country-scope');
    await page.getByRole('heading',{name:/Country intelligence/i}).waitFor({state:'visible',timeout:20000});
    await afterReload.waitFor({state:'attached',timeout:20000});
    assert.match(await afterReload.textContent(),/Russia/,'Reload must retain last visited country dossier');
    await openWorkspace(page,'Command & Situation Room','Situation room');
    await page.getByRole('region',{name:'Evidence-gated command alerts'}).waitFor({state:'visible',timeout:20000});
    assert.equal(await afterReload.count(),0,'Global command must hide country controls');
    assert.equal(await page.evaluate(()=>localStorage.getItem('ea.country.scope')),'RU');
    await openWorkspace(page,'Geopolitics & Intelligence','Country dossiers');
    await afterReload.waitFor({state:'attached',timeout:20000});
    assert.match(await afterReload.textContent(),/Russia/,'Returning to Countries must restore prior selection');
    // Defense is additive; country context persists and its alert module must mount once.
    await openWorkspace(page,'Defense, Security & Cyber','Global conflict watch');
    await page.getByRole('region',{name:'Global conflict and hotspot analyst'}).waitFor({state:'visible',timeout:15000});
    assert.equal(await page.locator('.gc-root').count(),1,'Global conflict analyst must mount exactly once');
    assert.match(await page.locator('#ea-country-scope').textContent(),/Russia/,
      'Conflict analyst lost the selected country scope');
    await openWorkspace(page,'Defense, Security & Cyber','Military asset changes');
    await page.getByRole('region',{name:'Military asset change analyst'}).waitFor({state:'visible',timeout:15000});
    assert.equal(await page.locator('.mac-root').count(),1,'Asset analyst must appear once in Defense');
    assert.match(await page.locator('#ea-country-scope').textContent(),/Russia/,'Asset analyst lost saved country context');
    await openWorkspace(page,'Geopolitics & Intelligence','Country dossiers');
    await openCountryPicker(page);
    const combo = page.getByRole('combobox',{name:'Search country or code'});
    await combo.fill('china');
    await combo.press('Enter');
    assert.match(await afterReload.textContent(),/China/);
    assert.equal(await page.evaluate(()=>localStorage.getItem('ea.country.scope')),'CN');
    await openWorkspace(page,'Geopolitics & Intelligence','Country dossiers');
    // The country brief is permanently visible; networks are an inline evidence expansion.
    assert.equal(await page.locator('.ea-country-subnav').count(),0,
      'Legacy competing country/network selector has returned');
    await page.locator('.country-brief .brief-relationship').waitFor({state:'visible',timeout:15000});
    const countryPanelWidth=await page.locator('.country-brief').evaluate(el=>el.getBoundingClientRect().width);
    assert.ok(countryPanelWidth >= Math.min(260,viewport.width-70),'Country dossier collapsed at '+viewport.width+'px: '+countryPanelWidth);

    // The asset dataset is required: source-attributed military hardware must
    // render in the country dossier rather than disappear behind the API feed.
    const equipment=page.locator('.country-brief .di-country-equip');
    await equipment.waitFor({state:'attached',timeout:25000});
    const tanks=equipment.locator('.di-equip-metric').filter({hasText:'Main battle tanks'});
    assert.equal(await tanks.count(),1,'China main battle tanks indicator is missing');
    assert.match(await tanks.textContent(),/4,800/,'Pinned 2026 China tank estimate not populated');
    const assetSource=page.locator('.country-brief .di-equipment-health');
    await assetSource.waitFor({state:'attached',timeout:20000});
    assert.match(await assetSource.textContent(),/equipment observations/,'Military equipment collection status missing');
    const categoryPicker=page.locator('.country-brief #di-asset-category');
    await categoryPicker.selectOption('Land');
    assert.ok(await page.locator('.country-brief .di-asset').count()>2,'China land asset equipment records missing');
    assert.equal(await page.locator('.country-brief .di-asset').filter({hasText:' / Naval'}).count(),0,
      'Country asset category filter includes unrelated naval figures');
    await categoryPicker.selectOption('All assets');
    await page.locator('.ea-treaty-sources a[href="https://www.everycrsreport.com/reports/R49319.html"]').waitFor({state:'visible',timeout:15000});
    assert.equal(await page.getByText('No NATO / listed bilateral alliance').count(),0,'obsolete US-only relationship label persisted');
    await openWorkspace(page,'Macroeconomics & Markets','Systemic risk');
    const scopedRisk=page.getByRole('region',{name:'Risk summary visual dashboard'});
    await scopedRisk.waitFor({state:'visible',timeout:15000});
    await scopedRisk.getByRole('heading',{name:'Risk signals, at a glance.'}).waitFor({state:'visible'});
    assert.equal(await scopedRisk.locator('.rdb-chart').count(),4,'Country Risks must remain charts-first');
    assert.equal(await page.locator('.rw-probes,.gs-signal').count(),0,'Country Risks should not show raw observations by default');
    assert.match(await scope.textContent(),/China/,'Systemic risk lost selected country scope');
    const dims=await page.evaluate(()=>({width:window.innerWidth,scroll:document.documentElement.scrollWidth}));
    assert.ok(dims.scroll <= dims.width+2,'Risk watch overflow at '+viewport.width+'px: '+JSON.stringify(dims));
    // Assurance runs are assessed separately from the build: unknown is not healthy.
    await openWorkspace(page,'Command & Situation Room','Coverage audit');
    const assurance=page.getByRole('region',{name:'Operational assurance checks'});
    await assurance.waitFor({state:'visible',timeout:15000});
    assert.equal(await assurance.locator('.oa-card').count(),4,'Expected four independent operational assurance checks');
    await assurance.getByText('Live production browser QA',{exact:true}).waitFor({state:'visible'});
    await assurance.getByText('Not independently connected:',{exact:false}).waitFor({state:'visible'});
    const health=page.getByRole('region',{name:'Connected sources and collector freshness'});
    await health.waitFor({state:'visible'});
    assert.equal(await health.locator('.cs-feed').count(),4,'Source health must be kept on Coverage rather than Home');
    await health.getByRole('button',{name:'View collector records'}).click();
    await health.locator('.cs-details').waitFor({state:'visible'});
    await health.getByRole('button',{name:'Hide collector records'}).click();
    const assuranceDims=await page.evaluate(()=>({width:window.innerWidth,scroll:document.documentElement.scrollWidth}));
    assert.ok(assuranceDims.scroll<=assuranceDims.width+2,'Assurance panel overflow at '+viewport.width+'px: '+JSON.stringify(assuranceDims));

    // Navigation-wide gate: every original screen must remain reachable from
    // exactly one eight-domain sidebar, and source-linked panels must survive.
    const allSections=[
      ['Situation room','Command & Situation Room','Situation room'],
      ['AI analyst','Command & Situation Room','AI analyst'],
      ['Collection desk','Command & Situation Room','Collection desk'],
      ['Verification lab','Command & Situation Room','Verification lab'],
      ['Coverage audit','Command & Situation Room','Coverage audit'],
      ['Source library','Command & Situation Room','Source library'],
      ['Methodology','Command & Situation Room','Methodology'],
      ['Countries','Geopolitics & Intelligence','Country dossiers'],
      ['World Factbook','Geopolitics & Intelligence','World Factbook'],
      ['Investigations','Geopolitics & Intelligence','Investigations'],
      ['Defense intelligence','Defense, Security & Cyber','Defense intelligence'],
      ['Global conflict watch','Defense, Security & Cyber','Global conflict watch'],
      ['Military asset changes','Defense, Security & Cyber','Military asset changes'],
      ['Cyber resilience','Defense, Security & Cyber','Cyber resilience'],
      ['Economic pulse','Macroeconomics & Markets','Economic pulse'],
      ['Growth & labor','Macroeconomics & Markets','Growth & labor'],
      ['Markets & early warning','Macroeconomics & Markets','Markets & early warning'],
      ['Systemic risk','Macroeconomics & Markets','Systemic risk'],
      ['Supply chains','Trade & Supply Chains','Supply chains'],
      ['Product shortages','Trade & Supply Chains','Product shortages'],
      ['Trade baselines','Trade & Supply Chains','Trade baselines'],
      ['Corporate intelligence','Business, Corporate & Tech','Corporate intelligence'],
      ['Energy & resources','Energy, Resources & Climate','Energy & resources'],
      ['Population & climate','Demographics & Biosecurity','Population & climate']
    ];
    assert.equal(await page.locator('#ea-primary-navigation button.nav-item').count(),8,'Sidebar must have exactly eight domains');
    assert.equal(await page.locator('.mobile-bottom-nav').count(),0,'Legacy duplicate nav must not mount');
    assert.equal(await page.locator('.ea-mobile-primary').count(),1,'Four-route nav must mount only once');
    assert.equal(await page.locator('.ea-domain-tabs').count(),1,'Duplicate horizontal tabs mounted');
    const inspected=[];
    for(const [sectionName,domainName,tabName] of allSections){
      await openWorkspace(page,domainName,tabName);
      const active=page.locator('nav[aria-label="Main navigation"] .nav-item.active');
      assert.equal(await active.count(),1,'Exactly one domain must be active for '+sectionName);
      assert.ok((await active.innerText()).includes(domainName),'Wrong domain after '+sectionName);
      const activeTab=page.locator('.ea-domain-tabs button.active');
      assert.equal(await activeTab.count(),1,'Exactly one workspace tab must be active for '+sectionName);
      assert.equal((await activeTab.innerText()).trim(),tabName,'Wrong contextual tab for '+sectionName);
      if(domainName==='Command & Situation Room'){
        assert.equal(await scope.count(),0,sectionName+' incorrectly exposes country filters');
        assert.equal(await page.locator('.ea-mobile-filter-pills').count(),0,sectionName+' repeats mobile filter pills');
      }else assert.match(await scope.textContent(),/China/,sectionName+' lost persistent country context');
      await page.waitForTimeout(100);
      assert.equal(await page.locator('.ea-ops').count(),0,sectionName+' repeats global counters');
      assert.equal(await page.locator('.ea-module-context').count(),0,sectionName+' repeats generic context');
      if(sectionName!=='Markets & early warning')
        assert.equal(await page.locator('.dr-root').count(),0,sectionName+' must not show screening radar by default');
      else
        assert.equal(await page.locator('.pew-context-radar').getAttribute('open'),null,'Radar must remain collapsed until requested');
      if(sectionName==='Countries'){
        assert.equal(await page.locator('.ea-country-subnav').count(),0,'Country / Networks duplicate navigation returned');
        await page.getByRole('heading',{name:/Country intelligence/i}).waitFor({state:'visible'});
        if(await page.getByRole('button',{name:'Explore relationships'}).count())
          await page.getByRole('button',{name:'Explore relationships'}).click();
        const network=page.getByRole('region',{name:'Sourced relationship networks'});
        await network.waitFor({state:'visible'});
        assert.equal(await network.locator('.ip-sanction-source').count(),0,'Relationships replaced by source inventory');
        await page.getByRole('button',{name:'Hide relationships'}).click();
        assert.equal(await network.count(),0,'Country relationships did not collapse');
      }
      if(sectionName==='AI analyst'){
        const analyst=page.locator('.ea-agent');
        await analyst.locator('.ea-agent-stats b').first().waitFor({state:'visible',timeout:15000});
        await page.waitForFunction(()=>Number(document.querySelector('.ea-agent-stats b')?.textContent||0)>0,{},{timeout:15000});
        assert.ok(Number(await analyst.locator('.ea-agent-stats b').first().innerText())>0,'AI analyst lost source totals');
        await analyst.getByRole('heading',{name:'Global source coverage'}).waitFor({state:'visible'});
        assert.equal(await analyst.locator('.ea-agent-context').count(),0,
          'Worldwide operational analyst must not display country-specific coverage limitations');
        await analyst.getByRole('heading',{name:'Original-source evidence'}).waitFor({state:'visible'});
        assert.ok(await analyst.locator('.ea-agent-records a').count()>0,
          'Global analyst source documents must remain accessible');
        assert.equal(await page.locator('#ea-country-scope').count(),0,
          'AI analyst submenu must not expose nonfunctional country filters');
      }
      if(sectionName==='Economic pulse'){
        const dashboard=page.getByRole('region',{name:'Unified economic intelligence'});
        await dashboard.waitFor({state:'visible',timeout:15000});
        assert.equal(await dashboard.locator('.ei-pulse > div').count(),6,'Economic overview lost six KPI cards');
        assert.equal(await dashboard.locator('.ei-domain').count(),5,'Economic overview lost five underlying modules');
        assert.equal(await dashboard.locator('.ei-tabs').count(),0,'Legacy economic menu duplicates the workspace tabs');
      }
      if(sectionName==='Growth & labor'||sectionName==='Trade baselines'||sectionName==='Energy & resources'||sectionName==='Population & climate'){
        await page.locator('.gs-root').waitFor({state:'visible',timeout:15000});
      }
      if(sectionName==='Supply chains')await page.locator('.sc-root').waitFor({state:'visible',timeout:15000});
      if(sectionName==='Product shortages'){
        const shortage=page.getByRole('region',{name:'Product shortage outlook'});
        await shortage.waitFor({state:'visible',timeout:15000});
        await shortage.locator('.sf-item').first().waitFor({state:'visible',timeout:15000});
        assert.equal(await shortage.locator('.sf-item').count(),14,'Fourteen existing product-shortage scenarios lost');
        await shortage.locator('.sf-item-head').first().click();
        await shortage.locator('.sf-evidence-list a').first().waitFor({state:'visible',timeout:15000});
      }
      if(sectionName==='Markets & early warning'){
        const early=page.getByRole('region',{name:'Global physical and economic early-warning intelligence'});
        await early.waitFor({state:'visible',timeout:15000});
        assert.equal(await early.locator('.pew-summary>div').count(),4,'Early warning lost original KPI panels');
        const gate=early.getByRole('button',{name:'View source data'});
        assert.equal(await gate.getAttribute('aria-expanded'),'false','Source data is open without consent');
        await gate.click();
        await early.locator('.pew-indicators').waitFor({state:'visible'});
        await early.getByRole('button',{name:'Hide source data'}).click();
        const dashboard=page.getByRole('region',{name:'Unified economic intelligence'});
        await dashboard.getByRole('button',{name:'Financial markets'}).click();
        await dashboard.locator('.fm-root').waitFor({state:'visible',timeout:15000});
      }
      if(sectionName==='Systemic risk')await page.locator('.rdb-charts').waitFor({state:'visible',timeout:15000});
      const mainText=await page.locator('.content').innerText();
      assert.ok(mainText.length>90,sectionName+' rendered empty content');
      const layout=await page.evaluate(()=>({viewport:innerWidth,document:document.documentElement.scrollWidth}));
      if(layout.document>layout.viewport+2){
        const overflowing=await page.evaluate(()=>Array.from(document.querySelectorAll('.content *'))
          .map(el=>({tag:el.tagName,className:typeof el.className==='string'?el.className.slice(0,90):'',right:Math.round(el.getBoundingClientRect().right)}))
          .filter(el=>el.right>innerWidth+2).sort((a,b)=>b.right-a.right).slice(0,12));
        console.error('Overflow offenders',sectionName,viewport.width,JSON.stringify(overflowing));
      }
      assert.ok(layout.document<=layout.viewport+2,sectionName+' overflows '+viewport.width+'px: '+JSON.stringify(layout));
      if(viewport.width===390)
        await page.screenshot({path:'audit-output/eastern-axis-tab-'+sectionName.toLowerCase().replace(/[^a-z0-9]+/g,'-')+'-390.png'});
      inspected.push(sectionName);
    }
    assert.equal(inspected.length,allSections.length,'Not every domain section was inspected');
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
