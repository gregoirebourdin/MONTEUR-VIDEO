const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await (await b.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
  await p.goto('https://www.manysetter.com/login', { waitUntil: 'networkidle' });
  await p.waitForTimeout(1500);
  console.log('URL', p.url());
  await p.screenshot({ path: 'login.png' });
  await b.close();
})();
