// Optional Playwright tooling: capture the delivered API without intercepting responses.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const base = process.env.TRADEPULSE_PREVIEW_URL || 'http://127.0.0.1:18131';
const api = process.env.TRADEPULSE_API_URL || `${base}/api`;
const out = path.resolve('docs/submission/assets');
const sha = (bytes) => crypto.createHash('sha256').update(bytes).digest('hex');

(async () => {
  const response = await fetch(`${api}/runs/latest`, { signal: AbortSignal.timeout(15000) });
  assert(response.ok);
  const source = await response.text(), run = JSON.parse(source);
  assert.notEqual(run.data_mode, 'SYNTHETIC');
  const record = run.explanations[0] || run.recommendations[0];
  const routes = [
    ['leaderboard', `/pool/${record.pool}`, '.table-card'],
    ['ticker', `/ticker/${record.pool}/${encodeURIComponent(record.symbol)}`, '#explanation'],
    ['factors', '/factors', '.factor-card'],
    ['trace', '/trace', '.trace-event-disclosure'],
  ];
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch({ headless: true, timeout: 15000,
    ...(process.env.TRADEPULSE_CHROMIUM ? { executablePath: process.env.TRADEPULSE_CHROMIUM } : {}),
  });
  try {
    const viewport = { width: 1440, height: 900 };
    const page = await browser.newPage({ viewport, reducedMotion: 'reduce' });
    page.setDefaultTimeout(20000);
    const images = [];
    for (const [name, route, focus] of routes) {
      await page.goto(base + route);
      await page.locator('h1').first().waitFor();
      await page.getByRole('button', { name: 'Pro View', exact: true }).click();
      assert((await page.locator('.run-info').innerText()).includes(run.run_id));
      assert(!(await page.locator('.mode-banner').innerText()).includes('with recorded model answers'));
      await page.evaluate(() => document.fonts.ready);
      const target = page.locator(focus).first();
      await target.waitFor();
      await target.evaluate((element) => element.scrollIntoView({ block: 'start', behavior: 'instant' }));
      const file = `${name}-real-api.png`;
      const bytes = await page.screenshot({ path: path.join(out, file) });
      images.push({ file, route, view: 'Pro', focus, viewport, sha256: sha(bytes) });
    }
    fs.writeFileSync(path.join(out, 'manifest.json'), JSON.stringify({
      captured_at: new Date().toISOString(), browser: browser.version(),
      run_id: run.run_id, as_of: run.as_of, data_mode: run.data_mode,
      api_payload_sha256: sha(source),
      capture: 'Actual local container API-backed UI; no interception. Reduced motion enabled.',
      model_acceptance: 'Model recording absent; actual explanations abstain. Images do not prove successful hosted models.',
      images,
    }, null, 2) + '\n');
    console.log(`Captured ${images.length} real API screenshots`);
  } finally { await browser.close(); }
})().catch((error) => { console.error(error.name); process.exitCode = 1; });
