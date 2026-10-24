// Optional browser tooling: use an existing Playwright installation, not a new app dependency.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '../..');
const fixture = require(path.join(root, 'contracts/fixtures/run_output.fixture.json'));
const base = process.env.TRADEPULSE_PREVIEW_URL || 'http://127.0.0.1:5180';
const out = path.resolve(process.env.TRADEPULSE_QA_DIR || path.join(root, 'web/.qa-output/redesign'));
fs.mkdirSync(out, { recursive: true });

(async () => {
  const browser = await chromium.launch({
    ...(process.env.TRADEPULSE_CHROMIUM ? { executablePath: process.env.TRADEPULSE_CHROMIUM } : {}),
    headless: true, args: ['--no-sandbox'],
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  page.setDefaultTimeout(12000);
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  page.on('console', (message) => { if (['error', 'warning'].includes(message.type())) errors.push(message.text()); });
  const results = [];
  async function check(name, action) {
    try { await action(); results.push({ name, status: 'PASS' }); console.log('PASS', name); }
    catch (error) { results.push({ name, status: 'FAIL', error: error.message }); console.log('FAIL', name, error.message); await page.screenshot({ path: path.join(out, `failure-${results.length}.png`) }); }
  }
  async function goto(route, title) {
    await page.goto(base + route);
    await page.getByRole('heading', { name: title, exact: true }).first().waitFor();
    await page.waitForTimeout(70);
  }
  async function mode(name) {
    const button = page.getByRole('button', { name: `${name} View`, exact: true });
    await button.click();
    await page.waitForFunction((label) => [...document.querySelectorAll('[aria-pressed]')].some((node) => node.textContent === label && node.getAttribute('aria-pressed') === 'true'), `${name} View`);
  }
  async function tabTo(locator, limit = 100) {
    for (let step = 0; step < limit; step += 1) {
      if (await locator.evaluate((element) => element === document.activeElement)) return;
      await page.keyboard.press('Tab');
    }
    throw new Error('Keyboard target was not reached within the bounded tab sequence');
  }
  const abstained = fixture.explanations.find((item) => item.verdict === 'abstained');
  const sample = fixture.recommendations.find((item) => item.pool === abstained.pool && item.symbol === abstained.symbol);

  await check('fresh Simple default, original redirect and honest Discover', async () => {
    await goto('/', 'US equities');
    assert(new URL(page.url()).pathname === '/pool/us_equity');
    assert.equal(await page.getByRole('button', { name: 'Simple View', exact: true }).getAttribute('aria-pressed'), 'true');
    assert.equal(await page.locator('.candidate-card').count(), 50);
    await goto('/discover', 'Make sense of the market.');
    assert.equal(await page.locator('input,textarea').count(), 0);
    assert.equal(await page.locator('.discovery-candidates .candidate-card').count(), fixture.pools.length);
    assert((await page.locator('.agent-capability').innerText()).includes('does not generate a new model answer'));
    assert.equal(await page.locator('html').getAttribute('lang'), 'en');
  });
  await check('working guided research and actual abstention evidence', async () => {
    await page.getByRole('link', { name: 'Examine an abstained explanation', exact: false }).click();
    await page.getByRole('heading', { name: abstained.symbol, exact: true }).waitFor();
    await page.waitForFunction(() => document.activeElement.id === 'explanation');
    await page.locator('.claim.rejected summary').first().click();
    assert(await page.locator('.claim.rejected[open]').count());
    for (const claim of abstained.claims) assert((await page.locator('#explanation').innerText()).includes(claim.text));
    assert((await page.locator('#explanation').innerText()).includes(abstained.counter_case[0]));
  });
  await check('same-instrument metric, source, rejected evidence and risk parity', async () => {
    await goto(`/ticker/${sample.pool}/${sample.symbol}`, sample.symbol);
    const readings = [];
    for (const presentation of ['Simple', 'Pro']) {
      await mode(presentation);
      assert.equal(await page.evaluate(() => document.activeElement.textContent), `${presentation} View`);
      if (presentation === 'Simple') await page.getByText('All original instrument metrics', { exact: true }).click();
      const metrics = await page.locator('#measurements .metrics').innerText();
      readings.push({ metrics, context: await page.locator('.detail-context').innerText(), claims: await page.locator('.claims').innerText(), risks: await page.locator('#risks').innerText() });
      assert((await page.locator('footer').innerText()).includes(fixture.disclaimer));
    }
    assert.deepEqual(readings[0], readings[1]);
    assert(readings[0].context.includes(sample.tier));
    assert(readings[0].risks.includes(sample.invalidation[0]));
  });
  await check('preference persistence and keyboard switch without focus loss', async () => {
    const button = page.getByRole('button', { name: 'Simple View', exact: true });
    await button.focus();
    await page.keyboard.press('Space');
    assert.equal(await button.getAttribute('aria-pressed'), 'true');
    assert.equal(await page.evaluate(() => document.activeElement.textContent), 'Simple View');
    assert.equal(await page.evaluate(() => localStorage.getItem('tradepulse.view')), 'simple');
    await page.reload();
    await page.getByRole('heading', { name: sample.symbol, exact: true }).waitFor();
    assert.equal(await button.getAttribute('aria-pressed'), 'true');
  });
  await check('filter, sector, tier and sort survive view changes', async () => {
    await goto('/pool/us_equity', 'US equities');
    const row = fixture.recommendations.find((item) => item.pool === 'us_equity' && item.tier === 'OVERWEIGHT');
    await page.getByRole('searchbox').fill(row.symbol);
    await page.getByLabel('Sector', { exact: true }).selectOption(row.sector);
    await page.getByLabel('Overweight', { exact: true }).check();
    await page.getByLabel('Sort candidates', { exact: true }).selectOption('score:desc');
    const url = page.url();
    await mode('Pro');
    assert.equal(page.url(), url);
    assert.equal(await page.locator('.leaderboard tbody tr').count(), 1);
    assert((await page.locator('.leaderboard tbody').innerText()).includes(row.symbol));
    await mode('Simple');
    assert.equal(page.url(), url);
    assert.equal(await page.locator('.candidate-card').count(), 1);
    assert.equal(await page.getByRole('searchbox').inputValue(), row.symbol);
    assert.equal(await page.getByLabel('Sector', { exact: true }).inputValue(), row.sector);
    assert.equal(await page.getByLabel('Overweight', { exact: true }).isChecked(), true);
  });
  await check('pagination and market context survive detail and browser Back', async () => {
    await goto('/pool/us_equity?sort=rank&dir=asc&page=2', 'US equities');
    await mode('Pro');
    const before = page.url();
    const selected = await page.locator('.leaderboard tbody tr').first().locator('a').innerText();
    await page.locator('.leaderboard tbody tr').first().locator('a').click();
    await page.getByRole('heading', { name: selected.split('\n')[0], exact: true }).waitFor();
    await page.getByRole('link', { name: 'Back to US equities', exact: false }).click();
    assert.equal(page.url(), before);
    await page.locator('.leaderboard tbody tr').first().waitFor();
    assert((await page.locator('.pagination').innerText()).includes('51–100'));
    await mode('Simple');
    assert.equal(page.url(), before);
    assert.equal(await page.locator('.candidate-card').count(), 50);
    await page.locator('.candidate-card h3 a').first().click();
    await page.getByRole('heading', { name: selected.split('\n')[0], exact: true }).waitFor();
    await page.goBack();
    await page.getByRole('heading', { name: 'US equities', exact: true }).waitFor();
    assert.equal(page.url(), before);
  });
  await check('blocked storage still supports both views and navigation', async () => {
    const context = await browser.newContext();
    await context.addInitScript(() => Object.defineProperty(window, 'localStorage', { get() { throw new Error('Storage disabled'); } }));
    const blocked = await context.newPage();
    const issues = [];
    blocked.on('pageerror', (error) => issues.push(error.message));
    await blocked.goto(base + '/discover');
    await blocked.getByRole('heading', { name: 'Make sense of the market.', exact: true }).waitFor();
    await blocked.getByRole('button', { name: 'Pro View', exact: true }).click();
    await blocked.getByRole('link', { name: 'Factor Lab', exact: true }).click();
    await blocked.getByRole('heading', { name: 'Factor Lab', exact: true }).waitFor();
    assert.equal(await blocked.getByRole('button', { name: 'Pro View', exact: true }).getAttribute('aria-pressed'), 'true');
    assert.deepEqual(issues, []);
    await context.close();
  });
  await check('every chart family has keyboard-operable numerical equivalents', async () => {
    await goto('/pool/us_equity', 'US equities'); await mode('Pro');
    await page.getByText('Sector values and keyboard filters', { exact: true }).focus(); await page.keyboard.press('Enter');
    const sectorRegion = page.getByRole('region', { name: 'Sector summary and accessible filters', exact: true });
    await sectorRegion.waitFor(); assert(await sectorRegion.locator('tbody tr').count() > 0);
    await goto(`/ticker/${sample.pool}/${sample.symbol}`, sample.symbol);
    await page.getByText('View contribution measurements', { exact: true }).click();
    assert.equal(await page.getByRole('region', { name: 'Underlying contribution values', exact: true }).locator('tbody tr').count(), sample.contributions.length);
    await goto('/factors', 'Factor Lab');
    assert.equal(await page.locator('.factor-card').first().getByRole('region').locator('tbody tr').count(), fixture.factor_cards[0].ic_decay.length);
    await goto('/regime', 'Market Regime');
    await page.getByText('Recorded regime history values', { exact: true }).first().click();
    const history = page.getByRole('region', { name: `${fixture.regimes[0].pool} historical fragility observations`, exact: true });
    await history.waitFor(); assert.equal(await history.locator('tbody tr').count(), fixture.regimes[0].history.length);
    await goto('/track-record', 'Track Record');
    await page.getByText('Calibration values and sample sizes', { exact: true }).click();
    const calibration = page.getByRole('region', { name: 'Original calibration measurements', exact: true });
    await calibration.waitFor(); assert.equal(await calibration.locator('tbody tr').count(), fixture.track_record.calibration.length);
    await page.getByText(`Composite IC values for ${fixture.pools[0].label}`, { exact: true }).click();
    const ic = page.getByRole('region', { name: `${fixture.pools[0].label} composite IC observations`, exact: true });
    await ic.waitFor(); assert.equal(await ic.locator('tbody tr').count(), fixture.track_record.composite_ic_series.filter((item) => item.pool === fixture.pools[0].pool).length);
    await goto('/trace', 'Run Trace');
    await page.getByText('Paired timing measurements', { exact: true }).click();
    assert(await page.getByRole('region', { name: 'Exact paired node timing', exact: true }).locator('tbody tr').count() > 0);
  });
  await check('Simple trace describes only actual node pairs and preserves retries', async () => {
    await goto('/trace', 'Run Trace'); await mode('Simple');
    await page.getByRole('heading', { name: 'Recorded research workflow', exact: true }).waitFor();
    const trace = fs.readFileSync(path.join(root, 'contracts/fixtures/trace.fixture.jsonl'), 'utf8').split('\n').filter(Boolean).map(JSON.parse);
    const pairs = trace.filter((item) => item.kind === 'node_end').length;
    assert.equal(await page.locator('.simple-trace-list li').count(), pairs);
    await page.getByText('Inspect full event chronology and filters', { exact: true }).click();
    await page.getByLabel('Event kind', { exact: true }).selectOption('retry');
    await mode('Pro');
    assert.equal(await page.getByLabel('Event kind', { exact: true }).inputValue(), 'retry');
    assert.equal(await page.locator('.event-table tbody tr').count(), trace.filter((item) => item.kind === 'retry').length);
    assert((await page.locator('main').innerText()).includes('Timing discrepancy:'));
  });
  await check('no-call and insufficient data remain limitations', async () => {
    const noCall = fixture.recommendations.find((row) => row.tier === 'NO_CALL');
    if (noCall) { await goto(`/ticker/${noCall.pool}/${noCall.symbol}`, noCall.symbol); await mode('Simple'); assert((await page.locator('main').innerText()).includes('No specific reason code is supplied')); }
    await goto('/factors?pool=eu_equity&status=INSUFFICIENT_DATA', 'Factor Lab');
    assert.equal(await page.locator('.factor-card').count(), fixture.factor_cards.filter((item) => item.pool === 'eu_equity' && item.status === 'INSUFFICIENT_DATA').length);
  });
  await check('keyboard-only Discover, evidence, glossary, mobile menu and Escape', async () => {
    await page.setViewportSize({ width: 390, height: 1000 });
    await goto('/discover', 'Make sense of the market.');
    await page.keyboard.press('Tab');
    const skip = page.getByRole('link', { name: 'Skip to main content', exact: true });
    await tabTo(skip, 100);
    assert((await skip.boundingBox()).y >= 0);
    await page.keyboard.press('Enter');
    assert.equal(await page.evaluate(() => document.activeElement.id), 'main-content');
    const guide = page.getByText('Research guide · Understand the terms', { exact: true });
    await tabTo(guide); await page.keyboard.press('Enter');
    await page.getByRole('heading', { name: 'Coverage is not confidence', exact: true }).waitFor();
    await page.keyboard.press('Enter');
    const journey = page.getByRole('link', { name: 'Examine an abstained explanation', exact: false });
    await tabTo(journey); await page.keyboard.press('Enter');
    await page.getByRole('heading', { name: sample.symbol, exact: true }).waitFor();
    await page.waitForFunction(() => document.activeElement.id === 'explanation');
    const rejected = page.locator('.claim.rejected summary').first();
    await tabTo(rejected); await page.keyboard.press('Enter');
    assert(await page.locator('.claim.rejected[open]').count());
    const menu = page.getByRole('button', { name: 'Menu', exact: true });
    await tabTo(menu); await page.keyboard.press('Enter');
    assert.equal(await page.getByRole('button', { name: 'Close menu', exact: true }).getAttribute('aria-expanded'), 'true');
    await page.keyboard.press('Tab'); await page.keyboard.press('Escape');
    assert.equal(await menu.getAttribute('aria-expanded'), 'false');
    assert(await menu.evaluate((element) => element === document.activeElement));
  });

  const routes = [
    ['discover', '/discover', 'Make sense of the market.'], ['leaderboard', '/pool/us_equity', 'US equities'],
    ['detail', `/ticker/${sample.pool}/${sample.symbol}`, sample.symbol], ['factors', '/factors', 'Factor Lab'],
    ['regime', '/regime', 'Market Regime'], ['track-record', '/track-record', 'Track Record'], ['trace', '/trace', 'Run Trace'],
  ];
  for (const width of [1440, 768, 390, 320]) {
    await check(`both-view reflow, provenance and screenshots at ${width} CSS pixels`, async () => {
      await page.setViewportSize({ width, height: 1000 });
      for (const presentation of ['Simple', 'Pro']) {
        await mode(presentation);
        for (const [name, route, title] of routes) {
          await goto(route, title);
          if (name === 'trace') await page.getByRole('heading', { name: 'Pipeline timeline', exact: true }).waitFor();
          await page.waitForTimeout(100);
          const dimensions = await page.evaluate(() => ({ width: innerWidth, body: document.body.scrollWidth, root: document.documentElement.scrollWidth }));
          assert(dimensions.body <= width && dimensions.root <= width, `${name} ${presentation}: ${JSON.stringify(dimensions)}`);
          assert((await page.locator('.mode-banner.warning').innerText()).includes('SYNTHETIC FIXTURE'));
          assert((await page.locator('footer').innerText()).includes(fixture.disclaimer));
          if (width !== 320) await page.screenshot({ path: path.join(out, `${name}-${presentation.toLowerCase()}-${width}.png`) });
        }
      }
    });
  }
  await check('200% text enlargement at narrow viewport, plus 400% equivalent reflow', async () => {
    await page.setViewportSize({ width: 390, height: 1000 });
    for (const presentation of ['Simple', 'Pro']) {
      await mode(presentation);
      for (const [name, route, title] of routes) {
        await goto(route, title);
        await page.addStyleTag({ content: ':root { font-size: 200% !important; }' });
        assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${name}/${presentation} overflows at 200% text`);
      }
    }
    // A 1280px browser at 400% zoom presents an equivalent 320 CSS pixel layout.
    await page.setViewportSize({ width: 320, height: 900 });
    await goto('/discover', 'Make sense of the market.');
    await page.screenshot({ path: path.join(out, 'reflow-320.png') });
  });
  await check('reduced motion and semantic accessibility names', async () => {
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await goto('/discover', 'Make sense of the market.');
    assert(await page.evaluate(() => matchMedia('(prefers-reduced-motion: reduce)').matches));
    const moving = await page.evaluate(() => [...document.querySelectorAll('*')].filter((element) => {
      const style = getComputedStyle(element); return style.animationName !== 'none' && style.animationDuration !== '0s';
    }).length);
    assert.equal(moving, 0);
    assert.equal(await page.getByRole('group', { name: 'Research presentation', exact: true }).count(), 1);
    const snapshot = await page.locator('main').ariaSnapshot();
    fs.writeFileSync(path.join(out, 'discover-aria.yml'), snapshot);
    assert(snapshot.includes('Make sense of the market.'));
    assert(snapshot.includes('Examine an abstained explanation'));
  });
  await check('no console errors or warnings in the new research journeys', async () => assert.deepEqual(errors, []));
  fs.writeFileSync(path.join(out, 'results.json'), JSON.stringify({ results, errors }, null, 2));
  await browser.close();
  console.log(`${results.filter((item) => item.status === 'PASS').length}/${results.length} groups passed`);
  process.exitCode = results.some((item) => item.status === 'FAIL') ? 1 : 0;
})().catch((error) => { console.error(error); process.exit(1); });
