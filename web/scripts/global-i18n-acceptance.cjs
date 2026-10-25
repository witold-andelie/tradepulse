// Optional existing Playwright runtime; this script adds no application dependency.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '../..');
const base = process.env.TRADEPULSE_PREVIEW_URL || 'http://127.0.0.1:5185';
const out = path.resolve(process.env.TRADEPULSE_QA_DIR || '/tmp/tradepulse-global-i18n');
const fixture = require(path.join(root, 'contracts/fixtures/run_output.fixture.json'));
const trace = fs.readFileSync(path.join(root, 'contracts/fixtures/trace.fixture.jsonl'), 'utf8').trim().split('\n').map(JSON.parse);
const locales = ['en', 'zh-CN', 'zh-TW', 'es', 'fr', 'de', 'pt-BR', 'ja', 'ko', 'cs', 'ar'];
const screenshots = new Set(['en', 'zh-CN', 'es', 'ja', 'ar']);
const routes = [
  ['discover', '/discover', 'Make sense of the market.'], ['leaderboard', '/pool/us_equity', 'US equities'],
  ['detail', '/ticker/us_equity/SYN369', 'SYN369'], ['factors', '/factors', 'Factor Lab'],
  ['regime', '/regime', 'Market Regime'], ['track-record', '/track-record', 'Track Record'], ['trace', '/trace', 'Run Trace'],
];
const results = [], matrix = [], consoleIssues = [];
fs.mkdirSync(out, { recursive: true });
function dict(locale) { return require(path.join(root, 'web/src/i18n', locale === 'en' ? 'en.json' : `locales/${locale}.json`)); }
function text(locale, key) { return dict(locale)[key] || key; }
function interpolate(message, values) { return message.replace(/\{([a-zA-Z]\w*)\}/g, (_, key) => String(values[key])); }
async function check(name, action, page) {
  try { await action(); results.push({ name, status: 'PASS' }); console.log('PASS', name); }
  catch (error) { results.push({ name, status: 'FAIL', error: error.stack }); console.log('FAIL', name, error.message); if (page) await page.screenshot({ path: path.join(out, `failure-${results.length}.png`) }).catch(() => {}); }
}
async function choose(page, locale) {
  const url = page.url();
  const control = page.locator('#app-language');
  await control.focus(); await control.selectOption(locale);
  await page.waitForFunction((value) => document.documentElement.lang === value, locale);
  assert.equal(page.url(), url);
  assert(await control.evaluate((node) => node === document.activeElement), 'Language selection stole focus');
  assert.equal(await page.locator('html').getAttribute('dir'), locale === 'ar' ? 'rtl' : 'ltr');
}
async function mode(page, locale, pro) {
  await page.getByRole('button', { name: text(locale, pro ? 'Pro View' : 'Simple View'), exact: true }).click();
}
async function nav(page, route, title) {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.locator(`.navigation a[href="${route}"]`).click();
  await page.getByRole('heading', { name: title, exact: true }).first().waitFor();
}
async function localeRoundTrip(page, locale, reading) {
  const url = page.url(); const before = await reading();
  await choose(page, locale === 'en' ? 'fr' : 'en');
  assert.equal(page.url(), url); assert.deepEqual(await reading(), before);
  await choose(page, locale); assert.equal(page.url(), url); assert.deepEqual(await reading(), before);
}
async function reflow(page, locale, name) {
  for (const width of [1440, 768, 320]) {
    await page.setViewportSize({ width, height: 1000 }); await page.waitForTimeout(45);
    await page.evaluate(() => window.scrollTo(0, 0));
    const size = await page.evaluate(() => ({ viewport: innerWidth, body: document.body.scrollWidth, root: document.documentElement.scrollWidth }));
    assert(size.body <= width && size.root <= width, `${locale}/${name} overflow: ${JSON.stringify(size)}`);
    const selector = await page.locator('#app-language').boundingBox();
    assert(selector && selector.x >= 0 && selector.x + selector.width <= width && selector.height >= 44, 'Language selector is clipped or undersized');
    if (screenshots.has(locale)) await page.screenshot({ path: path.join(out, `${locale}-${name}-${width}.png`), fullPage: true });
  }
  await page.setViewportSize({ width: 1440, height: 1000 });
}
async function routeChecks(page, locale, name) {
  assert.equal(await page.locator('#app-language').count(), 1);
  assert.equal(await page.locator('#app-language option').count(), 11);
  assert.equal(await page.locator('#app-language').inputValue(), locale);
  assert.equal(await page.locator('#research-guide-language').count(), 0);
  assert.equal(await page.locator('html').getAttribute('lang'), locale);
  assert((await page.locator('footer').innerText()).includes(fixture.disclaimer));
  assert((await page.locator('.mode-banner.warning').innerText()).includes(text(locale, 'SYNTHETIC FIXTURE — fictional instruments, generated numbers. Not results.')));
  // Detect visible exact English authored messages outside protected original/canonical data.
  const residual = await page.evaluate(({ english, localized }) => {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); const found = [];
    while (walker.nextNode()) {
      const node = walker.currentNode, parent = node.parentElement, value = node.textContent.trim();
      if (!parent || !value || parent.closest('.original-source,[translate="no"],pre,code,bdi,option,script,style') || parent.closest('[aria-hidden="true"]')) continue;
      if (!parent.getClientRects().length || getComputedStyle(parent).visibility === 'hidden') continue;
      if (Object.hasOwn(english, value) && localized[value] !== value && localized[value] != null) found.push(value);
    }
    return [...new Set(found)];
  }, { english: dict('en'), localized: dict(locale) });
  assert.deepEqual(residual, [], `Unlocalized authored text: ${residual.join('; ')}`);
  await reflow(page, locale, name);
}
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.TRADEPULSE_CHROMIUM || '/usr/bin/chromium', headless: true, args: ['--no-sandbox'] });
  const { messages: guide } = await import(path.join(root, 'web/src/components/agentResearch/messages.js'));
  for (const locale of locales) {
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } }); const page = await context.newPage();
    page.setDefaultTimeout(12000);
    page.on('pageerror', (error) => consoleIssues.push({ locale, error: error.message }));
    page.on('console', (message) => { if (['error', 'warning'].includes(message.type())) consoleIssues.push({ locale, error: message.text() }); });
    for (const [name, route, heading] of routes) {
      const start = results.length;
      await check(`${locale} · ${name}: localization, interactions and 3 widths`, async () => {
        if (name === 'discover') {
          await page.goto(base + route); await page.getByRole('heading', { name: routes[0][2], exact: true }).waitFor();
          assert.equal(await page.locator('#app-language').inputValue(), 'en');
          await choose(page, locale);
          await page.getByRole('heading', { name: text(locale, heading), exact: true }).waitFor();
          await page.locator('.workspace-tools .research-guide summary').click();
          assert(await page.getByRole('heading', { name: text(locale, 'Coverage is not confidence'), exact: true }).isVisible());
          await page.locator('.workspace-tools .research-guide summary').click();
        } else if (name === 'leaderboard') {
          await page.locator('.discover-hero a[href="/pool/us_equity"]').first().click();
          await page.getByRole('heading', { name: text(locale, heading), exact: true }).waitFor();
          await page.getByLabel(text(locale, 'Sort candidates'), { exact: true }).selectOption('score:desc');
          await page.getByRole('button', { name: text(locale, 'Next →'), exact: true }).click();
          await localeRoundTrip(page, locale, () => page.locator('.candidate-card h3 a').allTextContents());
          assert(new URL(page.url()).searchParams.get('page') === '2');
          await mode(page, locale, true);
          const row = fixture.recommendations.find((item) => item.symbol === 'SYN369');
          await page.getByRole('searchbox').fill(row.symbol);
          await page.getByLabel(text(locale, 'Sector'), { exact: true }).selectOption(row.sector);
          await page.locator('.tier-filters input[type="checkbox"]').first().check();
          await page.waitForFunction(() => document.querySelectorAll('.leaderboard tbody tr').length === 1);
          await localeRoundTrip(page, locale, async () => ({ rows: await page.locator('.leaderboard tbody tr').allTextContents().then((rows) => rows.map((row) => row.match(/SYN\d+/)?.[0])), sector: await page.getByRole('combobox').nth(1).inputValue(), search: await page.getByRole('searchbox').inputValue() }));
          const canonical = new URL(page.url()).searchParams; assert.equal(canonical.get('sector'), row.sector); assert.equal(canonical.get('q'), row.symbol);
          await page.getByRole('searchbox').fill('DOES_NOT_EXIST');
          await page.getByRole('heading', { name: text(locale, 'No instruments match your filters'), exact: true }).waitFor();
          await page.getByRole('button', { name: text(locale, 'Clear all filters'), exact: true }).click();
          await page.getByRole('searchbox').fill(row.symbol);
        } else if (name === 'detail') {
          await page.locator('.leaderboard tbody a.symbol').first().click();
          await page.getByRole('heading', { name: 'SYN369', exact: true }).waitFor();
          await page.getByRole('heading', { name: guide[locale].title, exact: true }).waitFor();
          await page.locator('.claim.rejected summary').first().click();
          const explanation = fixture.explanations.find((item) => item.symbol === 'SYN369');
          for (const claim of explanation.claims) {
            assert((await page.locator('#explanation').textContent()).includes(claim.text));
            for (const evidence of claim.evidence) {
              const original = await page.locator('.claims').textContent();
              for (const key of ['evidence_id', 'rows_sha256', 'query_template', 'source_table', 'as_of']) assert(original.includes(evidence[key]));
            }
          }
          assert.equal(await page.locator('#agent-research-guide > details').count(), 4);
          assert((await page.locator('#agent-research-guide').innerText()).includes(guide[locale].temporal));
          await localeRoundTrip(page, locale, async () => ({ metrics: await page.locator('#measurements dd').allTextContents().then((values) => values.map((value) => value.match(/[+−-]?\d[\d,.]*/g))), narratives: await page.locator('.claims [translate="no"]').allTextContents(), guideIdentifiers: await page.locator('#agent-research-guide bdi').allTextContents(), evidenceParameters: await page.locator('.evidence pre').allTextContents() }));
          const source = page.locator('.claim.rejected [translate="no"]').first(); assert.equal(await source.getAttribute('dir'), 'auto');
          if (locale !== 'en') assert(await page.locator('#explanation .source-label').count() > 0);
        } else if (name === 'factors') {
          await nav(page, route, text(locale, heading));
          await page.locator('.gate-explainer summary').click();
          await page.getByRole('combobox', { name: text(locale, 'Asset pool'), exact: true }).selectOption('crypto');
          await page.getByLabel(text(locale, 'Factor status'), { exact: true }).selectOption('ACTIVE');
          const expected = fixture.factor_cards.filter((item) => item.pool === 'crypto' && item.status === 'ACTIVE').length;
          await page.waitForFunction((count) => document.querySelectorAll('.factor-card').length === count, expected);
          assert.equal(await page.locator('.factor-card .gate-chip').count(), expected * 5);
          await localeRoundTrip(page, locale, () => page.locator('.factor-card .font-mono').allTextContents());
          await page.locator('.factor-card details').last().locator('summary').click();
        } else if (name === 'regime') {
          await nav(page, route, text(locale, heading));
          await page.locator('.chart-figure button').first().click();
          assert(await page.locator('.chart-figure table tbody tr').count() > 0);
          await localeRoundTrip(page, locale, () => page.locator('.chart-figure table tbody td').allTextContents());
          const recorded = fixture.regimes[0].history[0].date; assert((await page.locator('.chart-figure table').first().innerText()).includes(recorded));
        } else if (name === 'track-record') {
          await nav(page, route, text(locale, heading));
          await page.locator('.chart-figure button').first().click();
          assert.equal(await page.locator('.chart-figure table').first().locator('tbody tr').count(), fixture.track_record.calibration.length);
          await localeRoundTrip(page, locale, () => page.locator('.chart-figure table').first().locator('tbody td').allTextContents());
          assert((await page.locator('main').innerText()).includes('1,808')); assert((await page.locator('main').innerText()).includes('1,200'));
        } else if (name === 'trace') {
          await nav(page, route, text(locale, heading));
          await page.getByRole('heading', { name: text(locale, 'Event log'), exact: true }).waitFor();
          await page.getByLabel(text(locale, 'Event kind'), { exact: true }).selectOption('retry');
          assert.equal(await page.locator('.event-table tbody tr').count(), trace.filter((event) => event.kind === 'retry').length);
          await page.locator('.event-payload summary').first().click();
          const payload = await page.locator('.event-payload pre').first().textContent(); assert.deepEqual(JSON.parse(payload), trace.find((event) => event.kind === 'retry').payload);
          await localeRoundTrip(page, locale, () => page.locator('.event-payload pre').allTextContents());
          await page.getByRole('button', { name: text(locale, 'Clear filters'), exact: true }).click();
          assert.equal(await page.locator('.event-table tbody tr').count(), trace.length);
          await page.reload(); await page.getByRole('heading', { name: text(locale, heading), exact: true }).waitFor();
          assert.equal(await page.locator('#app-language').inputValue(), locale);
        }
        await routeChecks(page, locale, name);
      }, page);
      matrix.push({ locale, route: name, status: results[start].status });
      if (results[start].status === 'FAIL') break;
    }
    await context.close();
  }
  await check('global preference migration, invalid fallback and blocked-storage navigation', async () => {
    for (const scenario of ['migrate', 'invalid', 'blocked']) {
      const context = await browser.newContext();
      await context.addInitScript((kind) => {
        if (kind === 'blocked') Object.defineProperty(window, 'localStorage', { get() { throw new Error('Storage blocked'); } });
        else if (kind === 'invalid') { localStorage.setItem('tradepulse.locale', 'invalid'); localStorage.setItem('tradepulse.researchGuide.locale', 'ar'); }
        else localStorage.setItem('tradepulse.researchGuide.locale', 'ja');
      }, scenario);
      const page = await context.newPage(); await page.goto(base + '/discover'); await page.locator('h1').waitFor();
      assert.equal(await page.locator('#app-language').inputValue(), scenario === 'migrate' ? 'ja' : 'en');
      await choose(page, 'ar'); await nav(page, '/factors', text('ar', 'Factor Lab')); assert.equal(await page.locator('html').getAttribute('dir'), 'rtl');
      await context.close();
    }
  });
  await check('unknown instrument, empty results and global language selector', async () => {
    const page = await browser.newPage(); await page.goto(base + '/ticker/us_equity/NOT_RECORDED'); await page.locator('h1').waitFor();
    for (const locale of locales) { await choose(page, locale); assert((await page.locator('main').innerText()).includes(text(locale, 'Instrument not found'))); }
    await page.close();
  });
  await check('native speech availability recorded without claiming audible playback', async () => {
    const page = await browser.newPage(); await page.goto(base + '/ticker/us_equity/SYN369'); await page.locator('#agent-research-guide').waitFor();
    const native = await page.evaluate(() => ({ api: 'speechSynthesis' in window, voices: window.speechSynthesis?.getVoices().map(({ lang, name }) => ({ lang, name })) || [] }));
    fs.writeFileSync(path.join(out, 'native-speech.json'), JSON.stringify(native, null, 2));
    if (!native.voices.length) assert.equal(await page.getByRole('button', { name: guide.en.play, exact: true }).isDisabled(), true);
    await page.close();
  });
  await check('speech controller test double: all locales, pause/resume/stop, locale and navigation cancellation', async () => {
    const context = await browser.newContext();
    await context.addInitScript((languages) => {
      const events = new EventTarget();
      window.__speech = { spoken: [], canceled: 0, paused: 0, resumed: 0, utterance: null };
      window.SpeechSynthesisUtterance = class { constructor(value) { this.text = value; } };
      Object.defineProperty(window, 'speechSynthesis', { value: {
        getVoices: () => languages.map((lang) => ({ lang, name: `Test ${lang}`, voiceURI: lang, localService: true })),
        cancel() { window.__speech.canceled += 1; }, pause() { window.__speech.paused += 1; }, resume() { window.__speech.resumed += 1; },
        speak(utterance) { window.__speech.utterance = utterance; window.__speech.spoken.push({ text: utterance.text, lang: utterance.lang }); utterance.onstart?.(); },
        addEventListener: events.addEventListener.bind(events), removeEventListener: events.removeEventListener.bind(events),
      }, configurable: true });
    }, ['en-US', 'zh-CN', 'zh-TW', 'es-ES', 'fr-FR', 'de-DE', 'pt-BR', 'ja-JP', 'ko-KR', 'cs-CZ', 'ar-SA']);
    const page = await context.newPage(); await page.goto(base + '/ticker/us_equity/SYN369'); await page.locator('#agent-research-guide').waitFor();
    assert.equal(await page.evaluate(() => window.__speech.spoken.length), 0);
    for (const locale of locales) {
      await choose(page, locale); const g = guide[locale];
      await page.getByRole('button', { name: g.play, exact: true }).click();
      const spoken = await page.evaluate(() => window.__speech.spoken.at(-1));
      assert(spoken.text.includes(g.title)); assert(spoken.lang.toLowerCase().startsWith(locale.toLowerCase().split('-')[0]));
      for (const claim of fixture.explanations.find((item) => item.symbol === 'SYN369').claims) assert(!spoken.text.includes(claim.text), 'Arbitrary source text was narrated');
      await page.getByRole('button', { name: g.pause, exact: true }).click(); await page.getByRole('button', { name: g.resume, exact: true }).click();
      const canceled = await page.evaluate(() => window.__speech.canceled);
      await choose(page, locale === 'en' ? 'fr' : 'en'); assert(await page.evaluate(() => window.__speech.canceled) > canceled);
      await choose(page, locale);
      await page.getByRole('button', { name: g.play, exact: true }).click(); await page.getByRole('button', { name: g.stop, exact: true }).click();
    }
    const count = await page.evaluate(() => window.__speech.spoken.length);
    await page.getByRole('button', { name: guide.ar.play, exact: true }).click();
    await page.evaluate(() => window.__speech.utterance.onerror?.({ error: 'test-only' }));
    await page.waitForFunction((message) => document.querySelector('#agent-research-guide [role="status"]').textContent.includes(message), guide.ar.error);
    assert((await page.locator('#agent-research-guide [role="status"]').innerText()).includes(guide.ar.error));
    await page.getByRole('button', { name: guide.ar.play, exact: true }).click();
    const before = await page.evaluate(() => window.__speech.canceled);
    await nav(page, '/factors', text('ar', 'Factor Lab')); assert(await page.evaluate(() => window.__speech.canceled) > before);
    assert.equal(await page.evaluate(() => window.__speech.spoken.length), count + 2);
    await context.close();
  });
  await check('no speech API and no matching voice retain localized readable guide', async () => {
    const context = await browser.newContext(); await context.addInitScript(() => Object.defineProperty(window, 'speechSynthesis', { value: undefined }));
    const page = await context.newPage(); await page.goto(base + '/ticker/us_equity/SYN369'); await page.locator('#agent-research-guide').waitFor(); await choose(page, 'ja');
    assert((await page.locator('#agent-research-guide').innerText()).includes(guide.ja.unsupported)); assert.equal(await page.locator('#agent-research-guide > details').count(), 4);
    await context.close();
  });
  await check('localized keyboard, mobile menu, focus, text enlargement and reduced motion', async () => {
    const page = await browser.newPage({ viewport: { width: 320, height: 1000 } }); await page.goto(base + '/discover'); await page.locator('h1').waitFor(); await choose(page, 'ar');
    const selector = page.locator('#app-language'); await selector.focus(); const outline = await selector.evaluate((node) => getComputedStyle(node).outlineStyle); assert.notEqual(outline, 'none');
    await page.keyboard.press('Tab'); assert.equal(await page.evaluate(() => document.activeElement.tagName), 'BUTTON');
    const menu = page.locator('.menu-toggle'); await menu.focus(); await page.keyboard.press('Enter'); assert.equal(await menu.getAttribute('aria-expanded'), 'true');
    await page.keyboard.press('Tab'); await page.keyboard.press('Escape'); assert.equal(await menu.getAttribute('aria-expanded'), 'false'); assert(await menu.evaluate((node) => node === document.activeElement));
    await page.emulateMedia({ reducedMotion: 'reduce' }); await page.addStyleTag({ content: ':root { font-size: 200% !important; }' });
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    fs.writeFileSync(path.join(out, 'arabic-discover-aria.yml'), await page.locator('main').ariaSnapshot());
    await page.screenshot({ path: path.join(out, 'ar-discover-320-text-200.png') }); await page.close();
  });
  await check('normal journeys have no console errors or warnings', async () => assert.deepEqual(consoleIssues, []));
  fs.writeFileSync(path.join(out, 'results.json'), JSON.stringify({ results, matrix, consoleIssues }, null, 2));
  await browser.close(); console.log(`${results.filter((result) => result.status === 'PASS').length}/${results.length} groups passed`);
  process.exitCode = results.some((result) => result.status === 'FAIL') ? 1 : 0;
})().catch((error) => { console.error(error); process.exit(1); });
