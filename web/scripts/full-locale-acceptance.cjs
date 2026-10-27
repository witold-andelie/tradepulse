// Optional preinstalled Playwright runtime. No application dependency or external service.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const cp = require('node:child_process');
const root = path.resolve(__dirname, '../..');
const out = path.resolve(process.env.TRADEPULSE_QA_DIR || '/tmp/tradepulse-full-locale');
const base = process.env.TRADEPULSE_PREVIEW_URL || 'http://127.0.0.1:5211';
const apiBase = process.env.TRADEPULSE_API_PREVIEW || 'http://127.0.0.1:5212';
const api = process.env.TRADEPULSE_TEST_API || 'http://127.0.0.1:5196';
const locales = (process.env.TRADEPULSE_LOCALES || 'en,zh-CN,zh-TW,es,fr,de,pt-BR,ja,ko,cs,ar').split(',');
const routes = [['discover','/discover'],['leaderboard','/pool/us_equity'],['detail','/ticker/us_equity/SYN369'],['factors','/factors'],['regime','/regime'],['track-record','/track-record'],['trace','/trace']];
const fixture = require(path.join(root, 'contracts/fixtures/run_output.fixture.json'));
const trace = fs.readFileSync(path.join(root,'contracts/fixtures/trace.fixture.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
const dictionary = (locale) => require(path.join(root,'web/src/i18n',locale === 'en' ? 'en.json' : `locales/${locale}.json`));
const english = dictionary('en');
const stage = process.argv[2] || 'matrix';
const revision = cp.execFileSync('git',['rev-parse','HEAD'],{cwd:root,encoding:'utf8'}).trim();
const sourceDiff = crypto.createHash('sha256').update(cp.execFileSync('git',['diff','HEAD','--','web'],{cwd:root})).digest('hex');
fs.mkdirSync(out,{recursive:true});
const results = [], consoleIssues = [], inventories = [], equivalence = [];
async function check(locale, name, fn) {
  try { const evidence = await fn(); results.push({locale,name,status:'PASS',evidence}); console.log('PASS',locale,name); }
  catch (error) { results.push({locale,name,status:'FAIL',error:error.stack}); console.log('FAIL',locale,name,error.message); }
}
async function select(page,locale) { await page.locator('#app-language').selectOption(locale); await page.waitForFunction(l => document.documentElement.lang === l,locale); if (await page.locator('.detail-overview').count()) await page.locator(`#agent-research-guide[lang="${locale}"]`).waitFor(); }
async function ready(page,route) {
  await page.goto(base + route); await page.locator('h1').waitFor();
  if (route === '/trace') await page.locator('.trace-event-disclosure').waitFor();
  if (route.includes('/ticker/')) await page.locator('#agent-research-guide').waitFor();
}
async function expand(page) {
  // Repeat a bounded number of times because measurement children mount on toggle.
  for (let round=0; round<3; round++) {
    for (const details of await page.locator('main details:not([open])').all()) {
      const summary=details.locator(':scope > summary');
      if (await summary.isVisible()) await summary.click();
    }
  }
  for (const button of await page.locator('.chart-figure > button').all()) {
    if (await button.getAttribute('aria-expanded') === 'false') await button.click();
  }
}
function speechDouble({unsupported=false,empty=false,chineseOnly=false,delayed=false,eventless=false}={}) {
  if (unsupported) { Object.defineProperty(window,'speechSynthesis',{configurable:true,value:undefined}); return; }
  const events = new EventTarget();
  const make = langs => langs.map(lang => ({lang,voiceURI:lang,name:`Mock ${lang}`,localService:true}));
  const voices=make(chineseOnly ? ['zh-CN','zh-TW'] : ['en-US','zh-CN','zh-TW','es-ES','es-MX','fr-FR','de-DE','pt-BR','pt-PT','ja-JP','ko-KR','cs-CZ','ar-SA','ar-EG']);
  window.__speech={calls:[],cancels:0,pauses:0,resumes:0,voices:empty||delayed?[]:voices,current:null,paused:false};
  window.SpeechSynthesisUtterance=class { constructor(text){this.text=text;} };
  Object.defineProperty(window,'speechSynthesis',{configurable:true,value:{
    getVoices:()=>[...window.__speech.voices],get paused(){return window.__speech.paused;},
    addEventListener:(...args)=>events.addEventListener(...args),removeEventListener:(...args)=>events.removeEventListener(...args),
    speak(u){window.__speech.current=u;window.__speech.calls.push({text:u.text,lang:u.lang,voice:u.voice?.voiceURI});if(!window.__speech.paused)u.onstart?.();},
    cancel(){window.__speech.cancels++;},pause(){window.__speech.pauses++;window.__speech.paused=true;},resume(){window.__speech.resumes++;window.__speech.paused=false;}
  }});
  window.__updateVoices=(langs)=>{window.__speech.voices=make(langs);events.dispatchEvent(new Event('voiceschanged'));};
  if (delayed) setTimeout(()=>{window.__speech.voices=voices;if(!eventless)events.dispatchEvent(new Event('voiceschanged'));},450);
}
async function newLocale(browser,locale,options={}) {
  const c=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
  await c.addInitScript(({locale})=>localStorage.setItem('tradepulse.locale',locale),{locale});
  if (options.speech) await c.addInitScript(speechDouble,options.speech);
  const p=await c.newPage();p.setDefaultTimeout(14000);
  return {c,p};
}
(async()=>{
  const browser=await chromium.launch({executablePath:process.env.TRADEPULSE_CHROMIUM||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
  const guide=Object.fromEntries(locales.map(locale=>[locale,require(path.join(root,`web/src/components/agentResearch/locales/${locale}.json`))]));
  let nativeSpeech;
  try {
    const native=await browser.newPage();await native.goto(base+'/discover');await native.locator('h1').waitFor();
    nativeSpeech=await native.evaluate(()=>({api:!!window.speechSynthesis,voices:window.speechSynthesis?.getVoices().map(v=>({name:v.name,lang:v.lang}))||[],audioHeard:false}));await native.close();
    for (const locale of locales) {
      const t=k=>dictionary(locale)[k]??k;
      if (stage === 'matrix') {
        const {c,p}=await newLocale(browser,locale);
        p.on('pageerror',e=>consoleIssues.push({locale,error:e.message}));p.on('console',m=>{if(['warning','error'].includes(m.type()))consoleIssues.push({locale,type:m.type(),error:m.text()});});
        const simpleTexts={};
        for (const [name,route] of routes) for (const mode of ['simple','pro']) {
          await ready(p,route);
          await p.getByRole('button',{name:t(mode === 'pro'?'Pro View':'Simple View'),exact:true}).click();
          await expand(p);
          const text=await p.locator('main').innerText();
          const textFile=path.join(out,revision.slice(0,7),locale,`${name}-${mode}.txt`);fs.mkdirSync(path.dirname(textFile),{recursive:true});fs.writeFileSync(textFile,text);
          if(mode==='simple')simpleTexts[name]=text;else equivalence.push({locale,route,expandedMainTextIdentical:simpleTexts[name]===text,interpretation:'Compare recorded content; mode-specific introductions and visualizations may differ. Data parity is tested independently.'});
          for (const width of [1440,768,320]) await check(locale,`${name}/${width}/${mode}`,async()=>{
            await p.setViewportSize({width,height:1000});await p.evaluate(()=>window.scrollTo(0,0));
            await p.waitForFunction(() => !document.querySelector('.chart-figure .skeleton') && [...document.querySelectorAll('.chart-figure')].every(figure => figure.querySelector('canvas')) && [...document.querySelectorAll('.echarts-for-react canvas')].filter(canvas => canvas.getClientRects().length).every(canvas => Math.abs(parseFloat(canvas.style.width) - canvas.closest('.echarts-for-react').clientWidth) < 2));
            const inventory=await p.evaluate(({english,localized})=>{
              const visible=e=>!!e.getClientRects().length&&getComputedStyle(e).visibility!=='hidden'&&!e.closest('[aria-hidden=true]');
              const tables=[...document.querySelectorAll('main table')].filter(visible).map(e=>({caption:e.caption?.textContent,headers:[...e.querySelectorAll('thead th')].map(h=>({text:h.textContent,scope:h.scope})),region:e.closest('[role=region]')?.getAttribute('aria-label')}));
              const unnamed=[...document.querySelectorAll('input,select,button')].filter(visible).filter(e=>!e.getAttribute('aria-label')&&!e.labels?.length&&!e.textContent.trim()).map(e=>e.outerHTML);
              const residual=[];const walker=document.createTreeWalker(document.querySelector('main'),NodeFilter.SHOW_TEXT);while(walker.nextNode()){const n=walker.currentNode,p=n.parentElement,v=n.textContent.trim();if(!p||!v||!visible(p)||p.closest('.original-source,[translate=no],pre,code,bdi,script,style,option'))continue;if(Object.hasOwn(english,v)&&localized[v]!=null&&localized[v]!==v)residual.push(v);}
              return {rootWidth:document.documentElement.scrollWidth,bodyWidth:document.body.scrollWidth,viewport:innerWidth,h1:document.querySelectorAll('h1').length,tables,unnamed,residual,charts:[...document.querySelectorAll('.chart-figure')].map(e=>({label:e.querySelector('[role=img]')?.getAttribute('aria-label'),caption:e.querySelector('figcaption')?.textContent})),lang:document.documentElement.lang,dir:document.documentElement.dir};
            },{english,localized:dictionary(locale)});
            assert(inventory.rootWidth<=width&&inventory.bodyWidth<=width,'page overflow');assert.equal(inventory.h1,1);assert.equal(inventory.lang,locale);assert.equal(inventory.dir,locale==='ar'?'rtl':'ltr');assert.deepEqual(inventory.unnamed,[]);assert.deepEqual(inventory.residual,[]);
            assert(inventory.tables.every(x=>x.caption?.trim()&&x.headers.every(h=>h.scope==='col')),'caption/header missing');
            assert(inventory.charts.every(x=>x.label?.trim()&&x.caption?.trim()),'chart lacks text alternative');
            const language=await p.locator('#app-language').boundingBox();assert(language.x>=0&&language.x+language.width<=width&&language.y+language.height<=1000,'selector not immediately visible');
            const screenshot=path.join(revision.slice(0,7),locale,name,String(width),`${mode}.png`);fs.mkdirSync(path.dirname(path.join(out,screenshot)),{recursive:true});
            await p.screenshot({path:path.join(out,screenshot),animations:'disabled'});
            await p.screenshot({path:path.join(out,screenshot.replace('.png','.full.png')),fullPage:true,animations:'disabled'});
            const businessScreenshot=screenshot.replace('.png','.business.png');
            await p.evaluate(()=>document.querySelector('.page-title')?.scrollIntoView({block:'start'}));
            await p.screenshot({path:path.join(out,businessScreenshot),animations:'disabled'});
            const chartScreenshots=[];
            if(width===320 && mode==='pro'){
              const figures=await p.locator('.chart-figure').all();
              for(let i=0;i<figures.length;i++){
                const file=screenshot.replace('.png',`.chart-${i+1}.png`);
                await figures[i].screenshot({path:path.join(out,file),animations:'disabled'});chartScreenshots.push(file);
              }
              if(name==='detail') await p.locator('#guide-speech-panel').screenshot({path:path.join(out,screenshot.replace('.png','.speech.png'))});
            }
            inventories.push({locale,name,route,width,mode,screenshot,businessScreenshot,chartScreenshots,...inventory,screenshotInspection:'NOT YET REVIEWED'});
            return {screenshot,tables:inventory.tables.length,charts:inventory.charts.length};
          });
        }
        await check(locale,'200% text enlargement on every route at 768px (not native browser zoom)',async()=>{
          for(const [,route]of routes){await ready(p,route);await p.evaluate(()=>document.documentElement.style.fontSize='200%');await p.setViewportSize({width:768,height:1000});assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await p.screenshot({path:path.join(out,revision.slice(0,7),locale,`text-200-${route.split('/')[1]}.png`)});await p.evaluate(()=>document.documentElement.style.fontSize='');}return {routes:7,nativeBrowserZoom:'NOT TESTED'};
        });
        await c.close();
      }
      if (stage === 'states') {
        const {c,p}=await newLocale(browser,locale,{speech:{}});
        await check(locale,'initial load, persisted locale, navigation, filters and empty results',async()=>{
          await ready(p,'/discover');assert.equal(await p.locator('#app-language').inputValue(),locale);assert(await p.locator('#app-language').isVisible());await p.reload();await p.locator('h1').waitFor();assert.equal(await p.locator('#app-language').inputValue(),locale);
          await p.locator('.navigation a[href="/pool/us_equity"]').click();await p.getByRole('searchbox').fill('SYN369');await p.getByLabel(t('Sector'),{exact:true}).selectOption(fixture.recommendations.find(x=>x.symbol==='SYN369').sector);
          const url=p.url();await p.getByRole('button',{name:t('Pro View'),exact:true}).click();await p.getByRole('button',{name:t('Simple View'),exact:true}).click();assert.equal(p.url(),url);
          await select(p,locale==='en'?'cs':'en');await select(p,locale);assert.equal(p.url(),url);assert.equal(await p.getByRole('searchbox').inputValue(),'SYN369');
          await p.getByRole('searchbox').fill('UNKNOWN_NO_MATCH');await p.getByRole('heading',{name:t('No instruments match your filters'),exact:true}).waitFor();await p.getByRole('button',{name:t('Clear all filters'),exact:true}).click();await p.locator('.candidate-card').first().waitFor();assert(await p.locator('.candidate-card').count()>0);
          return {preference:locale,searchAndFiltersPreserved:true};
        });
        await check(locale,'rapid Factor Lab pool and status changes retain both filters',async()=>{
          await ready(p,'/factors');await p.locator('.factor-card').first().waitFor();
          await p.getByRole('combobox',{name:t('Asset pool'),exact:true}).selectOption('crypto');
          await p.getByRole('combobox',{name:t('Factor status'),exact:true}).selectOption('ACTIVE');
          const expected=fixture.factor_cards.filter(x=>x.pool==='crypto'&&x.status==='ACTIVE').length;
          await p.waitForFunction(count=>document.querySelectorAll('.factor-card').length===count,expected);
          const params=new URL(p.url()).searchParams;assert.equal(params.get('pool'),'crypto');assert.equal(params.get('status'),'ACTIVE');
          assert.equal(await p.locator('.gate-chip').count(),expected*5);return {pool:'crypto',status:'ACTIVE',cards:expected};
        });
        await check(locale,'SYN369 original verdict, source evidence, missing explanation and invalid ticker',async()=>{
          await ready(p,'/ticker/us_equity/SYN369');await expand(p);
          const source=fixture.explanations.find(x=>x.symbol==='SYN369');const content=await p.locator('#explanation').textContent();
          for(const claim of source.claims){assert(content.includes(claim.text));for(const ev of claim.evidence)for(const k of ['evidence_id','rows_sha256','as_of','source_table','query_template'])assert(content.includes(ev[k]));}
          assert((await p.locator('#agent-research-guide').innerText()).includes('"abstained"'));assert((await p.locator('#agent-research-guide').innerText()).includes(guide[locale].temporal));assert((await p.locator('#agent-research-guide').innerText()).includes(guide[locale].synthetic));
          const absent=fixture.recommendations.find(x=>!x.explanation_id);await ready(p,`/ticker/${absent.pool}/${absent.symbol}`);assert((await p.locator('#explanation').innerText()).includes(t('No explanation recorded')));
          await p.goto(base+'/ticker/us_equity/UNKNOWN');await p.getByRole('heading',{name:t('Instrument not found'),level:1,exact:true}).waitFor();assert.equal(await p.locator('#agent-research-guide').count(),0);return {originalVerdict:source.verdict};
        });
        await check(locale,'keyboard Listen entry, all speech controls, stop recovery, error, route cancellation',async()=>{
          await ready(p,'/ticker/us_equity/SYN369');const button=k=>p.getByRole('button',{name:guide[locale][k],exact:true});
          assert.equal(await p.evaluate(()=>window.__speech.calls.length),0);
          const entry=p.getByRole('button',{name:t('Listen to this explanation'),exact:true});await entry.focus();await p.keyboard.press('Enter');assert.equal(await p.evaluate(()=>document.activeElement.id),'guide-speech-title');assert.equal(await p.evaluate(()=>window.__speech.calls.length),0);
          await button('play').click();assert.equal(await p.evaluate(()=>window.__speech.calls.length),1);const call=await p.evaluate(()=>window.__speech.calls[0]);assert(call.text.includes('abstained'));assert(call.text.includes(guide[locale].synthetic));assert(!call.text.includes('A linked supplier'));
          await button('pause').click();assert(await button('resume').isEnabled());await button('resume').click();await button('pause').click();await button('stop').click();await button('play').click();assert.equal(await p.evaluate(()=>window.__speech.paused),false);
          await p.evaluate(()=>window.__speech.current.onerror?.({error:'test-only'}));await p.waitForFunction(text=>document.querySelector('#agent-research-guide [role=status]').textContent.includes(text),guide[locale].error);assert((await p.locator('#agent-research-guide [role=status]').innerText()).includes(guide[locale].error));assert(await button('play').isEnabled());
          await button('play').click();const count=await p.evaluate(()=>window.__speech.cancels);await select(p,locale==='en'?'fr':'en');assert(await p.evaluate(()=>window.__speech.cancels)>count);assert.equal(await p.evaluate(()=>window.__speech.calls.length),3);await select(p,locale);
          await button('play').click();const before=await p.evaluate(()=>window.__speech.cancels);await p.locator('.hero-actions a[href="/discover"]').click();await p.waitForURL('**/discover');await p.getByRole('heading',{name:t('Make sense of the market.'),exact:true}).waitFor();await p.waitForFunction(value=>window.__speech.cancels>value,before);assert(await p.evaluate(()=>window.__speech.cancels)>before);
          return {mockVoice:call.lang,audioHeard:false,noAutoplay:true};
        });
        await check(locale,'reduced motion and keyboard disclosure/selector operability',async()=>{
          await ready(p,'/ticker/us_equity/SYN369');assert(await p.evaluate(()=>matchMedia('(prefers-reduced-motion: reduce)').matches));const summary=p.locator('#agent-research-guide > details').nth(1).locator('summary');await summary.focus();const before=await summary.evaluate(e=>e.parentElement.open);await p.keyboard.press('Enter');assert.notEqual(await summary.evaluate(e=>e.parentElement.open),before);assert.notEqual(await summary.evaluate(e=>getComputedStyle(e).outlineWidth),'0px');
          await p.locator('#app-language').focus();await p.keyboard.press('Home');await p.keyboard.press('Enter');assert.equal(await p.locator('#app-language').inputValue(),'en');await select(p,locale);return {keyboard:true,reducedMotion:true};
        });await c.close();
        for(const config of[{unsupported:true},{empty:true},{chineseOnly:true},{delayed:true},{delayed:true,eventless:true}])await check(locale,`voice availability ${JSON.stringify(config)}`,async()=>{
          const {c,p}=await newLocale(browser,locale,{speech:config});await ready(p,'/ticker/us_equity/SYN369');const play=p.getByRole('button',{name:guide[locale].play,exact:true});
          if(config.unsupported){assert((await p.locator('#agent-research-guide').innerText()).includes(guide[locale].unsupported));assert.equal(await play.count(),0);}
          else if(config.empty||(config.chineseOnly&&!locale.startsWith('zh-'))){assert(await play.isDisabled());assert((await p.locator('#agent-research-guide').innerText()).includes(guide[locale].voiceMissing));assert.equal(await p.evaluate(()=>window.__speech.calls.length),0);}
          else{await p.waitForFunction(()=>!document.querySelector('#agent-research-guide button.primary').disabled);assert.equal(await p.evaluate(()=>window.__speech.calls.length),0);await play.click();const lang=await p.evaluate(()=>window.__speech.calls.at(-1).lang);assert(locale.includes('-')?lang===locale:lang.split('-')[0]===locale);}
          const voices=config.unsupported?[]:await p.evaluate(()=>window.__speech.voices.map(v=>v.lang));await c.close();return {mock:config,voices,audioHeard:false};
        });
        // Each locale starts independently in its persisted language for every API scenario.
        for(const scenario of ['loading','HTTP503','malformed','empty','missing-evidence','summary-only-abstention'])await check(locale,`API ${scenario}`,async()=>{
          const {c,p}=await newLocale(browser,locale);let release;const gate=new Promise(r=>{release=r;});const requests=[];
          const output=structuredClone(fixture);
          if(scenario==='empty'){output.recommendations=[];output.explanations=[];output.factor_cards=[];output.regimes=[];}
          if(scenario==='missing-evidence')for(const explanation of output.explanations)for(const claim of explanation.claims)claim.evidence=[];
          if(scenario==='summary-only-abstention')output.explanations.find(x=>x.symbol==='SYN369').claims=[];
          await c.route(`${api}/**`,async r=>{requests.push({url:r.request().url(),method:r.request().method()});if(scenario==='loading')await gate;await r.fulfill({status:scenario==='HTTP503'?503:200,contentType:'application/json',headers:{'Access-Control-Allow-Origin':'*'},body:JSON.stringify(r.request().url().endsWith('/trace')?(scenario==='empty'?[]:trace):scenario==='malformed'?{unknown:true}:output)});});
          await p.goto(apiBase+(['missing-evidence','summary-only-abstention'].includes(scenario)?'/ticker/us_equity/SYN369':'/discover'));
          if(scenario==='loading'){await p.getByRole('status').filter({hasText:t('Loading research data…')}).waitFor();assert((await p.locator('main').innerText()).includes(t('Loading research data…')));assert.equal(await p.locator('#app-language').inputValue(),locale);release();await p.locator('h1').waitFor();}
          else if(['HTTP503','malformed'].includes(scenario)){await p.getByRole('alert').waitFor();assert((await p.getByRole('alert').innerText()).includes(t('Research data is unavailable')));assert(await p.getByRole('button',{name:t('Retry'),exact:true}).isEnabled());assert.equal(await p.locator('.mode-banner.warning').count(),0);}
          else if(scenario==='empty'){await p.locator('h1').waitFor();for(const [route,label]of[['/pool/us_equity','No instruments match your filters'],['/factors','No factor cards match this selection'],['/regime','Regime data unavailable'],['/trace','No trace events recorded']]){await p.goto(apiBase+route);await p.getByRole('heading',{name:t(label),exact:true}).waitFor();}}
          else if(scenario==='summary-only-abstention'){await p.locator('#agent-research-guide').waitFor();await expand(p);const source=output.explanations.find(x=>x.symbol==='SYN369');const text=await p.locator('#agent-research-guide > details').last().innerText();assert(text.includes(source.summary));assert(text.includes(guide[locale].noReason));assert(text.includes('abstained'));}
          else {await p.locator('#explanation').waitFor();await expand(p);assert.equal(await p.locator('.evidence').count(),0);assert((await p.locator('#explanation').innerText()).includes(t('No evidence reference supplied.')));}
          assert(requests.every(r=>r.method==='GET'));await c.close();return {scenario,requests,simulated:true};
        });
      }
    }
    if(stage==='matrix')await check('all','normal console clean',async()=>assert.deepEqual(consoleIssues,[]));
  } finally {
    fs.writeFileSync(path.join(out,`${stage}-results.json`),JSON.stringify({revision,sourceDiff,browser:browser.version(),stage,nativeSpeech,results,consoleIssues,inventories,equivalence},null,2));await browser.close();
  }
  console.log(`${results.filter(r=>r.status==='PASS').length}/${results.length} ${stage} checks passed`);process.exitCode=results.some(r=>r.status==='FAIL')?1:0;
})().catch(e=>{console.error(e);process.exitCode=1;});
