// Optional browser tooling; run against the real local API, with no fixture interception.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const base = process.env.TRADEPULSE_PREVIEW_URL || 'http://127.0.0.1:5198';
const api = process.env.TRADEPULSE_API_URL || 'http://127.0.0.1:8000';
const out = process.env.TRADEPULSE_QA_DIR || path.resolve('web/.qa-output/real-api');

(async () => {
  const response = await fetch(`${api}/runs/latest`, { signal: AbortSignal.timeout(15000) });
  assert(response.ok, `API returned HTTP ${response.status}`);
  const body = await response.text();
  const run = JSON.parse(body);
  assert.notEqual(run.data_mode, 'SYNTHETIC', 'This suite requires a real-data run');
  assert(run.pools.length && run.recommendations.length, 'The real run must contain instruments');
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch({
    ...(process.env.TRADEPULSE_CHROMIUM ? { executablePath: process.env.TRADEPULSE_CHROMIUM } : {}),
    headless: true, timeout: 15000,
  });
  const page = await browser.newPage();
  page.setDefaultTimeout(20000);
  const errors = [], fixtureRequests = [], results = [];
  page.on('pageerror', (error) => errors.push(error.message));
  page.on('console', (message) => { if (['warning', 'error'].includes(message.type())) errors.push(message.text()); });
  page.on('request', (request) => { if (/\/assets\/[^/]+\.fixture-/.test(request.url())) fixtureRequests.push(request.url()); });
  async function check(name, operation) {
    try { await operation(); results.push({ name, status: 'PASS' }); console.log('PASS', name); }
    catch (error) { results.push({ name, status: 'FAIL', error: error.message }); console.log('FAIL', name, error.message); }
  }
  async function goto(route) {
    await page.goto(base + route);
    await page.locator('h1').first().waitFor();
    assert.equal(await page.getByRole('heading', { name: 'This page could not be displayed' }).count(), 0);
    const context = await page.locator('.run-info').innerText();
    assert(context.includes(run.run_id) && context.includes(run.data_mode));
    if (run.data_mode === 'REPLAY') {
      const banner = await page.locator('.mode-banner strong').innerText();
      assert(banner.startsWith('REPLAY') && banner.includes('model availability'));
      assert(!banner.includes('with recorded model answers'));
    }
    assert((await page.locator('footer').innerText()).includes(run.disclaimer));
  }
  const explanation = run.explanations[0];
  const detail = explanation || run.recommendations[0];
  const routes = [
    ...run.pools.map((pool) => [`pool-${pool.pool}`, `/pool/${pool.pool}`]),
    ['detail', `/ticker/${detail.pool}/${encodeURIComponent(detail.symbol)}`],
    ['discover', '/discover'], ['factors', '/factors'], ['regime', '/regime'],
    ['track-record', '/track-record'], ['trace', '/trace'],
  ];
  for (const width of [1440, 320]) for (const view of ['Simple', 'Pro']) {
    await check(`real API routes, disclosures and reflow: ${view} at ${width}px`, async () => {
      await page.setViewportSize({ width, height: 1000 });
      for (const [name, route] of routes) {
        await goto(route);
        await page.getByRole('button', { name: `${view} View`, exact: true }).click();
        if (name.startsWith('pool-')) {
          const pool = name.slice(5), count = run.recommendations.filter((row) => row.pool === pool).length;
          assert.equal(await page.locator('.result-count').innerText(), `${count.toLocaleString('en-US')} of ${count.toLocaleString('en-US')} instruments`);
        }
        if (name === 'detail' && explanation?.verdict === 'abstained') {
          await page.locator('#agent-research-guide > details').nth(3).locator('summary').click();
          assert((await page.locator('#agent-research-guide').innerText()).includes(explanation.summary));
        }
        if (name === 'trace') {
          const log = page.locator('.trace-event-disclosure');
          if (await log.getAttribute('open') === null) await log.locator(':scope > summary').click();
          await page.getByRole('heading', { name: 'Event log', exact: true }).waitFor();
        }
        assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${name}: page overflow`);
        await page.screenshot({ path: path.join(out, `${name}-${view.toLowerCase()}-${width}.png`), fullPage: true });
      }
    });
  }
  await check('real instruments support combined filters and keyboard detail navigation', async () => {
    const row = run.recommendations[0];
    await page.setViewportSize({ width: 1440, height: 1000 });
    await goto(`/pool/${row.pool}`);
    await page.getByRole('button', { name: 'Pro View', exact: true }).click();
    await page.getByRole('searchbox').fill(row.name);
    await page.getByLabel('Sector', { exact: true }).selectOption(row.sector);
    const expected = run.recommendations.filter((item) => item.pool === row.pool && item.sector === row.sector
      && `${item.symbol} ${item.name} ${item.sector}`.toLowerCase().includes(row.name.toLowerCase())).length;
    await page.waitForFunction((count) => document.querySelectorAll('tbody tr').length === count, Math.min(expected, 50));
    const first = page.locator('tbody tr').first();
    await first.focus(); await page.keyboard.press('Enter');
    await page.getByRole('heading', { level: 1, name: row.symbol, exact: true }).waitFor();
  });
  await check('all real factor cards preserve insufficient-data and zero-active states', async () => {
    await goto('/factors');
    for (const pool of run.pools) {
      await page.getByLabel('Asset pool', { exact: true }).selectOption(pool.pool);
      for (const status of ['', 'ACTIVE', 'INSUFFICIENT_DATA']) {
        await page.getByLabel('Factor status', { exact: true }).selectOption(status);
        const cards = run.factor_cards.filter((card) => card.pool === pool.pool && (!status || card.status === status));
        await page.waitForFunction((count) => document.querySelectorAll('.factor-card').length === count, cards.length);
        assert.equal(await page.locator('.gate-chip').count(), cards.reduce((sum, card) => sum + card.gates.length, 0));
      }
    }
  });
  await check('actual trace events support node and kind filters together', async () => {
    const traceResponse = await fetch(`${api}/runs/${encodeURIComponent(run.run_id)}/trace`, { signal: AbortSignal.timeout(15000) });
    assert(traceResponse.ok);
    const events = await traceResponse.json();
    assert(events.length);
    const selected = events.find((event) => event.kind === 'error') || events[0];
    await goto('/trace');
    const log = page.locator('.trace-event-disclosure');
    if (await log.getAttribute('open') === null) await log.locator(':scope > summary').click();
    await page.getByLabel('Pipeline node', { exact: true }).selectOption(selected.node);
    await page.getByLabel('Event kind', { exact: true }).selectOption(selected.kind);
    const expected = events.filter((event) => event.node === selected.node && event.kind === selected.kind).length;
    await page.waitForFunction((count) => document.querySelectorAll('.event-table tbody tr').length === count, expected);
    assert.equal(await page.locator('.result-count').innerText(), `${expected.toLocaleString('en-US')} of ${events.length.toLocaleString('en-US')} events`);
  });
  await check('normal real API journeys have no console errors or fixture requests', async () => {
    assert.deepEqual(errors, []); assert.deepEqual(fixtureRequests, []);
  });
  const normalMessages = errors.slice();
  await check('API failures are visible and never fall back to synthetic fixtures', async () => {
    await page.route(`${api}/runs/latest`, (route) => route.fulfill({ status: 503,
      headers: { 'access-control-allow-origin': new URL(base).origin }, contentType: 'application/json', body: '{}' }));
    await page.goto(base + '/pool/us_equity');
    await page.getByRole('alert').waitFor();
    assert((await page.getByRole('alert').innerText()).includes('503'));
    await page.unroute(`${api}/runs/latest`);
    assert.deepEqual(fixtureRequests, []);
  });
  // The deliberate 503 is allowed to produce its browser network error; normal journeys are recorded separately.
  const report = { run_id: run.run_id, as_of: run.as_of, data_mode: run.data_mode,
    source_sha256: crypto.createHash('sha256').update(body).digest('hex'), browser: browser.version(),
    results, fixtureRequests, normal_console_errors: normalMessages,
    expected_failure_messages: errors.slice(normalMessages.length),
    models: 'Uses the actual saved run, including its unavailable-model abstentions; does not certify NIM or hosted sponsors.' };
  fs.writeFileSync(path.join(out, 'results.json'), JSON.stringify(report, null, 2));
  await browser.close();
  if (results.some((item) => item.status !== 'PASS')) process.exitCode = 1;
})().catch((error) => { console.error(error.name); process.exitCode = 1; });
