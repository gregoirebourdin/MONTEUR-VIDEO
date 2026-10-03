(async()=>{
const { chromium } = require('playwright');
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
await p.goto('https://www.manysetter.com', { waitUntil: 'networkidle' });
await p.waitForTimeout(2500);
await p.screenshot({ path: 'site-hero.png' });
await p.screenshot({ path: 'site-full.png', fullPage: true });
for (const u of ['pricing','how-it-works']) {
  try { await p.goto('https://www.manysetter.com/'+u, { waitUntil: 'networkidle' }); await p.waitForTimeout(1500);
  await p.screenshot({ path: `site-${u}.png`, fullPage: true });
  const t = await p.evaluate(()=>document.body.innerText); require('fs').writeFileSync(`${u}.txt`, t);
  } catch(e) { console.log(u, e.message) }
}
await b.close();
})();
