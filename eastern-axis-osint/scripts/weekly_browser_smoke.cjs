/* Eastern Axis weekly browser smoke: real read-only navigation and scope QA. */
const fs=require('node:fs');
const path=require('node:path');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const BASE=process.env.EASTERN_AXIS_URL||'https://eastern-axis-osint-unified.vercel.app';
const OUT=process.env.AUDIT_OUTPUT_DIR||'audit-output';
fs.mkdirSync(OUT,{recursive:true});
const SECTIONS=['Command center','Countries','World Factbook','Global systems',
  'Supply chain','Risk watch','Coverage audit','Connections','Defense intelligence',
  'Investigations','Collection desk','Verification lab','Source library','Methodology'];
const checks=[];
const note=(name,status,detail)=>checks.push({name,status,detail});
async function run(){
  let browser;
  try {
    browser=await chromium.launch({channel:'chrome',headless:true,args:['--no-sandbox']});
    for(const [name,width,height] of [['desktop',1440,900],['mobile',390,844]]){
      const context=await browser.newContext({viewport:{width,height},deviceScaleFactor:1});
      const page=await context.newPage();
      const errors=[];
      page.on('pageerror',e=>errors.push(String(e).slice(0,200)));
      try{
        const response=await page.goto(BASE,{waitUntil:'domcontentloaded',timeout:45000});
        if(!response||response.status()!==200)throw Error('Home page HTTP '+response?.status());
        const scope=page.locator('#ea-country-scope');
        await scope.waitFor({state:'visible',timeout:30000});
        await page.waitForFunction(()=>document.querySelector('#ea-country-scope')?.options.length>2,null,{timeout:30000});
        note(name+' initial load','PASS','Source catalog and country selector populated');
        for(const section of SECTIONS){
          if(name==='mobile'){
            const open=page.getByRole('button',{name:'Open navigation'});
            if(await open.isVisible())await open.click();
          }
          const button=page.locator('nav[aria-label="Main navigation"] button.nav-item').filter({hasText:section}).first();
          try{await button.click({timeout:12000});}
          catch(error){throw Error('Cannot open '+section+' on '+name+': '+String(error).slice(0,160));}
          const active=await page.locator('nav[aria-label="Main navigation"] button.nav-item.active').innerText();
          if(!active.toLowerCase().includes(section.toLowerCase()))
            throw Error('Section '+section+' failed to activate; active='+active);
        }
        note(name+' sections','PASS',SECTIONS.length+' navigation sections activated');
        if(name==='desktop'){
          await scope.selectOption('RU');
          await page.locator('nav[aria-label="Main navigation"] button.nav-item').filter({hasText:'Command center'}).click();
          const label=page.locator('.cc-country-detail h2');
          await label.waitFor({state:'visible',timeout:15000});
          if(!/russia/i.test(await label.textContent()||''))throw Error('RU country context absent');
          await scope.selectOption('all');
          await page.waitForTimeout(450);
          if(await page.locator('.cc-country-detail').count()>0)
            throw Error('Country context failed to reset on Global');
          note('Russia to Global scope','PASS','Country detail cleared when switching to Global');
        }
        const dimensions=await page.evaluate(()=>({page:document.documentElement.scrollWidth,width:window.innerWidth}));
        if(dimensions.page>dimensions.width+2)throw Error('Horizontal overflow '+JSON.stringify(dimensions));
        note(name+' responsive','PASS','No horizontal overflow');
        note(name+' uncaught JS errors',errors.length?'WARN':'PASS',
          errors.length?errors.slice(0,4).join('; '):'None');
      }catch(error){
        note(name+' functional smoke','FAIL',String(error).slice(0,250));
        try{await page.screenshot({path:path.join(OUT,name+'-failure.png')});}catch(_){}
      }finally{await context.close();}
    }
  }catch(error){note('Browser setup','FAIL',String(error).slice(0,250))}
  finally{if(browser)await browser.close();}
  fs.writeFileSync(path.join(OUT,'browser.json'),JSON.stringify(checks,null,2)+'\n');
  const lines=['# Eastern Axis weekly browser smoke','',...checks.map(x=>'- **'+x.status+'** '+x.name+': '+x.detail)];
  fs.writeFileSync(path.join(OUT,'browser.md'),lines.join('\n')+'\n');
  if(process.env.GITHUB_STEP_SUMMARY)fs.appendFileSync(process.env.GITHUB_STEP_SUMMARY,'\n'+lines.join('\n')+'\n');
  for(const x of checks)console.log(x.status,x.name,x.detail);
  if(checks.some(x=>x.status==='FAIL'))process.exitCode=1;
}
run().catch(error=>{console.error(error);process.exitCode=1});
