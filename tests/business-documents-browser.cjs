const {chromium,webkit}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
(async()=>{for(const type of [chromium,webkit]){const b=await type.launch({headless:true});try{for(const width of [320,390,1280]){
 const page=await b.newPage({viewport:{width,height:900}}),requests=[],errors=[];
 page.on('request',r=>requests.push(r.url()+' '+(r.postData()||'')));page.on('pageerror',e=>errors.push(String(e)));
 await page.goto(process.env.BUSINESS_TEST_URL||'http://127.0.0.1:4175/business-intelligence/');
 await page.locator('nav a[href="#profile"]').click();await page.locator('#business-type').selectOption('importer');
 await page.getByLabel('Business document',{exact:true}).setInputFiles({name:'isolated-fixture.txt',mimeType:'text/plain',buffer:Buffer.from('Supplier: QA_PRIVATE_DOC_6357\nCountry: US\nTotal: 12345')});
 await page.getByRole('button',{name:'Approve as new dependency'}).waitFor();
 await page.getByLabel('Confirmed product group').selectOption('fuel');
 await page.getByRole('button',{name:'Approve as new dependency'}).click();
 assert.equal(await page.locator('[data-field=name]').inputValue(),'QA_PRIVATE_DOC_6357');
 assert.equal(await page.locator('[data-field=monthlyCost]').inputValue(),'');
 await page.locator('#apply').click();assert.equal(await page.locator('#dep-count').innerText(),'1');
 assert.ok(requests.every(x=>!x.includes('QA_PRIVATE_DOC_6357')&&!x.includes('isolated-fixture')));
 assert.deepEqual(errors,[]);assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 await page.close();console.log('Document approval and network inspection passed in '+type.name()+' at '+width);
 }}finally{await b.close();}}})().catch(e=>{console.error(e);process.exit(1)});
