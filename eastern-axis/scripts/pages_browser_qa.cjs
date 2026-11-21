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
    const scope = page.getByRole('button',{name:'Choose country intelligence scope'});
    await scope.waitFor({state:'visible',timeout:20000});
    // Report a bug lives in the existing menu and never redirects visitors to GitHub.
    if(viewport.width<600)await page.getByRole('button',{name:'Open navigation'}).click();
    const bugTrigger=page.locator('#ea-primary-navigation').getByRole('button',{name:/Report a bug/});
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
    assert.equal(await page.locator('.ea-bug-dialog').count(),0,'Bug dialog failed to close');
    // Core release invariant: no global stat ribbon repeated on every page.
    assert.equal(await page.locator('.ea-ops').count(),0,'Repeated monitoring stats should not render anywhere');
    assert.equal(await page.locator('.ea-module-context').count(),0,'Generic duplicate page context should be removed');
    assert.equal(await page.getByRole('navigation',{name:'Primary intelligence workspaces'}).count(),0,'Horizontal duplicate navigation must be removed');
    const radar=page.getByRole('region',{name:'Decision radar by domain'});
    await radar.waitFor({state:'visible',timeout:20000});
    assert.equal(await radar.locator('.dr-lane').count(),4,'Home must show four distinct decision domains');
    for(const domain of ['Finance','Trade & essential goods','Infrastructure & survival','Military & intelligence'])
      await radar.getByRole('heading',{name:domain}).waitFor({state:'visible'});
    await radar.locator('.dr-pair').first().waitFor({state:'visible',timeout:20000});
    assert.ok(await radar.locator('.dr-move-foot a[href^="https://"]').count()>0,
      'Data comparisons must link to original sources');
    await radar.getByRole('button',{name:'Review triggers'}).click();
    assert.ok((await radar.locator('.dr-lane').count())<=4,'Review filter not applied');
    await radar.getByRole('button',{name:'Blind spots'}).click();
    await radar.getByRole('button',{name:'All domains'}).click();
    assert.equal(await radar.locator('.dr-lane').count(),4,'All domains filter did not restore all cards');
    const decisionWidth=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth}));
    assert.ok(decisionWidth.scroll<=decisionWidth.width+2,
      'Home radar overflows viewport '+viewport.width+'px: '+JSON.stringify(decisionWidth));
    // Country scope retains independent benchmarks, never presents global reports as country events.
    await radar.getByRole('button',{name:'Analyze'}).first().waitFor({state:'visible'});
    // A decision drilldown must land in the right measured domain, not an unrelated list.
    await radar.locator('.dr-finance footer button').click();
    const fundingTab=page.getByRole('button',{name:'Overnight funding'});
    await fundingTab.waitFor({state:'visible',timeout:15000});
    assert.equal(await fundingTab.getAttribute('aria-pressed'),'true','Finance card did not select funding comparisons');
    if(viewport.width<600)await page.getByRole('button',{name:'Open navigation'}).click();
    await page.locator('nav[aria-label="Main navigation"] .nav-item').filter({hasText:'Command center'}).click();
    await radar.waitFor({state:'visible',timeout:15000});
    // Home contains only the decision radar; geospatial layers belong to Countries.
    assert.equal(await page.locator('.cc-map-panel').count(),0,'Home still contains the geospatial map');
    assert.equal(await page.locator('.cc-stream-panel,.cc-connect-panel,.cc-live-panel').count(),0,'Home still repeats investigation/source/earthquake lists');
    if(viewport.width<600)await page.getByRole('button',{name:'Open navigation'}).click();
    await page.locator('nav[aria-label="Main navigation"] .nav-item').filter({hasText:'Risk watch'}).click();
    const risk=page.getByRole('region',{name:'Risk summary visual dashboard'});
    await risk.waitFor({state:'visible',timeout:20000});
    assert.equal(await risk.locator('.rdb-chart').count(),4,'Risk needs four compact visual panels');
    assert.equal(await risk.locator('.rw-probe,.gs-signal').count(),0,'Risks shows raw evidence before user requests it');
    await risk.getByRole('button',{name:'View source data'}).click();
    await risk.locator('.rw-probes').waitFor({state:'visible',timeout:20000});
    await risk.getByRole('button',{name:'Hide details'}).click();
    assert.equal(await risk.locator('.rw-probe,.gs-signal').count(),0,'Risk evidence did not collapse');
    if(viewport.width<600)await page.getByRole('button',{name:'Open navigation'}).click();
    await page.locator('nav[aria-label="Main navigation"] .nav-item').filter({hasText:'Countries'}).click();
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
    if(viewport.width<600){
      const mobile=page.getByRole('navigation',{name:'Mobile primary navigation'});
      assert.deepEqual(await mobile.locator('button span').allTextContents(),['Home','Countries','Risks','Systems','More']);
      await mobile.getByRole('button',{name:'Countries'}).click();
    }else{
      await page.locator('nav[aria-label="Main navigation"] .nav-item').filter({hasText:'Countries'}).click();
    }
    const countryViews=page.getByRole('group',{name:'Country intelligence views'});
    await countryViews.getByRole('button',{name:'Networks'}).click();
    const network=page.getByRole('region',{name:'Sourced relationship networks'});
    await network.waitFor({state:'visible',timeout:15000});
    await network.locator('.nx-graph').waitFor({state:'visible'});
    assert.ok(await network.locator('.nx-connection').count()>=2,'Global network spotlight should show sourced ties');
    assert.equal(await network.locator('.ip-sanction-source').count(),0,'Sanctions inventories must not replace Networks');
    assert.match(await network.locator('.nx-source').getAttribute('href'),/^https:\/\//,'Network evidence must link to original publisher');
    for(const countryName of ['Canada','Antigua & Barbuda']){
      await scope.click();
      await page.getByRole('combobox',{name:'Search country or code'}).fill(countryName);
      await page.getByRole('option',{name:countryName,exact:false}).click();
      if(countryName==='Canada'){
        await network.locator('.nx-connection').filter({hasText:'NATO'}).first().waitFor({state:'visible',timeout:15000});
      }else{
        await network.locator('.nx-empty').waitFor({state:'visible',timeout:15000});
      }
      assert.equal(await page.locator('#root').isVisible(),true,countryName+' blanked the React root');
    }
    await scope.click();
    await page.getByRole('combobox',{name:'Search country or code'}).fill('russ');
    await page.getByRole('option',{name:/Russia/}).click();
    assert.equal(await page.evaluate(()=>localStorage.getItem('ea.country.scope')),'RU');
    assert.match(await scope.innerText(),/Russia/);
    for(const target of ['Global systems','Supply chain','Countries']){
      if(viewport.width<600)await page.getByRole('button',{name:'Open navigation'}).click();
      await page.locator('nav[aria-label="Main navigation"] .nav-item').filter({hasText:target}).click();
      assert.match(await scope.innerText(),/Russia/,target+' lost selected scope');
      assert.equal(await page.locator('.ea-ops').count(),0,'Shared stats strip returned on '+target);
      if(target==='Countries'){
        await countryViews.getByRole('button',{name:'Networks'}).click();
        await network.locator('.nx-graph').waitFor({state:'visible',timeout:15000});
        assert.match(await scope.innerText(),/Russia/,'Networks nested in Countries lost scope');
      }
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
    await page.locator('nav[aria-label="Main navigation"] .nav-item').filter({hasText:'Countries'}).click();
    // Country dossier is selected explicitly after visiting the nested Networks view.
    await page.getByRole('group',{name:'Country intelligence views'}).getByRole('button',{name:'Country intelligence'}).click();
    await page.locator('.country-brief .brief-relationship').waitFor({state:'visible',timeout:15000});
    await page.locator('.ea-treaty-sources a[href="https://www.everycrsreport.com/reports/R49319.html"]').waitFor({state:'visible',timeout:15000});
    assert.equal(await page.getByText('No NATO / listed bilateral alliance').count(),0,'obsolete US-only relationship label persisted');
    if(viewport.width<600)await page.getByRole('button',{name:'Open navigation'}).click();
    await page.locator('nav[aria-label="Main navigation"] .nav-item').filter({hasText:'Risk watch'}).click();
    const scopedRisk=page.getByRole('region',{name:'Risk summary visual dashboard'});
    await scopedRisk.waitFor({state:'visible',timeout:15000});
    await scopedRisk.getByRole('heading',{name:'Risk signals, at a glance.'}).waitFor({state:'visible'});
    assert.equal(await scopedRisk.locator('.rdb-chart').count(),4,'Country Risks must remain charts-first');
    assert.equal(await page.locator('.rw-probes,.gs-signal').count(),0,'Country Risks should not show raw observations by default');
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
    const health=page.getByRole('region',{name:'Connected sources and collector freshness'});
    await health.waitFor({state:'visible'});
    assert.equal(await health.locator('.cs-feed').count(),4,'Source health must be kept on Coverage rather than Home');
    await health.getByRole('button',{name:'View collector records'}).click();
    await health.locator('.cs-details').waitFor({state:'visible'});
    await health.getByRole('button',{name:'Hide collector records'}).click();
    const assuranceDims=await page.evaluate(()=>({width:window.innerWidth,scroll:document.documentElement.scrollWidth}));
    assert.ok(assuranceDims.scroll<=assuranceDims.width+2,'Assurance panel overflow at '+viewport.width+'px: '+JSON.stringify(assuranceDims));
    // Navigation-wide release gate: inspect all 15 sections on every viewport,
    // retaining the active country selector and catching empty routes or overflow.
    const allSections=[
      'Command center','Countries','World Factbook','Global systems','Supply chain',
      'Early warning','Risk watch','AI analyst','Coverage audit',
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
      assert.equal(await page.locator('.ea-ops').count(),0,sectionName+' repeats global counters');
      assert.equal(await page.locator('.ea-module-context').count(),0,sectionName+' repeats generic context');
      assert.equal(await page.locator('.dr-root').count(),sectionName==='Command center'?1:0,sectionName+' displays Home-specific metrics on a specialist tab');
      if(sectionName==='Countries'){
        const countryViews=page.getByRole('group',{name:'Country intelligence views'});
        await countryViews.getByRole('button',{name:'Networks'}).click();
        const network=page.getByRole('region',{name:'Sourced relationship networks'});
        await network.waitFor({state:'visible'});
        assert.equal(await network.locator('.ip-sanction-source').count(),0,'Networks regressed to sanctions source inventory');
        await countryViews.getByRole('button',{name:'Country intelligence'}).click();
        await page.getByRole('heading',{name:/Country intelligence/i}).waitFor({state:'visible'});
      }
      if(sectionName==='AI analyst'){
        const analyst=page.locator('.ea-agent');
        await analyst.locator('.ea-agent-stats b').first().waitFor({state:'visible',timeout:15000});
        await page.waitForFunction(()=>Number(document.querySelector('.ea-agent-stats b')?.textContent||0)>0,{},{timeout:15000});
        assert.ok(Number(await analyst.locator('.ea-agent-stats b').first().innerText())>0,
          'Analyst must show real global source totals with a country selected');
        // A country with no tagged records retains WORLDWIDE evidence, never false country attribution.
        await scope.click();
        await page.getByRole('combobox',{name:'Search country or code'}).fill('United States');
        await page.getByRole('option',{name:/United States/}).click();
        await analyst.locator('.ea-agent-context').waitFor({state:'visible',timeout:15000});
        const nInferred=Number(await analyst.locator('.ea-agent-stats b').nth(3).innerText());
        if(nInferred>0){
          await analyst.getByRole('heading',{name:'Original-source evidence'}).waitFor({state:'visible'});
          await analyst.locator('.ea-agent-evidence-inferred').first().waitFor({state:'visible'});
          const labels=await analyst.locator('.ea-agent-evidence-inferred').allInnerTexts();
          assert.ok(labels.some(t=>t.includes('US (')),'US title matches must name the country and cited phrase');
        }else{
          await analyst.getByRole('heading',{name:'Worldwide source evidence (unassigned)'}).waitFor({state:'visible'});
          await analyst.locator('.ea-agent-section').filter({hasText:'Worldwide source evidence (unassigned)'})
            .locator('.ea-agent-records a').first().waitFor({state:'visible',timeout:15000});
        }
        // Restore the persistent China selection for the remaining navigation checks.
        await scope.click();
        await page.getByRole('combobox',{name:'Search country or code'}).fill('China');
        await page.getByRole('option',{name:/China/}).click();
        assert.match(await scope.innerText(),/China/);
      }
      if(sectionName==='Early warning'){
        const early=page.getByRole('region',{name:'Global physical and economic early-warning intelligence'});
        await early.getByRole('heading',{name:'Early warning signals.'}).waitFor({state:'visible'});
        assert.equal(await early.locator('.pew-domain-nav,.pew-indicators,.pew-nodes,.pew-source-health').count(),0,
          'Source-registry cards must not consume the Early Warning screen by default');
        assert.equal(await early.locator('.pew-summary>div').count(),4,'Missing four primary warning metrics');
        await early.getByRole('button',{name:'Review changes'}).click();
        await early.getByRole('button',{name:'All measurements'}).click();
        const gate=early.getByRole('button',{name:'View source data'});
        assert.equal(await gate.getAttribute('aria-expanded'),'false','Evidence is open by default');
        await gate.click();
        await early.locator('.pew-domain-nav').waitFor({state:'visible'});
        await early.locator('.pew-indicators article').first().waitFor({state:'visible'});
        await early.getByRole('button',{name:'Hide source data'}).click();
        assert.equal(await early.locator('.pew-indicators').count(),0,'Source data failed to collapse');
      }
      const mainText=await page.locator('.content').innerText();
      assert.ok(mainText.length>90,sectionName+' rendered an empty content panel');
      const layout=await page.evaluate(()=>({viewport:innerWidth,document:document.documentElement.scrollWidth}));
      if(layout.document>layout.viewport+2){
        const overflowing=await page.evaluate(()=>Array.from(document.querySelectorAll('main .content *'))
          .map(el=>({tag:el.tagName,className:typeof el.className==='string'?el.className.slice(0,90):'',text:(el.textContent||'').trim().slice(0,40),right:Math.round(el.getBoundingClientRect().right)}))
          .filter(el=>el.right>innerWidth+2).sort((a,b)=>b.right-a.right).slice(0,15));
        console.error('Overflow offenders',sectionName,viewport.width,JSON.stringify(overflowing));
      }
      assert.ok(layout.document<=layout.viewport+2,sectionName+' overflows '+viewport.width+'px: '+JSON.stringify(layout));
      if(viewport.width===390){
        const slug=sectionName.toLowerCase().replace(/[^a-z0-9]+/g,'-');
        await page.screenshot({path:'audit-output/eastern-axis-tab-'+slug+'-390.png'});
      }
      inspected.push(sectionName);
    }
    assert.equal(inspected.length,15,'Not every navigation section was inspected');
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
