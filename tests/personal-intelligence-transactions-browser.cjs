const {chromium,webkit}=require(process.env.PLAYWRIGHT_MODULE||"playwright");
const assert=require("node:assert/strict");
(async()=>{for(const type of [chromium,webkit]){const browser=await type.launch();try{
 const page=await browser.newPage({viewport:{width:390,height:844}}),errors=[],network=[];page.on("pageerror",e=>errors.push(String(e)));page.on("request",r=>network.push({url:r.url(),method:r.method(),body:r.postData()}));
 await page.goto("http://127.0.0.1:4175/personal-intelligence/#transactions");await page.locator("#transactions-screen").waitFor({state:"visible"});
 async function load(csv,opening,closing){
  await page.locator("#tx-account").fill("QA_PRIVATE_ACCOUNT");await page.locator("#tx-start").fill("2026-09-01");await page.locator("#tx-end").fill("2026-11-30");await page.locator("#tx-mode").selectOption("negative-out");await page.locator("#tx-opening").fill(opening);await page.locator("#tx-closing").fill(closing);
  await page.locator("#tx-file").setInputFiles({name:"QA_PRIVATE_STATEMENT.csv",mimeType:"text/csv",buffer:Buffer.from(csv)});
  await page.locator("#tx-extract").click();await page.locator("#tx-review .tx-row").first().waitFor({state:"visible"});
 }
 const csv="date,description,amount\n2026-09-01,Netflix,-15\n2026-10-01,Netflix,-15\n2026-11-01,Netflix,-15\n2026-11-02,Payroll,100\n2026-11-03,Transfer,-20\n2026-11-04,Refund,10";
 await load(csv,"0","45");
 assert.equal(await page.locator("#tx-commit").isDisabled(),true);assert.equal(await page.locator("#tx-review input:checked").count(),0);
 await page.locator("#tx-approve").click();assert.equal(await page.locator("#tx-commit").isDisabled(),true);
 for(const [row,cat] of [[4,"Income"],[5,"Transfer"],[6,"Refund"]]){
  const r=page.locator("#tx-review .tx-row").nth(row-1);if(await r.locator("select").first().inputValue()!==cat)await r.locator("select").first().selectOption(cat);await r.locator("input").check();
 }
 assert.match(await page.locator("#tx-review-status").innerText(),/matched/);
 await page.locator("#tx-commit").click();assert.match(await page.locator("#tx-summary").innerText(),/\$45.00/);assert.match(await page.locator("#tx-recurring").innerText(),/3 charges/);
 await load("date,description,amount\n2026-09-01,Netflix,-15","0","-15");
 assert.match(await page.locator("#tx-review").innerText(),/Possible duplicate/);assert.equal(await page.locator("#tx-approve").isDisabled(),true);
 await page.locator("#tx-review select").first().selectOption("Exclude");await page.getByLabel("Exclusion reason for row 2").selectOption("overlap");await page.locator("#tx-review input").check();
 assert.match(await page.locator("#tx-review-status").innerText(),/matched/);await page.locator("#tx-commit").click();
 assert.match(await page.locator("#tx-summary").innerText(),/\$45.00/);
 await page.locator("#transactions-screen a[href='#decisions']").click();await page.locator("#decisions").waitFor({state:"visible"});assert.match(await page.locator("#decisions-list").innerText(),/Reviewed transaction spending/);
 await page.locator("nav a[href='#profile']").click();await page.locator("#clear").click();assert.equal(await page.locator("#decisions-list article").count(),0);
 assert.equal(await page.evaluate(()=>localStorage.length+sessionStorage.length),0);assert.ok(network.every(r=>r.method==="GET"&&!r.body&&!/QA_PRIVATE_ACCOUNT|QA_PRIVATE_STATEMENT/.test(r.url)));
 assert.deepEqual(errors,[]);assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));console.log("PASS local transaction review and privacy "+type.name());
 }finally{await browser.close();}}})().catch(e=>{console.error(e);process.exit(1);});
