// Browser-only transport simulations against the existing schema boundary, never a live service.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '../..');
const fixture = require(path.join(root, 'contracts/fixtures/run_output.fixture.json'));
const trace = fs.readFileSync(path.join(root, 'contracts/fixtures/trace.fixture.jsonl'), 'utf8').trim().split('\n').map(JSON.parse);
const base = process.env.TRADEPULSE_PREVIEW_URL || 'http://127.0.0.1:5195';
const api = process.env.TRADEPULSE_TEST_API || 'http://127.0.0.1:5196';
const out = process.env.TRADEPULSE_QA_DIR || '/tmp/tradepulse-global-api';
const locales = ['en', 'zh-CN', 'zh-TW', 'es', 'fr', 'de', 'pt-BR', 'ja', 'ko', 'cs', 'ar'];
const dict = (locale) => require(path.join(root, 'web/src/i18n', locale === 'en' ? 'en.json' : `locales/${locale}.json`));
fs.mkdirSync(out, { recursive: true });
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.TRADEPULSE_CHROMIUM || '/usr/bin/chromium', headless: true, args: ['--no-sandbox'] });
  const results = [];
  async function check(name, action) { try { await action(); results.push({ name, status: 'PASS' }); console.log('PASS', name); } catch (error) { results.push({ name, status: 'FAIL', error: error.stack }); console.log('FAIL', name, error.message); } }
  async function select(page, locale) { await page.locator('#app-language').selectOption(locale); await page.waitForFunction((value) => document.documentElement.lang === value, locale); }
  async function simulation(output = fixture, status = 200, delay = false, traceOutput = trace) {
    const context = await browser.newContext(); const requests = []; let release;
    const waiting = new Promise((resolve) => { release = resolve; });
    await context.route(`${api}/**`, async (route) => {
      const request = route.request(); requests.push({ method: request.method(), url: request.url() });
      if (delay && request.url().endsWith('/runs/latest')) await waiting;
      await route.fulfill({ status, contentType: 'application/json', headers: { 'Access-Control-Allow-Origin': '*' }, body: JSON.stringify(request.url().endsWith('/trace') ? traceOutput : output) });
    });
    const page = await context.newPage(); page.setDefaultTimeout(10000);
    return { context, page, requests, release };
  }
  await check('loading remains localized and mounted; all locale changes preserve one validated run request', async () => {
    const { context, page, requests, release } = await simulation(fixture, 200, true);
    await page.goto(base + '/discover'); await page.locator('#app-language').waitFor();
    for (const locale of locales) { await select(page, locale); assert((await page.locator('main').innerText()).includes(dict(locale)['Loading research data…'])); }
    assert.equal(requests.length, 1); release(); await page.getByRole('heading', { name: dict('ar')['Make sense of the market.'], exact: true }).waitFor();
    await page.setViewportSize({ width: 1440, height: 1000 }); await page.locator('.navigation a[href="/trace"]').click();
    await page.getByRole('heading', { name: dict('ar')['Pipeline timeline'], exact: true }).waitFor();
    await page.locator('.trace-event-disclosure > summary').click();
    await page.getByLabel(dict('ar')['Event kind'], { exact: true }).selectOption('retry');
    for (const locale of locales) { await select(page, locale); assert.equal(await page.getByLabel(dict(locale)['Event kind'], { exact: true }).inputValue(), 'retry'); }
    assert.equal(requests.filter((request) => request.url.endsWith('/runs/latest')).length, 1);
    assert.equal(requests.filter((request) => request.url.endsWith('/trace')).length, 1);
    assert.equal(requests.filter((request) => request.method !== 'GET').length, 0);
    fs.writeFileSync(path.join(out, 'request-counts.json'), JSON.stringify(requests, null, 2)); await context.close();
  });
  for (const scenario of [{ name: 'HTTP 503', output: {}, status: 503 }, { name: 'invalid contract', output: { unknown: true }, status: 200 }]) {
    await check(`${scenario.name}: eleven localized error states; no fixture substitution`, async () => {
      const { context, page, requests } = await simulation(scenario.output, scenario.status);
      await page.goto(base + '/discover'); await page.getByRole('alert').waitFor();
      for (const locale of locales) {
        await select(page, locale); assert((await page.getByRole('alert').innerText()).includes(dict(locale)['Research data is unavailable']));
        assert.equal(await page.getByRole('button', { name: dict(locale).Retry, exact: true }).count(), 1);
        assert.equal(await page.locator('.candidate-card').count(), 0);
      }
      assert.equal(requests.length, 1); assert.equal(await page.locator('.mode-banner.warning').count(), 0);
      await page.screenshot({ path: path.join(out, `${scenario.status}-ar-error.png`) }); await context.close();
    });
  }
  await check('schema-valid empty collections: localized leaderboard, factors, regime and trace', async () => {
    const empty = { ...fixture, recommendations: [], explanations: [], factor_cards: [], regimes: [] };
    const { context, page } = await simulation(empty, 200, false, []);
    for (const [route, title] of [['/pool/us_equity', 'No instruments match your filters'], ['/factors', 'No factor cards match this selection'], ['/regime', 'Regime data unavailable'], ['/trace', 'No trace events recorded']]) {
      await page.goto(base + route); await page.locator('#app-language').waitFor(); await select(page, 'fr');
      await page.getByRole('heading', { name: dict('fr')[title] || title, exact: true }).first().waitFor();
    }
    await context.close();
  });
  await check('lazy-route failure retains the global language selector and localized recovery', async () => {
    const { context, page } = await simulation();
    await context.route('**/assets/FactorLabPage-*.js', (route) => route.abort());
    await page.goto(base + '/factors'); await page.getByRole('heading', { name: 'This page could not be displayed', level: 1, exact: true }).waitFor();
    await select(page, 'ja'); await page.getByRole('heading', { name: dict('ja')['This page could not be displayed'], level: 1, exact: true }).waitFor();
    assert.equal(await page.locator('#app-language').count(), 1); await context.close();
  });
  fs.writeFileSync(path.join(out, 'results.json'), JSON.stringify(results, null, 2)); await browser.close();
  console.log(`${results.filter((result) => result.status === 'PASS').length}/${results.length} groups passed`); process.exitCode = results.some((result) => result.status === 'FAIL') ? 1 : 0;
})().catch((error) => { console.error(error); process.exit(1); });
