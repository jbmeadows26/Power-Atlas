import {test,expect} from '@playwright/test';
test('filters persist, exports download, evidence is searchable, no runtime errors',async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://localhost:5173/?section=Tribalism&chamber=Senate&year=2022');
 await expect(page.getByRole('combobox')).toHaveValue('Senate');
 await page.getByRole('combobox').selectOption('House');await page.reload();await expect(page.getByRole('combobox')).toHaveValue('House');
 const download=page.waitForEvent('download');await page.getByRole('button',{name:'CSV ↓',exact:true}).click();expect((await download).suggestedFilename()).toBe('power-atlas.csv');
 await page.locator('#evidence input').fill('Rucho');await expect(page.locator('#evidence tbody')).toContainText('Rucho');
 await page.locator('#search').fill('nonexistent-zzzz');await expect(page.locator('.results')).toContainText('No matching');
 await page.getByRole('button',{name:'Gerrymandering',exact:true}).click();await page.getByRole('combobox').selectOption('2010');await expect(page).toHaveURL(/year=2010/);await expect(page.locator('.recharts-scatter-symbol').first()).toBeVisible();
 await page.getByRole('button',{name:'Voting Access',exact:true}).click();await expect(page.locator('.recharts-bar-rectangle').first()).toBeVisible();expect(errors).toEqual([]);
});
test('failed feed has visible error state',async({page})=>{await page.route('**/data/voting.json',r=>r.fulfill({status:503,body:'Unavailable'}));await page.goto('http://localhost:5173');await expect(page.getByRole('heading',{name:'Data temporarily unavailable'})).toBeVisible();});
test('keyboard skip link reaches content',async({page})=>{await page.goto('http://localhost:5173');await expect(page.locator('h1')).toBeVisible();await page.keyboard.press('Tab');await expect(page.getByRole('link',{name:'Skip to data'})).toBeFocused();await page.keyboard.press('Enter');await expect(page).toHaveURL(/#main$/);});
