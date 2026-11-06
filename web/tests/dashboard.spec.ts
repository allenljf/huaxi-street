import { test, expect } from '@playwright/test';
import { fixture } from './fixtures/markets';

test.beforeEach(async ({page})=>{
 await page.clock.setFixedTime(new Date('2026-11-06T08:15:00+08:00'));
 await page.route('**/data/markets.json',route=>route.fulfill({json:fixture}));
 await page.goto('/');
});

test('score directions, unavailable data and leveraged risk are visible',async({page})=>{
 const taiwan=page.getByTestId('market-taiex');
 await expect(taiwan).toContainText('7.6');
 await expect(taiwan).toContainText('陪葬訊號集結，分批入席');
 await expect(page.getByTestId('market-0050')).toContainText('躲噴警報，檢查減碼節奏');
 const unavailable=page.getByTestId('market-sp500');
 await expect(unavailable).toContainText('暫不評分');
 await expect(unavailable).not.toContainText('0.0');
 await expect(page.getByTestId('market-00631L')).toContainText('每日槓桿重設');
});

test('filters display the selected markets',async({page})=>{
 await page.getByRole('button',{name:'美股',exact:true}).click();
 await expect(page.getByTestId('market-sp500')).toBeVisible();
 await expect(page.getByTestId('market-taiex')).toHaveCount(0);
});

test('dialog has tabs, traps focus and restores original trigger',async({page})=>{
 const trigger=page.getByTestId('market-taiex').getByRole('button',{name:'看陪葬攻略'});
 await trigger.click();
 const dialog=page.getByRole('dialog');
 await expect(dialog).toHaveAccessibleName('台灣加權・陪葬攻略');
 await page.getByRole('tab',{name:'訊號'}).click();
 await expect(dialog).toContainText('RSI 32.00');
 for(let i=0;i<15;i++) await page.keyboard.press('Tab');
 expect(await dialog.evaluate(el=>el.contains(document.activeElement))).toBeTruthy();
 await page.keyboard.press('Escape');
 await expect(dialog).not.toBeVisible();
 await expect(trigger).toBeFocused();
});

test('mobile text zoom does not overflow and dialog can close',async({page})=>{
 await page.setViewportSize({width:320,height:720});
 await page.addStyleTag({content:'html { font-size: 200%; }'});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
 await page.getByTestId('market-taiex').getByRole('button',{name:'看陪葬攻略'}).click();
 await page.getByRole('button',{name:'關閉視窗'}).click();
 await expect(page.getByRole('dialog')).not.toBeVisible();
});

test('no backdrop support and reduced motion preserve content',async({page})=>{
 await page.emulateMedia({reducedMotion:'reduce'});
 await page.addStyleTag({content:'* { backdrop-filter: none !important; -webkit-backdrop-filter: none !important; }'});
 await page.getByRole('button',{name:'這分數怎麼來的？'}).click();
 await expect(page.getByRole('dialog')).toContainText('分數不是獲利機率');
 await page.getByRole('button',{name:'關閉視窗'}).click();
 await expect(page.getByRole('heading',{name:'陪葬! 華西街',exact:true})).toBeVisible();
});

test('pending confirmation, conflicts and stale scores never imply a confirmed action',async({page})=>{
 const altered=structuredClone(fixture);
 altered.markets[0].confirmed=false;
 altered.markets[1].buyScore=8;
 await page.route('**/data/markets.json',route=>route.fulfill({json:altered}));
 await page.reload();
 await expect(page.getByTestId('market-taiex')).toContainText('訊號待確認');
 await expect(page.getByTestId('market-0050')).toContainText('陪葬、躲噴各有說法');
 await expect(page.getByTestId('market-00631L')).toContainText('暫不評分');
});

test('failed data request gives a visible retry action',async({page})=>{
 await page.route('**/data/markets.json',route=>route.fulfill({status:503,body:'offline'}));
 await page.reload();
 await expect(page.getByRole('alert')).toContainText('暫時讀不到市場筆記');
 await expect(page.getByRole('button',{name:'重新讀取'})).toBeVisible();
});


test('expired generated snapshot cannot keep actionable scores',async({page})=>{
 await page.clock.setFixedTime(new Date('2026-11-09T08:15:00+08:00'));
 await page.reload();
 const card=page.getByTestId('market-taiex');
 await expect(card).toContainText('網站快照已超過36小時');
 await expect(card).not.toContainText('7.6');
 await expect(card).toContainText('暫不評分');
});

test('malformed numbers fail visibly instead of showing invalid financial data',async({page})=>{
 const broken=structuredClone(fixture) as any;broken.markets[0].buyScore=99;
 await page.route('**/data/markets.json',route=>route.fulfill({json:broken}));
 await page.reload();
 await expect(page.getByRole('alert')).toContainText('暫時讀不到市場筆記');
});
