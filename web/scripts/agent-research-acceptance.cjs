// Uses the existing optional Playwright runtime; no application dependency is added.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const fixture = require('../../contracts/fixtures/run_output.fixture.json');
const base = process.env.TRADEPULSE_PREVIEW_URL || 'http://127.0.0.1:5184';
const out = process.env.TRADEPULSE_QA_DIR || '/tmp/tradepulse-agent-research';
const localeIds = ['en', 'zh-CN', 'zh-TW', 'es', 'fr', 'de', 'pt-BR', 'ja', 'ko', 'cs', 'ar'];
fs.mkdirSync(out, { recursive: true });

function speechStub({ noApi = false, empty = false } = {}) {
  if (noApi) {
    Object.defineProperty(window, 'speechSynthesis', { configurable: true, value: undefined });
    return;
  }
  const events = new EventTarget();
  const voices = empty ? [] : ['en-US', 'zh-CN', 'zh-TW', 'es-ES', 'fr-FR', 'de-DE', 'pt-BR', 'ja-JP', 'ko-KR', 'cs-CZ', 'ar-SA']
    .map((lang) => ({ lang, voiceURI: lang, name: `Test ${lang}`, localService: true }));
  window.__speech = { calls: [], cancels: 0, pauses: 0, resumes: 0, current: null };
  class Utterance { constructor(text) { this.text = text; } }
  Object.defineProperty(window, 'SpeechSynthesisUtterance', { configurable: true, value: Utterance });
  Object.defineProperty(window, 'speechSynthesis', { configurable: true, value: {
    getVoices: () => voices,
    addEventListener: (...args) => events.addEventListener(...args), removeEventListener: (...args) => events.removeEventListener(...args),
    speak(utterance) { window.__speech.current = utterance; window.__speech.calls.push({ text: utterance.text, lang: utterance.lang }); utterance.onstart?.(); },
    pause() { window.__speech.pauses += 1; }, resume() { window.__speech.resumes += 1; }, cancel() { window.__speech.cancels += 1; },
  } });
}

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.TRADEPULSE_CHROMIUM || '/usr/bin/chromium', headless: true, args: ['--no-sandbox'] });
  const native = await browser.newPage();
  await native.goto(base + '/ticker/us_equity/SYN369');
  await native.locator('#agent-research-guide').waitFor();
  const nativeSpeech = await native.evaluate(() => ({ api: 'speechSynthesis' in window, voices: window.speechSynthesis?.getVoices().map((voice) => ({ name: voice.name, lang: voice.lang })) || [] }));
  await native.screenshot({ path: path.join(out, 'native-speech.png'), fullPage: true });
  await native.close();
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  await context.addInitScript(speechStub);
  const page = await context.newPage();
  page.setDefaultTimeout(12000);
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  page.on('console', (message) => { if (['warning', 'error'].includes(message.type())) errors.push(message.text()); });
  const results = [];
  async function check(name, fn) {
    try { await fn(); results.push({ name, status: 'PASS' }); console.log('PASS', name); }
    catch (error) { results.push({ name, status: 'FAIL', error: error.message }); console.log('FAIL', name, error.message); await page.screenshot({ path: path.join(out, `failure-${results.length}.png`) }); }
  }
  const abstained = fixture.explanations.find((item) => item.symbol === 'SYN369');
  const explained = fixture.explanations.find((item) => item.verdict === 'explained');
  const absent = fixture.recommendations.find((item) => !item.explanation_id);
  const route = (row) => `/ticker/${row.pool}/${row.symbol}`;
  async function goto(row) { await page.goto(base + route(row)); await page.locator('#agent-research-guide').waitFor(); }
  async function openQuestions() {
    for (const details of await page.locator('#agent-research-guide > details').all()) {
      if (!(await details.getAttribute('open') !== null)) await details.locator('summary').click();
    }
  }

  await check('explained record and four question-led disclosures', async () => {
    await goto(explained);
    assert.equal(await page.locator('#agent-research-guide > details').count(), 4);
    await openQuestions();
    assert((await page.locator('#agent-research-guide').innerText()).includes('This explanation is not recorded as abstained.'));
    assert.equal((await page.evaluate(() => window.__speech.calls)).length, 0);
  });
  await check('abstention, verified and rejected claims, exact original evidence and missing timing', async () => {
    await goto(abstained); await openQuestions();
    const guide = await page.locator('#agent-research-guide').innerText();
    assert(guide.includes('The explanation abstained'));
    assert(guide.includes('generated test records'));
    assert(guide.includes('cannot be independently reproduced'));
    for (const claim of abstained.claims) {
      assert(guide.includes(claim.text));
      await page.locator(`#explanation .claim.${claim.status} summary`).first().click();
      const content = await page.locator(`#explanation .claim.${claim.status}`).first().innerText();
      for (const item of claim.evidence) for (const key of ['evidence_id', 'rows_sha256', 'query_template', 'source_table']) assert(content.includes(item[key]));
    }
    assert((await page.locator('#explanation').innerText()).includes('No source link supplied.'));
  });
  await check('same original claims and financial fields across Simple and Pro', async () => {
    const snapshots = [];
    for (const view of ['Simple', 'Pro']) {
      await page.getByRole('button', { name: `${view} View`, exact: true }).click();
      snapshots.push({ guide: await page.locator('#agent-research-guide').innerText(), context: await page.locator('.detail-context').innerText(), evidence: await page.locator('#explanation .claims').innerText() });
    }
    assert.deepEqual(snapshots[0], snapshots[1]);
  });
  await check('all eleven locales preserve numbers, enums, evidence and original narratives', async () => {
    const values = await page.locator('#agent-research-guide dl dd').allTextContents();
    for (const locale of localeIds) {
      await page.locator('#research-guide-language').selectOption(locale);
      assert.deepEqual(await page.locator('#agent-research-guide dl dd').allTextContents(), values);
      assert.equal(await page.locator('#agent-research-guide').getAttribute('lang'), locale);
      assert.equal(await page.locator('html').getAttribute('lang'), 'en');
      assert((await page.locator('#agent-research-guide').innerText()).includes(abstained.claims[1].text));
      assert.equal(await page.locator('#explanation .claim.rejected .hash').textContent(), abstained.claims[1].evidence[0].rows_sha256);
    }
  });
  await check('Arabic RTL region with isolated LTR identifiers and original text', async () => {
    assert.equal(await page.locator('#agent-research-guide').getAttribute('dir'), 'rtl');
    assert.equal(await page.locator('#agent-research-guide bdi').first().getAttribute('dir'), 'ltr');
    assert(await page.locator('#agent-research-guide [lang=""][dir="auto"][translate="no"]').count());
    assert.equal(await page.locator('.detail-context').evaluate((node) => getComputedStyle(node).direction), 'ltr');
    await fs.promises.writeFile(path.join(out, 'arabic-aria.txt'), await page.locator('#agent-research-guide').ariaSnapshot());
  });
  await check('locale persistence, invalid preference fallback and blocked storage', async () => {
    await page.reload(); await page.locator('#agent-research-guide').waitFor();
    assert.equal(await page.locator('#research-guide-language').inputValue(), 'ar');
    await page.evaluate(() => localStorage.setItem('tradepulse.researchGuide.locale', 'unavailable'));
    await page.reload(); await page.locator('#agent-research-guide').waitFor();
    assert.equal(await page.locator('#research-guide-language').inputValue(), 'en');
    const blocked = await context.newPage();
    await blocked.addInitScript(() => { Object.defineProperty(window, 'localStorage', { get() { throw new DOMException('Blocked', 'SecurityError'); } }); });
    await blocked.goto(base + route(abstained)); await blocked.locator('#agent-research-guide').waitFor();
    await blocked.locator('#research-guide-language').selectOption('ja');
    assert.equal(await blocked.locator('#agent-research-guide').getAttribute('lang'), 'ja');
    await blocked.close();
  });
  await check('play, pause, resume, stop and exact readable structured speech', async () => {
    await page.getByRole('button', { name: 'Play', exact: true }).click();
    const call = await page.evaluate(() => window.__speech.calls.at(-1));
    assert.equal(call.lang, 'en-US');
    assert(call.text.includes('abstained'));
    assert(call.text.includes('cannot be independently reproduced'));
    assert(!call.text.includes(abstained.claims[1].text));
    await page.getByRole('button', { name: 'Pause', exact: true }).click();
    assert.equal(await page.evaluate(() => window.__speech.pauses), 1);
    await page.getByRole('button', { name: 'Resume', exact: true }).click();
    assert.equal(await page.evaluate(() => window.__speech.resumes), 1);
    await page.getByRole('button', { name: 'Stop', exact: true }).click();
    assert.equal(await page.getByRole('button', { name: 'Play', exact: true }).isEnabled(), true);
  });
  await check('locale changes cancel speech without auto-playing another language', async () => {
    await page.getByRole('button', { name: 'Play', exact: true }).click();
    const before = await page.evaluate(() => ({ calls: window.__speech.calls.length, cancels: window.__speech.cancels }));
    await page.locator('#research-guide-language').selectOption('ar');
    const after = await page.evaluate(() => ({ calls: window.__speech.calls.length, cancels: window.__speech.cancels }));
    assert.equal(after.calls, before.calls); assert(after.cancels > before.cancels);
    await page.locator('#agent-research-guide button.primary').click();
    assert.equal(await page.evaluate(() => window.__speech.calls.at(-1).lang), 'ar-SA');
  });
  await check('route navigation and instrument changes cancel active speech', async () => {
    const before = await page.evaluate(() => window.__speech.cancels);
    await page.getByRole('link', { name: 'Return to Discover', exact: true }).click();
    await page.getByRole('heading', { name: 'Make sense of the market.', exact: true }).waitFor();
    assert(await page.evaluate(() => window.__speech.cancels) > before);
    await goto(abstained);
    await page.locator('#research-guide-language').selectOption('en');
    await page.getByRole('button', { name: 'Play', exact: true }).click();
    const initial = await page.evaluate(() => window.__speech.cancels);
    await page.evaluate((url) => { history.pushState({}, '', url); window.dispatchEvent(new PopStateEvent('popstate')); }, route(explained));
    await page.getByRole('heading', { name: explained.symbol, exact: true }).waitFor();
    assert(await page.evaluate(() => window.__speech.cancels) > initial);
  });
  await check('no explanation and unknown instrument retain honest existing states', async () => {
    await goto(absent); await openQuestions();
    assert((await page.locator('#agent-research-guide').innerText()).includes('No explanation was supplied'));
    assert((await page.locator('#explanation').innerText()).includes('No explanation recorded'));
    await page.goto(base + '/ticker/us_equity/UNKNOWN');
    await page.getByRole('heading', { name: 'Instrument not found', level: 1, exact: true }).waitFor();
    assert.equal(await page.locator('#agent-research-guide').count(), 0);
  });
  await check('missing voices and unsupported browser remain readable with no silent fallback', async () => {
    for (const configuration of [{ empty: true }, { noApi: true }]) {
      const limited = await browser.newContext(); await limited.addInitScript(speechStub, configuration);
      const limitedPage = await limited.newPage();
      await limitedPage.goto(base + route(abstained)); await limitedPage.locator('#agent-research-guide').waitFor();
      const text = await limitedPage.locator('#agent-research-guide').innerText();
      if (configuration.empty) {
        assert(text.includes('No suitable voice'));
        assert(await limitedPage.getByRole('button', { name: 'Play', exact: true }).isDisabled());
        assert.equal(await limitedPage.evaluate(() => window.__speech.calls.length), 0);
      } else assert(text.includes('Read aloud is unavailable in this browser'));
      await limited.close();
    }
  });
  await check('speech errors leave the page and readable research usable', async () => {
    await goto(abstained); await page.locator('#research-guide-language').selectOption('en');
    await page.getByRole('button', { name: 'Play', exact: true }).click();
    await page.evaluate(() => window.__speech.current.onerror({ error: 'interrupted' }));
    await page.waitForFunction(() => document.querySelector('#agent-research-guide [role="status"]').textContent.includes('could not continue'));
    assert((await page.locator('#agent-research-guide [role="status"]').innerText()).includes('could not continue'));
    assert(await page.getByRole('button', { name: 'Play', exact: true }).isEnabled());
  });
  await check('keyboard disclosures, language selection, focus ring and control labels', async () => {
    await page.locator('#research-guide-language').focus();
    await page.keyboard.press('ArrowDown'); await page.keyboard.press('Enter');
    assert.equal(await page.locator('#research-guide-language').inputValue(), 'zh-CN');
    const summary = page.locator('#agent-research-guide > details').nth(1).locator('summary');
    await summary.focus();
    const initiallyOpen = await summary.evaluate((node) => node.parentElement.open);
    await page.keyboard.press('Enter');
    assert.notEqual(await summary.evaluate((node) => node.parentElement.open), initiallyOpen);
    const outline = await summary.evaluate((node) => getComputedStyle(node).outlineWidth);
    assert.notEqual(outline, '0px');
    const unnamed = await page.locator('#agent-research-guide').evaluate((root) => [...root.querySelectorAll('button,select')].filter((node) => !(node.labels?.length || node.getAttribute('aria-label') || node.textContent.trim())).length);
    assert.equal(unnamed, 0);
    await fs.promises.writeFile(path.join(out, 'guide-aria.txt'), await page.locator('#agent-research-guide').ariaSnapshot());
  });
  await check('1440, 768 and 320px layouts in English, Chinese and Arabic', async () => {
    await openQuestions();
    for (const width of [1440, 768, 320]) for (const locale of ['en', 'zh-CN', 'ar']) {
      await page.setViewportSize({ width, height: 1000 }); await page.locator('#research-guide-language').selectOption(locale);
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${width} ${locale}: page overflow`);
      const dimensions = await page.locator('#agent-research-guide').evaluate((node) => ({ content: node.scrollWidth, outer: node.clientWidth }));
      assert(dimensions.content <= dimensions.outer + 1, `${width} ${locale}: guide overflow`);
      await page.locator('#agent-research-guide').screenshot({ path: path.join(out, `guide-${locale}-${width}.png`) });
    }
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await page.evaluate(() => { document.documentElement.style.fontSize = '200%'; });
    await page.setViewportSize({ width: 768, height: 1000 });
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await page.screenshot({ path: path.join(out, 'arabic-text-200-percent.png'), fullPage: true });
    await page.evaluate(() => { document.documentElement.style.fontSize = ''; });
  });
  await check('clean browser console throughout the normal fixture journeys', async () => assert.deepEqual(errors, []));
  const report = { browser: browser.version(), nativeSpeech, results, errors, speechTesting: 'Playback lifecycle tested with an injected browser API double. No audible native voice acceptance is claimed.' };
  fs.writeFileSync(path.join(out, 'results.json'), JSON.stringify(report, null, 2));
  await browser.close();
  if (results.some((result) => result.status === 'FAIL')) process.exitCode = 1;
})().catch((error) => { console.error(error); process.exitCode = 1; });
