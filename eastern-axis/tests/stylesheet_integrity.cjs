const {chromium,webkit,devices}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const origin=(process.env.EA_BROWSER_ORIGIN||'http://127.0.0.1:4174').replace(/\/$/,'');
const release=process.env.GITHUB_SHA;
(async()=>{
 fs.mkdirSync('audit-output',{recursive:true});
 for(const [name,engine,options] of [
   ['iphone-webkit',webkit,{...devices['iPhone 13']}],
   ['desktop-chromium',chromium,{viewport:{width:1440,height:900}}]
 ]){
   const browser=await engine.launch({headless:true});
   try{
     const context=await browser.newContext(options);
     // Simulate a missing fingerprinted CSS file and unavailable external fonts.
     await context.route('**/*',route=>route.request().resourceType()==='stylesheet'?route.abort():route.continue());
     const page=await context.newPage();
     const errors=[];
     page.on('pageerror',e=>errors.push(e.message));
     for(const tab of ['Situation room','Forecast intelligence','Forecast track record']){
       const query=new URLSearchParams({ea_domain:'command',ea_tab:tab,ea_country:'all',ea_pane:'workspace',release:release||'qa'});
       const response=await page.goto(origin+'/?'+query,{waitUntil:'domcontentloaded',timeout:30000});
       assert.equal(response.status(),200);
       await page.locator('.ea-control-room').waitFor({state:'visible',timeout:20000});
       const style=await page.evaluate(()=>{
         const shell=document.querySelector('.ea-control-room'),nav=document.querySelector('.ea-mobile-primary');
         const root=getComputedStyle(document.documentElement),body=getComputedStyle(document.body),s=getComputedStyle(shell);
         return {inline:!!document.querySelector('style[data-ea-dashboard-css="inline"]'),
           release:document.querySelector('meta[name="ea-release"]')?.content,
           margin:body.margin,display:s.display,background:s.backgroundColor,rootBackground:root.backgroundColor,font:root.fontFamily,
           mobileNav:nav?getComputedStyle(nav).display:null,width:innerWidth,scroll:document.documentElement.scrollWidth};
       });
       assert.ok(style.inline,'Missing embedded dashboard CSS '+JSON.stringify(style));
       if(release)assert.equal(style.release,release,'Unexpected deployed revision');
       assert.equal(style.margin,'0px','Browser default margins: stylesheet missing');
       assert.ok(['flex','grid'].includes(style.display),'Browser default shell layout '+JSON.stringify(style));
       assert.notEqual(style.rootBackground,'rgba(0, 0, 0, 0)','Unstyled page background');
       assert.ok(!/Times New Roman/i.test(style.font),'Unstyled browser serif typography');
       if(name==='iphone-webkit')assert.ok(style.mobileNav&&style.mobileNav!=='none','Mobile navigation CSS missing');
       assert.ok(style.scroll<=style.width+2,'Horizontal overflow '+JSON.stringify(style));
       if(tab==='Forecast intelligence')await page.locator('.fc-root .fc-target').first().waitFor({state:'visible',timeout:15000});
       if(tab==='Forecast track record')await page.locator('.fc-calibration').waitFor({state:'visible',timeout:15000});
       await page.screenshot({path:'audit-output/style-'+name+'-'+tab.toLowerCase().replaceAll(' ','-')+'.png'});
       console.log('STYLE QA',name,tab,JSON.stringify(style));
     }
     assert.deepEqual(errors,[],'Uncaught browser exceptions');
   } finally {await browser.close();}
 }
})().catch(error=>{console.error(error);process.exitCode=1;});
