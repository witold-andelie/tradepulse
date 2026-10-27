// Uses existing external Playwright tooling; no application dependency is added.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const cp = require('node:child_process');
const root = path.resolve(__dirname, '../..');
const base = process.env.TRADEPULSE_PREVIEW_URL || 'http://127.0.0.1:5232';
const out = path.resolve(process.env.TRADEPULSE_QA_DIR || '/tmp/tradepulse-v2-loader');
const build = path.resolve(process.env.TRADEPULSE_BUILD_DIR || path.join(root, 'web/dist'));
const manifest = JSON.parse(fs.readFileSync(path.join(build, '.vite/manifest.json'), 'utf8'));
const appAsset = (locale) => '/'+manifest[`src/i18n/locales/${locale}.json`].file;
const guideAsset = (locale) => '/'+manifest[`src/components/agentResearch/locales/${locale}.json`].file;
const languages = ['en','zh-CN','zh-TW','es','fr','de','pt-BR','ja','ko','cs','ar'];
const results = [];
fs.mkdirSync(out, { recursive: true });
async function check(name, action) {
  try { const evidence = await action(); results.push({ name, status: 'PASS', evidence }); console.log('PASS',name); }
  catch (error) { results.push({ name, status: 'FAIL', error: error.stack }); console.log('FAIL',name,error.message); }
}
async function selected(page, locale) {
  await page.locator('#app-language').selectOption(locale);
  await page.waitForFunction((id) => document.documentElement.lang === id && document.querySelector('#app-language')?.getAttribute('aria-busy') === 'false', locale);
}
async function context(browser, preference, legacy = false) {
  const c = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  if (preference) await c.addInitScript(({ preference, legacy }) => { localStorage.setItem(legacy ? 'tradepulse.researchGuide.locale' : 'tradepulse.locale', preference); localStorage.setItem('tradepulse.view','pro'); },{preference,legacy});
  return c;
}
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.TRADEPULSE_CHROMIUM || '/usr/bin/chromium', args:['--no-sandbox'] });
  try {
    await check('production graph has twenty lazy catalogs and no eager non-English catalog',async()=>{
      const entry=Object.values(manifest).find(x=>x.isEntry);const seen=new Set();
      function visit(key){if(seen.has(key))return;seen.add(key);for(const child of manifest[key]?.imports||[])visit(child);}
      visit(Object.keys(manifest).find(k=>manifest[k]===entry));
      assert(![...seen].some(k=>/locales\/(?!en\.json)/.test(k)));
      for(const locale of languages.filter(l=>l!=='en'))assert(appAsset(locale)!==guideAsset(locale));
      const chunks=fs.readdirSync(path.join(build,'assets')).filter(x=>x.endsWith('.js')).map(name=>({name,bytes:fs.statSync(path.join(build,'assets',name)).size}));
      assert(chunks.filter(x=>!x.name.startsWith('run_output.fixture')).every(x=>x.bytes<=1000000));
      return { eagerModules:[...seen],lazyCatalogCount:20,chunks };
    });
    await check('initial English requests neither non-English catalogs nor guides',async()=>{
      const c=await context(browser);const p=await c.newPage();const requests=[];p.on('request',r=>requests.push(new URL(r.url()).pathname));
      await p.goto(base+'/discover');await p.locator('h1').waitFor();assert.equal(await p.locator('html').getAttribute('lang'),'en');
      assert(await p.locator('#app-language').isVisible());
      for(const locale of languages.filter(l=>l!=='en'))assert(!requests.includes(appAsset(locale))&&!requests.includes(guideAsset(locale)));
      await c.close();return {requests};
    });
    await check('saved non-English preference gates English UI and exposes selector during loading',async()=>{
      const c=await context(browser,'es');const p=await c.newPage();let release;const gate=new Promise(r=>release=r);
      await p.route('**'+appAsset('es'),async route=>{await gate;await route.continue();});
      await p.goto(base+'/discover',{waitUntil:'domcontentloaded'});await p.locator('.locale-bootstrap').waitFor();
      assert(await p.locator('#app-language').isVisible());assert.equal(await p.locator('.navigation').count(),0);assert.equal(await p.locator('h1').count(),0);
      await p.screenshot({path:path.join(out,'saved-es-loading.png')});release();
      await p.waitForFunction(()=>document.documentElement.lang==='es');await p.locator('h1').waitFor();
      assert.equal(await p.locator('#app-language').inputValue(),'es');await c.close();
    });
    await check('rapid switching activates the final selection when earlier import finishes later',async()=>{
      const c=await context(browser);const p=await c.newPage();let release;const gate=new Promise(r=>release=r);
      await p.goto(base+'/pool/us_equity?q=SYN369&sort=score&dir=desc');await p.locator('h1').waitFor();
      await p.route('**'+appAsset('de'),async route=>{await gate;await route.continue();});
      await p.locator('#app-language').selectOption('de');await selected(p,'fr');release();await p.waitForTimeout(200);
      assert.equal(await p.locator('html').getAttribute('lang'),'fr');assert.equal(new URL(p.url()).searchParams.get('q'),'SYN369');
      assert.equal(await p.evaluate(()=>localStorage.getItem('tradepulse.locale')),'fr');await c.close();
    });
    await check('legacy guide preference migrates, reloads and preserves RTL',async()=>{
      const c=await context(browser,'ar',true);const p=await c.newPage();await p.goto(base+'/discover');await p.locator('h1').waitFor();
      assert.equal(await p.locator('html').getAttribute('lang'),'ar');assert.equal(await p.locator('html').getAttribute('dir'),'rtl');
      assert.equal(await p.evaluate(()=>localStorage.getItem('tradepulse.locale')),'ar');await p.reload();await p.locator('h1').waitFor();assert.equal(await p.locator('#app-language').inputValue(),'ar');await c.close();
    });
    await check('catalog import failure gives accessible English fallback and explicit retry',async()=>{
      const c=await context(browser,'fr');const p=await c.newPage();const pattern='**'+appAsset('fr');
      await p.route(pattern,route=>route.abort('internetdisconnected'));await p.goto(base+'/discover');await p.getByRole('alert').waitFor();
      assert.equal(await p.locator('html').getAttribute('lang'),'en');assert.equal(await p.evaluate(()=>localStorage.getItem('tradepulse.locale')),'en');
      assert(await p.locator('#app-language').isVisible());assert((await p.getByRole('alert').innerText()).includes('English is active'));
      await p.screenshot({path:path.join(out,'catalog-error.png')});await p.unroute(pattern);await p.getByRole('button',{name:'Retry',exact:true}).click();
      await p.waitForFunction(()=>document.documentElement.lang==='fr');await p.locator('h1').waitFor();assert.equal(await p.locator('#app-language').inputValue(),'fr');await c.close();
    });
    await check('offline locale failure does not erase records and recovers after retry',async()=>{
      const c=await context(browser,'en');const p=await c.newPage();await p.goto(base+'/pool/us_equity?q=SYN369');await p.locator('tbody').waitFor();const before=await p.locator('tbody').innerText();
      await c.setOffline(true);await p.locator('#app-language').selectOption('ko');await p.getByRole('alert').waitFor();
      assert.equal(await p.locator('tbody').innerText(),before);assert.equal(await p.locator('html').getAttribute('lang'),'en');
      await c.setOffline(false);await p.getByRole('button',{name:'Retry',exact:true}).click();await p.waitForFunction(()=>document.documentElement.lang==='ko');assert.equal(new URL(p.url()).searchParams.get('q'),'SYN369');await c.close();
    });
    await check('guide chunks load only on detail, cache on reuse, and preserve source evidence',async()=>{
      const c=await context(browser,'fr');const p=await c.newPage();const requests=[];p.on('request',r=>requests.push(new URL(r.url()).pathname));
      await p.goto(base+'/discover');await p.locator('h1').waitFor();assert(requests.includes(appAsset('fr')));assert(!requests.includes(guideAsset('fr')));
      await p.goto(base+'/ticker/us_equity/SYN369');await p.locator('#agent-research-guide[lang="fr"]').waitFor();assert(requests.includes(guideAsset('fr')));
      const hashes=await p.locator('.hash').allTextContents();const count=requests.filter(x=>x===appAsset('fr')||x===guideAsset('fr')).length;
      await selected(p,'en');await selected(p,'fr');await p.locator('#agent-research-guide[lang="fr"]').waitFor();
      assert.equal(requests.filter(x=>x===appAsset('fr')||x===guideAsset('fr')).length,count);assert.deepEqual(await p.locator('.hash').allTextContents(),hashes);await c.close();
      return {catalogRequests:requests.filter(x=>x===appAsset('fr')||x===guideAsset('fr'))};
    });
    await check('guide import failure preserves selector and falls back without English caveat flash',async()=>{
      const c=await context(browser,'ja');const p=await c.newPage();const pattern='**'+guideAsset('ja');
      await p.route(pattern,route=>route.abort());await p.goto(base+'/ticker/us_equity/SYN369');await p.getByRole('alert').waitFor();
      assert.equal(await p.locator('html').getAttribute('lang'),'en');await p.locator('#agent-research-guide[lang="en"]').waitFor();
      assert(await p.locator('#app-language').isVisible());await p.unroute(pattern);await p.getByRole('button',{name:'Retry',exact:true}).click();
      await p.locator('#agent-research-guide[lang="ja"]').waitFor();assert.equal(await p.locator('html').getAttribute('lang'),'ja');await c.close();
    });
    await check('delayed guide does not flash English and cannot override a later locale selection',async()=>{
      const c=await context(browser,'ja');const p=await c.newPage();let release;const gate=new Promise(r=>release=r);
      await p.goto(base+'/pool/us_equity');await p.locator('h1').waitFor();
      await p.route('**'+guideAsset('ja'),async route=>{await gate;await route.continue();});
      await p.locator('a[href="/ticker/us_equity/SYN369"]').first().click();
      await p.getByRole('status').filter({hasText:require(path.join(root,'web/src/i18n/locales/ja.json'))['Loading research data…']}).waitFor();
      assert.equal(await p.locator('.detail-overview').count(),0);assert(await p.locator('#app-language').isVisible());
      assert(!(await p.locator('main').innerText()).includes('Explore the recorded Agent research'));
      await selected(p,'en');await p.locator('#agent-research-guide[lang="en"]').waitFor();release();await p.waitForTimeout(150);
      assert.equal(await p.locator('html').getAttribute('lang'),'en');assert.equal(await p.locator('#agent-research-guide').getAttribute('lang'),'en');await c.close();
    });
    await check('a previous guide failure cannot cancel a newer pending language',async()=>{
      const c=await context(browser,'ja');const p=await c.newPage();let failGuide,releaseCatalog,seenCatalog;
      const guideGate=new Promise(r=>failGuide=r),catalogGate=new Promise(r=>releaseCatalog=r),catalogSeen=new Promise(r=>seenCatalog=r);
      await p.route('**'+guideAsset('ja'),async route=>{await guideGate;await route.abort('failed');});
      await p.route('**'+appAsset('es'),async route=>{seenCatalog();await catalogGate;await route.continue();});
      await p.goto(base+'/pool/us_equity');await p.waitForFunction(()=>document.documentElement.lang==='ja');
      await p.locator('a[href="/ticker/us_equity/SYN369"]').first().click();
      const ja=require(path.join(root,'web/src/i18n/locales/ja.json'));
      await p.getByRole('status').filter({hasText:ja['Loading research data…']}).waitFor();
      await p.locator('#app-language').selectOption('es');await catalogSeen;failGuide();
      await p.getByRole('alert').filter({hasText:ja['Data could not be loaded. Please retry.']}).waitFor();
      assert.equal(await p.locator('html').getAttribute('lang'),'ja');assert.equal(await p.locator('#app-language').inputValue(),'es');
      assert.equal(await p.locator('#app-language').getAttribute('aria-busy'),'true');releaseCatalog();
      await p.locator('#agent-research-guide[lang="es"]').waitFor();assert.equal(await p.locator('html').getAttribute('lang'),'es');
      await c.close();return {previousLocale:'ja',latestLocale:'es',lateFailureIgnored:true};
    });
    await check('blocked localStorage permits in-memory selection and no unauthorized requests',async()=>{
      const c=await context(browser);await c.addInitScript(()=>Object.defineProperty(window,'localStorage',{get(){throw new DOMException('Blocked','SecurityError')}}));
      const p=await c.newPage();const mutations=[];p.on('request',r=>{if(!['GET','HEAD'].includes(r.method()))mutations.push(r.method()+' '+r.url());});
      await p.goto(base+'/discover');await p.locator('h1').waitFor();await selected(p,'cs');assert.equal(await p.locator('html').getAttribute('lang'),'cs');assert.deepEqual(mutations,[]);await c.close();
    });
  } finally {
    await browser.close();fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({revision:cp.execFileSync('git',['rev-parse','HEAD'],{cwd:root,encoding:'utf8'}).trim(),results},null,2));
  }
  console.log(`${results.filter(r=>r.status==='PASS').length}/${results.length} loader browser groups passed`);process.exitCode=results.some(r=>r.status==='FAIL')?1:0;
})().catch(error=>{console.error(error);process.exitCode=1;});
