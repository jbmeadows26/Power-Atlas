const {chromium, request: createRequest} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const api = fs.readFileSync('eastern-axis/public-api-origin.txt','utf8').trim().replace(/\/$/,'');
const origin = process.env.EA_BROWSER_ORIGIN || 'http://127.0.0.1:4173';
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
    await connect(page);
    await page.goto(origin+'/',{waitUntil:'domcontentloaded',timeout:30000});
    const scope = page.getByRole('button',{name:'Choose country intelligence scope'});
    await scope.waitFor({state:'visible',timeout:20000});
    await scope.click();
    await page.getByRole('combobox',{name:'Search country or code'}).fill('russ');
    await page.getByRole('option',{name:/Russia/}).click();
    assert.equal(await page.evaluate(()=>localStorage.getItem('ea.country.scope')),'RU');
    assert.match(await scope.innerText(),/Russia/);
    for(const target of ['Global systems','Supply chain','Connections']){
      if(viewport.width<600)await page.getByRole('button',{name:'Open navigation'}).click();
      await page.locator('nav[aria-label="Main navigation"] .nav-item').filter({hasText:target}).click();
      assert.match(await scope.innerText(),/Russia/,target+' lost selected scope');
    }
    await page.reload({waitUntil:'domcontentloaded'});
    const afterReload = page.getByRole('button',{name:'Choose country intelligence scope'});
    await afterReload.waitFor({state:'visible',timeout:20000});
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
    assert.equal(await page.getByText('No NATO / listed bilateral alliance').count(),0,'obsolete US-only relationship label persisted');
    await page.screenshot({path:'audit-output/eastern-axis-'+viewport.width+'.png',fullPage:true});
    console.log('Browser QA passed',viewport.width,'country picker search, treaty facts, persistence, three tabs');
    await context.close();
  }
  await browser.close();
  await req.dispose();
  if(errors.length){console.error('Uncaught browser exceptions',errors);process.exitCode=1;}
})().catch(e=>{console.error(e);process.exit(1)});
