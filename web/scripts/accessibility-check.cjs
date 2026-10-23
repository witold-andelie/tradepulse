// A focused Chromium check, not a WCAG conformance audit or a screen-reader test.
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '../..');
const fixture = require(path.join(root, 'contracts/fixtures/run_output.fixture.json'));
const base = process.env.TRADEPULSE_PREVIEW_URL || 'http://127.0.0.1:5180';
const out = path.resolve(process.env.TRADEPULSE_QA_DIR || path.join(root, 'web/.qa-output/accessibility'));
fs.mkdirSync(out, { recursive: true });
(async () => {
  const browser = await chromium.launch({ ...(process.env.TRADEPULSE_CHROMIUM ? { executablePath: process.env.TRADEPULSE_CHROMIUM } : {}), headless: true, args: ['--no-sandbox'] });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const row = fixture.recommendations[0];
  const routes = ['/discover', '/pool/us_equity', `/ticker/${row.pool}/${row.symbol}`, '/factors', '/regime', '/track-record', '/trace'];
  const results = [];
  for (const view of ['simple', 'pro']) {
    await page.addInitScript((value) => { try { localStorage.setItem('tradepulse.view', value); } catch {} }, view);
    for (const route of routes) {
      await page.goto(base + route); await page.locator('h1').waitFor();
      await page.getByRole('button', { name: view === 'pro' ? 'Pro View' : 'Simple View', exact: true }).click();
      if (route === '/trace') await page.getByRole('heading', { name: 'Pipeline timeline', exact: true }).waitFor();
      const result = await page.evaluate(() => {
        const rgb = (value) => { const values = value.match(/[\d.]+/g)?.map(Number); return values?.length >= 3 ? [...values.slice(0, 3), values[3] ?? 1] : [255, 255, 255, 1]; };
        const blend = (front, back) => front.slice(0, 3).map((value, index) => value * front[3] + back[index] * (1 - front[3]));
        const background = (element) => {
          const chain = []; for (let node = element; node; node = node.parentElement) chain.unshift(node);
          return chain.reduce((back, node) => blend(rgb(getComputedStyle(node).backgroundColor), back), [255, 255, 255]);
        };
        const luminance = (color) => color.map((value) => value / 255).map((value) => value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4).reduce((sum, value, index) => sum + value * [.2126, .7152, .0722][index], 0);
        const contrast = (a, b) => (Math.max(luminance(a), luminance(b)) + .05) / (Math.min(luminance(a), luminance(b)) + .05);
        const visible = (element) => { const rect = element.getBoundingClientRect(); const style = getComputedStyle(element); return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && Number(style.opacity) > 0 && !element.closest('[aria-hidden=true]'); };
        const failures = []; let inspected = 0; let minimum = 99;
        for (const element of document.querySelectorAll('a,button,p,span,dt,dd,th,td,label,summary,h1,h2,h3,h4,small,strong,legend')) {
          if (!visible(element) || element.closest(':disabled') || ![...element.childNodes].some((node) => node.nodeType === Node.TEXT_NODE && node.textContent.trim())) continue;
          const style = getComputedStyle(element); const bg = background(element); const ratio = contrast(blend(rgb(style.color), bg), bg);
          const large = parseFloat(style.fontSize) >= 24 || (parseFloat(style.fontSize) >= 18.666 && parseInt(style.fontWeight, 10) >= 700);
          inspected += 1; minimum = Math.min(minimum, ratio);
          if (ratio + .005 < (large ? 3 : 4.5)) failures.push({ text: element.textContent.slice(0, 85), ratio: Number(ratio.toFixed(2)), color: style.color, background: bg, size: style.fontSize });
        }
        const targets = [];
        for (const element of document.querySelectorAll('button,a,summary,input,select')) {
          if (!visible(element) || element.matches(':disabled')) continue;
          const target = element.matches('input[type=checkbox]') ? element.closest('label') || element : element;
          const rect = target.getBoundingClientRect();
          if (rect.width < 24 || rect.height < 24) targets.push({ text: element.textContent?.slice(0, 50) || element.getAttribute('aria-label') || element.tagName, width: rect.width, height: rect.height });
        }
        const unnamed = [...document.querySelectorAll('input,select,button')].filter((element) => visible(element) && !element.getAttribute('aria-label') && !element.labels?.length && !element.textContent.trim()).map((element) => element.outerHTML.slice(0, 100));
        const firstControl = document.querySelector('input[type=search], select, .view-switch');
        const border = firstControl ? contrast(rgb(getComputedStyle(firstControl).borderTopColor).slice(0, 3), background(firstControl)) : null;
        return { inspected, minimum: Number(minimum.toFixed(2)), failures, targetsBelow24: targets, unnamed, controlBorderContrast: border && Number(border.toFixed(2)) };
      });
      results.push({ view, route, ...result });
      console.log(view, route, `text=${result.inspected}, contrast failures=${result.failures.length}, small targets=${result.targetsBelow24.length}, unnamed=${result.unnamed.length}`);
    }
  }
  fs.writeFileSync(path.join(out, 'contrast-targets.json'), JSON.stringify(results, null, 2));
  await browser.close();
  process.exitCode = results.some((result) => result.failures.length || result.unnamed.length || result.targetsBelow24.length) ? 1 : 0;
})().catch((error) => { console.error(error); process.exit(1); });
