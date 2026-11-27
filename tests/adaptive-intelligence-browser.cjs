const {chromium,webkit}=require(process.env.PLAYWRIGHT_MODULE||"playwright");
const assert=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path");
const root=path.resolve(__dirname,".."),base=process.env.ADAPTIVE_ORIGIN||"http://127.0.0.1:4175";
(async()=>{for(const type of [chromium,webkit]){const browser=await type.launch();try{
 const ctx=await browser.newContext({viewport:{width:390,height:844}}),page=await ctx.newPage(),requests=[],errors=[];
 page.on("request",r=>requests.push({url:r.url(),method:r.method(),body:r.postData()}));page.on("pageerror",e=>errors.push(String(e)));
 await page.route("https://raw.githubusercontent.com/jbmeadows26/Power-Atlas/main/**",async route=>{const rel=route.request().url().split("/main/")[1],file=path.resolve(root,rel);if(!file.startsWith(root+path.sep)||!fs.existsSync(file))return route.abort();await route.fulfill({contentType:"application/json",headers:{"access-control-allow-origin":"*"},body:fs.readFileSync(file)});});
 await page.goto(base+"/business-intelligence/#profile");await page.waitForFunction(()=>document.querySelector("#feed-count").textContent==="8 / 8");
 const ai=page.locator("#adaptive-intelligence"),enable=ai.getByRole("button",{name:/Enable local AI/});
 await enable.waitFor({state:"visible"});await page.waitForFunction(()=>!document.querySelector("#adaptive-intelligence button").disabled,{},{timeout:20000});
 assert.ok(!requests.some(x=>/adaptive-assets\/(?:vendor|models)\//.test(x.url)));
 // Declined permission must not cause model downloads.
 page.once("dialog",d=>d.dismiss());await enable.click();assert.ok(!requests.some(x=>/adaptive-assets\/(?:vendor|models)\//.test(x.url)));
 await page.locator("#business-type").selectOption("importer");await page.locator("#add").click();await page.locator("[data-field=name]").fill("QA_PRIVATE_ADAPTIVE_DEP");await page.locator("[data-field=product]").selectOption("fuel");await page.locator("#apply").click();
 await page.locator("nav a[href='#profile']").click();await page.locator("#adaptive-query").fill("fuel");
 await ai.getByRole("button",{name:"Find relevant intelligence"}).click();assert.match(await ai.innerText(),/Standard keyword search/);assert.match(await ai.innerText(),/Transport fuels/);
 page.once("dialog",d=>d.accept());await enable.click();await page.waitForFunction(()=>document.querySelector("#adaptive-intelligence").textContent.includes("Local AI ready"),{},{timeout:180000});
 assert.ok(requests.some(x=>x.url.includes("model_quantized.onnx")));
 // Existing model must run with the network disabled, including a private query.
 await ctx.setOffline(true);
 await page.locator("#adaptive-query").fill("QA_PRIVATE_ADAPTIVE_QUERY energy transportation fuel");await ai.getByRole("button",{name:"Find relevant intelligence"}).click();
 await page.waitForFunction(()=>document.querySelector("#adaptive-intelligence").textContent.includes("On-device semantic relevance"),{},{timeout:90000});
 assert.match(await ai.innerText(),/Local AI completed/);assert.match(await ai.innerText(),/Transport fuels/);
 await ctx.setOffline(false);await page.locator("#clear").click();assert.equal(await page.locator("#adaptive-query").inputValue(),"");assert.match(await ai.innerText(),/Local model stopped/);
 assert.ok(requests.every(x=>x.method==="GET"&&!x.body&&!/QA_PRIVATE_ADAPTIVE/.test(x.url)));assert.deepEqual(errors,[]);
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.close();
 const pi=await ctx.newPage();await pi.goto(base+"/personal-intelligence/#profile");
 await pi.locator("#adaptive-intelligence").waitFor({state:"visible"});assert.match(await pi.locator("#adaptive-intelligence").innerText(),/Private Intelligence Engine/);
 await pi.locator("#adaptive-query").fill("energy");await pi.locator("#clear").click();assert.equal(await pi.locator("#adaptive-query").inputValue(),"");
 await pi.close();await ctx.close();console.log("PASS actual local model, consent, offline inference and shared UI",type.name());
 }finally{await browser.close();}}})().catch(e=>{console.error(e);process.exit(1);});
