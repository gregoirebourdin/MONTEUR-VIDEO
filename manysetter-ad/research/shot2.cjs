const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
  const p = await ctx.newPage();
  for (const [name, url] of [['home','https://www.manysetter.com'],['how','https://www.manysetter.com/how-it-works'],['pricing','https://www.manysetter.com/pricing']]) {
    await p.goto(url, { waitUntil: 'networkidle' });
    // dismiss cookie banner
    try { await p.getByRole('button', { name: 'Decline' }).click({ timeout: 2000 }); } catch {}
    const H = await p.evaluate(() => document.documentElement.scrollHeight);
    let i = 0;
    for (let y = 0; y < H; y += 700) {
      await p.evaluate(yy => window.scrollTo(0, yy), y);
      await p.waitForTimeout(1600);
      await p.screenshot({ path: `${name}-${String(i++).padStart(2,'0')}.png` });
    }
    await p.evaluate(() => window.scrollTo(0, 0)); await p.waitForTimeout(800);
    await p.screenshot({ path: `${name}-full.png`, fullPage: true });
    console.log(name, H, i);
  }
  await b.close();
})();
