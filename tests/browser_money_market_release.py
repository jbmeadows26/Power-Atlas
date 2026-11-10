"""Headless desktop/mobile acceptance check against unpublished Power Atlas preview deployments."""
import asyncio
import os
from playwright.async_api import async_playwright

ORIGINS = {
    "research": os.environ.get("POWER_ATLAS_RESEARCH_PREVIEW", "https://power-atlas-research-j3t1midj5-jbmeadows26s-projects.vercel.app"),
    "unified": os.environ.get("POWER_ATLAS_UNIFIED_PREVIEW", "https://power-atlas-unified-q0fweki5w-jbmeadows26s-projects.vercel.app"),
}

async def check(browser, label, origin, width):
    page = await browser.new_page(viewport={"width":width, "height":812 if width==375 else 900}, device_scale_factor=1, has_touch=width==375)
    page.set_default_timeout(24000)
    r = await page.goto(origin + "/", wait_until="domcontentloaded", timeout=30000)
    assert r and r.status == 200, (label, "home",r.status if r else None)
    await page.locator(".pa4-home").wait_for()
    tiles=page.locator(".pa4-tile")
    assert await tiles.count()==9, (label, "story cards",await tiles.count())
    hrefs=await tiles.locator("a").evaluate_all("(nodes)=>nodes.map(x=>x.getAttribute('href'))")
    if not hrefs: hrefs=await tiles.evaluate_all("(nodes)=>nodes.map(x=>x.getAttribute('href'))")
    assert any(h and "money-scale.html" in h for h in hrefs), (label,"missing money tile",hrefs)
    assert any(h and "market-power.html" in h for h in hrefs), (label,"missing market tile",hrefs)

    r=await page.goto(origin + "/money-scale.html",wait_until="domcontentloaded",timeout=30000)
    assert r and r.status==200, (label,"money page",r.status if r else None)
    await page.locator("#scale .bar-row").first.wait_for()
    await page.locator('button[data-group="annual-output"]').click()
    await page.wait_for_function("document.querySelectorAll('#scale .bar-row').length===2")
    text=await page.locator("#scale").inner_text()
    assert "World economic output (GDP)" in text, (label,text)
    assert "U.S. economic output (GDP)" in text, (label,text)
    await page.locator('button[data-group="liability-stock"]').click()
    debt=await page.locator("#scale").inner_text()
    assert "Global debt" in debt, (label,debt)
    await page.locator("#scale .bar-row").first.click()
    info=await page.locator("#detail").inner_text()
    assert "Original source" in info, (label,info)
    assert await page.locator('meta[name="robots"][content*="noindex"]').count()==0
    assert await page.evaluate("document.documentElement.scrollWidth <= innerWidth + 3"),(label,"money overflow",width)

    r=await page.goto(origin + "/market-power.html",wait_until="domcontentloaded",timeout=30000)
    assert r and r.status==200, (label,"market page",r.status if r else None)
    await page.locator('#hbBars button[data-category="groceries"]').wait_for()
    assert await page.locator("#hbBars button").count()==4,(label,"household cards")
    await page.locator('#hbBars button[data-category="groceries"]').click()
    out=await page.locator("#hbDetail").inner_text()
    assert "Meatpacking & ranchers" in out,(label,out)
    await page.locator('#hbBars button[data-category="health"]').click()
    health=await page.locator("#hbDetail").inner_text()
    assert "Prescription drug middlemen" in health,(label,health)
    assert "Local hospital systems" in health,(label,health)
    assert await page.locator("#caseMenu button").count()>=12,(label,"cases missing")
    await page.locator('#filters button[data-topic="Health"]').click()
    assert await page.locator("#caseMenu button").count()>=2,(label,"filter dead")
    assert await page.evaluate("document.documentElement.scrollWidth <= innerWidth + 3"),(label,"market overflow",width)
    assert await page.locator('meta[name="robots"][content*="noindex"]').count()==0
    print(f"PASS {label} {width}px: home navigation, data-backed tabs, linked cases, filter, no overflow")
    await page.close()

async def main():
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,args=["--no-sandbox"])
        try:
            for label,origin in ORIGINS.items():
                for width in (375,1280):
                    await check(browser,label,origin,width)
        finally:
            await browser.close()

if __name__=="__main__":
    asyncio.run(main())
