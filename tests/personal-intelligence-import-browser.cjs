const {chromium,webkit}=require(process.env.PLAYWRIGHT_MODULE||"playwright");
const assert=require("node:assert/strict");
// Public synthetic QA fixture only. No user document goes into test artifacts or GitHub.
function pdfFixture(){
 const stream="BT /F1 12 Tf 50 740 Td (Amount due: $123.45) Tj 0 -24 Td (Due date: 12/05/2026) Tj ET";
 const objects=["<< /Type /Catalog /Pages 2 0 R >>","<< /Type /Pages /Kids [3 0 R] /Count 1 >>","<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>","<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>","<< /Length "+Buffer.byteLength(stream)+" >>\nstream\n"+stream+"\nendstream"];
 let body="%PDF-1.4\n",offsets=[0];objects.forEach((obj,i)=>{offsets.push(Buffer.byteLength(body));body+=(i+1)+" 0 obj\n"+obj+"\nendobj\n";});const xref=Buffer.byteLength(body);body+="xref\n0 6\n0000000000 65535 f \n"+offsets.slice(1).map(x=>String(x).padStart(10,"0")+" 00000 n \n").join("")+"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n"+xref+"\n%%EOF\n";return Buffer.from(body);
}
(async()=>{for(const type of [chromium,webkit]){const browser=await type.launch();try{
 const page=await browser.newPage({viewport:{width:390,height:844}}),errors=[],network=[];page.on("pageerror",e=>errors.push(String(e)));page.on("request",r=>network.push({url:r.url(),method:r.method(),body:r.postData()}));
 await page.goto("http://127.0.0.1:4175/personal-intelligence/#imports");
 await page.locator("#imports-screen").waitFor({state:"visible"});
 await page.locator("#import-text").fill("Monthly household take-home income: $4321\nTotal monthly household expenses: $3100\nAmount due: $98.15\nAccount: QA_PRIVATE_SENTINEL");
 await page.locator("#import-extract").click();await page.locator("#import-review input").first().waitFor();
 assert.equal(await page.locator("#import-review input:checked").count(),0);assert.equal(await page.locator("#import-confirm").isDisabled(),true);
 assert.equal(await page.locator("#net").inputValue(),"");await page.locator("#import-review input").nth(0).check();await page.locator("#import-review input").nth(1).check();await page.locator("#import-review input").nth(2).check();
 await page.locator("#import-confirm").click();assert.equal(await page.locator("#net").inputValue(),"4321");assert.equal(await page.locator("#expenses").inputValue(),"3100");assert.equal(await page.locator("#import-text").inputValue(),"");assert.match(await page.locator("#import-records").innerText(),/\$98.15/);
 await page.locator("#import-file").setInputFiles({name:"test-bill.pdf",mimeType:"application/pdf",buffer:pdfFixture()});await page.locator("#import-extract").click();await page.waitForFunction(()=>document.querySelectorAll("#import-review input").length>=2,{},{timeout:45000});assert.match(await page.locator("#import-review").innerText(),/\$123.45/);assert.equal(await page.locator("#import-review input:checked").count(),0);
 await page.locator("#import-review input").first().check();await page.locator("#import-confirm").click();assert.equal(await page.locator("#expenses").inputValue(),"3100");
 await page.locator("#imports-screen a[href='#decisions']").click();await page.locator("#decisions").waitFor({state:"visible"});assert.match(await page.locator("#decisions-list").innerText(),/\$1,221 per month/);assert.match(await page.locator("#decisions-list").innerText(),/\$123.45/);
 await page.locator("nav a[href='#profile']").click();await page.locator("#clear").click();assert.equal(await page.locator("#net").inputValue(),"");assert.equal(await page.locator("#decisions-list article").count(),0);
 assert.equal(await page.evaluate(()=>localStorage.length+sessionStorage.length),0);
 assert.ok(network.every(r=>r.method==="GET"&&!r.body&&!/QA_PRIVATE_SENTINEL|test-bill\.pdf|4321/.test(r.url)));assert.deepEqual(errors,[]);assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 console.log("PASS local document import and privacy "+type.name());
 }finally{await browser.close();}}})().catch(e=>{console.error(e);process.exit(1);});