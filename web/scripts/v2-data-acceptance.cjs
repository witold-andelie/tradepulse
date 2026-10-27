// Optional existing browser runtime. Source-data parity acceptance for the integrated V2.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '../..');
const out = path.resolve(process.env.TRADEPULSE_QA_DIR || '/tmp/tradepulse-v2-data'); fs.mkdirSync(out,{recursive:true});
const base = process.env.TRADEPULSE_PREVIEW_URL || 'http://127.0.0.1:5234';
const fixture = require(path.join(root, 'contracts/fixtures/run_output.fixture.json'));
const locales = ['en','zh-CN','zh-TW','es','fr','de','pt-BR','ja','ko','cs','ar'];
const dictionary = (locale) => require(path.join(root, 'web/src/i18n', locale === 'en' ? 'en.json' : `locales/${locale}.json`));
const tiers = { STRONG_OVERWEIGHT:'Strong overweight', OVERWEIGHT:'Overweight', NEUTRAL:'Neutral', UNDERWEIGHT:'Underweight', AVOID:'Avoid', NO_CALL:'No call' };
const score = (value) => Number.isFinite(value) ? `${value > 0 ? '+' : ''}${value.toFixed(2)}` : '—';
const bps = (value) => Number.isFinite(value) ? `${value > 0 ? '+' : ''}${value.toFixed(1)} bp` : '—';
const pct = (value) => Number.isFinite(value) ? `${(value * 100).toFixed(1)}%` : '—';
const results=[], findings=[], semantics=[], residuals=[], snapshots=[], errors=[];
const paths = [['discover','/discover'],['leaderboard','/pool/us_equity'],['detail','/ticker/us_equity/SYN369'],['factors','/factors'],['regime','/regime'],['track-record','/track-record'],['trace','/trace']];
const screenshots = new Set();
async function check(name, fn) { try { const count=await fn(); results.push({name,status:'PASS',count}); console.log('PASS',name,count??''); } catch(error) { results.push({name,status:'FAIL',error:error.stack}); console.log('FAIL',name,error.message); } }
async function navigate(page, route) { await page.goto(base+route); await page.locator('h1').waitFor(); if(route==='/trace') await page.locator('.trace-event-disclosure').waitFor(); if(route.startsWith('/ticker/') && await page.locator('.detail-overview').count()) await page.locator('#agent-research-guide').waitFor(); }
async function expand(page) {
  const details=page.locator('main details'); const count=await details.count();
  for(let i=0;i<count;i++){ const node=details.nth(i); if(await node.getAttribute('open')===null && await node.locator(':scope > summary').isVisible()) await node.locator(':scope > summary').click(); }
  await page.waitForTimeout(40);
}
async function choose(page,locale) { await page.locator('#app-language').selectOption(locale); await page.waitForFunction((locale)=>document.documentElement.lang===locale,locale); if(await page.locator('.detail-overview').count()) await page.locator(`#agent-research-guide[lang="${locale}"]`).waitFor(); }
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
 const guide=Object.fromEntries(locales.map(locale=>[locale,require(path.join(root,`web/src/components/agentResearch/locales/${locale}.json`))]));
 try {
 for(const locale of locales){
  const context=await browser.newContext({viewport:{width:1440,height:1000}});await context.addInitScript(()=>localStorage.setItem('tradepulse.view','pro'));
  const page=await context.newPage();page.setDefaultTimeout(15000);page.on('pageerror',e=>errors.push({locale,error:e.message}));page.on('console',m=>{if(['error','warning'].includes(m.type()))errors.push({locale,error:m.text()})});
  const t=(key)=>dictionary(locale)[key]??key;
  await check(`${locale}: immediate Discover selector and preference`,async()=>{
   await navigate(page,'/discover');assert.equal(await page.locator('#app-language').inputValue(),'en');
   const box=await page.locator('#app-language').boundingBox();assert(box && box.y>=0 && box.y+box.height<=1000);await choose(page,locale);
   assert.equal(await page.locator('html').getAttribute('dir'),locale==='ar'?'rtl':'ltr');assert.equal(await page.evaluate(()=>localStorage.getItem('tradepulse.locale')),locale);
   await page.reload();await page.locator('h1').waitFor();assert.equal(await page.locator('#app-language').inputValue(),locale);return 1;
  });
  await check(`${locale}: all 620 instrument rows, every pool and financial table value`,async()=>{
   let inspected=0;
   for(const pool of fixture.pools){
    const expected=fixture.recommendations.filter(r=>r.pool===pool.pool).sort((a,b)=>a.rank-b.rank);
    await navigate(page,`/pool/${pool.pool}?sort=rank&dir=asc`);
    const badge=await page.locator('.page-title > .badge').evaluate(e=>({text:e.textContent,classes:e.className,color:getComputedStyle(e).color,background:getComputedStyle(e).backgroundColor}));
    snapshots.push({locale,pool:pool.pool,sourceState:pool.regime_state,badge});
    if(!badge.classes.split(/\s+/).includes(`tone-${pool.regime_state}`))findings.push({id:'regime-badge-tone',locale,pool:pool.pool,sourceState:pool.regime_state,...badge});
    for(let index=0;index<Math.ceil(expected.length/50);index++){
     const segment=expected.slice(index*50,index*50+50);await page.waitForFunction((symbol)=>document.querySelector('.leaderboard tbody a.symbol')?.firstChild?.textContent===symbol,segment[0].symbol);
     const actual=await page.locator('.leaderboard tbody tr').evaluateAll(rows=>rows.map(row=>({symbol:row.querySelector('a.symbol').firstChild.textContent,cells:[...row.querySelectorAll('td')].map(cell=>cell.textContent)})));
     assert.equal(actual.length,segment.length);
     for(let i=0;i<segment.length;i++){
      const source=segment[i],row=actual[i];assert.equal(row.symbol,source.symbol);assert.equal(row.cells[0],String(source.rank));
      assert.equal(row.cells[3],t(tiers[source.tier]));
      assert.deepEqual(row.cells.slice(4),[score(source.score),bps(source.net_edge_bps),bps(source.expected_alpha_bps),pct(source.coverage),pct(source.ret_1d)]);
      inspected++;
     }
     if(index+1<Math.ceil(expected.length/50))await page.getByRole('button',{name:t('Next →'),exact:true}).click();
    }
   }
   return inspected;
  });
  await check(`${locale}: all 30 original explanations, verdicts, evidence and detail measurements`,async()=>{
   let inspected=0;
   for(const explanation of fixture.explanations){
    const source=fixture.recommendations.find(r=>r.symbol===explanation.symbol&&r.pool===explanation.pool);
    await navigate(page,`/ticker/${source.pool}/${source.symbol}`);await page.locator('#agent-research-guide').waitFor();
    for(const node of await page.locator('#agent-research-guide > details').all())if(await node.getAttribute('open')===null)await node.locator(':scope > summary').click();
    const ids=await page.locator('#agent-research-guide bdi').allTextContents();assert(ids.includes(JSON.stringify(explanation.verdict)));assert(ids.includes(source.tier));
    const metrics=await page.locator('#measurements .metrics dd').allTextContents();assert.equal(metrics.length,8);
    assert.equal(metrics[1],score(source.score));assert.equal(metrics[2],bps(source.expected_alpha_bps));assert.equal(metrics[3],bps(source.net_edge_bps));assert.equal(metrics[4],bps(source.cost_bps_round_trip));assert.equal(metrics[5],pct(source.coverage));
    assert.deepEqual(metrics[0].match(/\d+/g).map(Number),[source.rank,fixture.recommendations.filter(r=>r.pool===source.pool).length]);
    const claimNodes=page.locator('#explanation .claim');assert.equal(await claimNodes.count(),explanation.claims.length);
    for(const claim of explanation.claims){
     const node=claimNodes.filter({hasText:claim.text});assert(await node.evaluate((e,status)=>e.classList.contains(status),claim.status));
     if(await node.getAttribute('open')===null)await node.locator(':scope > summary').click();
     assert((await node.textContent()).includes(claim.claim_id));assert((await node.textContent()).includes(claim.text));
     assert.equal(await node.locator('.evidence').count(),claim.evidence.length);
     for(let e=0;e<claim.evidence.length;e++){
      const evidence=claim.evidence[e],rendered=node.locator('.evidence').nth(e),text=await rendered.textContent();
      for(const key of ['evidence_id','query_template','source_table','rows_sha256','as_of'])assert(text.includes(evidence[key]));
      assert.deepEqual(JSON.parse(await rendered.locator('pre').textContent()),evidence.params);
     }
     for(const gate of claim.checks)assert((await node.textContent()).includes(gate.detail));
    }
    inspected++;
   }
   return inspected;
  });
  await check(`${locale}: NO_CALL, absent explanation, rejected evidence and educational caveats`,async()=>{
   const row=fixture.recommendations.find(r=>r.tier==='NO_CALL');await navigate(page,`/ticker/${row.pool}/${row.symbol}`);
   assert((await page.locator('main').innerText()).includes(t('No call — the source run records no directional research stance. No specific reason code is supplied for this instrument. Inspect coverage, pool IC and the available explanation; no stance has been inferred.')));
   const absent=fixture.recommendations.find(r=>!r.explanation_id);await navigate(page,`/ticker/${absent.pool}/${absent.symbol}`);
   assert((await page.locator('#explanation').innerText()).includes(t('No explanation recorded')));
   await navigate(page,'/ticker/us_equity/SYN369');assert((await page.locator('#agent-research-guide').innerText()).includes(guide[locale].temporal));return 3;
  });
  await check(`${locale}: expanded seven routes, semantic inventory, both-view reflow and residual English`,async()=>{
   let cases=0;
   for(const [name,route]of paths){
    await page.setViewportSize({width:1440,height:1000});await navigate(page,route);await expand(page);
    if(route==='/regime'||route==='/track-record'||route==='/trace')for(const b of await page.locator('.chart-figure > button').all())if(await b.getAttribute('aria-expanded')==='false')await b.click();
    const inventory=await page.evaluate(()=>{
     const visible=e=>!!e.getClientRects().length&&getComputedStyle(e).visibility!=='hidden'&&!e.closest('[aria-hidden=true]');
     const tables=[...document.querySelectorAll('table')].filter(visible).map(e=>({classes:e.className,caption:e.querySelector('caption')?.textContent??null,ariaLabel:e.getAttribute('aria-label'),ariaLabelledby:e.getAttribute('aria-labelledby'),region:e.closest('[role=region]')?.getAttribute('aria-label'),headers:[...e.querySelectorAll('thead th')].map(h=>({text:h.textContent,scope:h.scope})),rows:e.tBodies[0]?.rows.length}));
     const english=[];const walker=document.createTreeWalker(document.querySelector('main'),NodeFilter.SHOW_TEXT);while(walker.nextNode()){const n=walker.currentNode,p=n.parentElement,v=n.textContent.trim();if(!p||!v||!visible(p)||p.closest('.original-source,[translate=no],pre,code,bdi,script,style,option'))continue;if(/[A-Za-z]{3,}/.test(v))english.push({text:v,tag:p.tagName,classes:p.className});}
     const charts=[...document.querySelectorAll('.chart-figure')].map(e=>({label:e.querySelector('[role=img]')?.getAttribute('aria-label'),caption:e.querySelector('figcaption')?.textContent,tableToggle:!!e.querySelector(':scope > button'),axes:e.querySelector('.chart-axis-labels')?.textContent}));
     const unnamed=[...document.querySelectorAll('input,select,button')].filter(visible).filter(e=>!e.getAttribute('aria-label')&&!e.labels?.length&&!e.textContent.trim()).map(e=>e.outerHTML.slice(0,120));
     return{tables,english,charts,unnamed,h1:document.querySelectorAll('h1').length};
    });
    semantics.push({locale,route,...inventory});assert.equal(inventory.h1,1);assert.deepEqual(inventory.unnamed,[]);assert(inventory.charts.every(c=>c.label?.trim()&&c.caption?.trim()));
    if(locale!=='en')for(const item of inventory.english){const translated=dictionary(locale)[item.text];if(translated&&translated!==item.text)residuals.push({locale,route,...item});}
    for(const view of['pro','simple']){
     await page.getByRole('button',{name:t(view==='pro'?'Pro View':'Simple View'),exact:true}).click();
     for(const width of[320,390,768,1024,1440]){
      await page.setViewportSize({width,height:1000});await page.waitForTimeout(15);
      const size=await page.evaluate(()=>({root:document.documentElement.scrollWidth,body:document.body.scrollWidth,width:innerWidth}));
      assert(size.root<=width&&size.body<=width,`${locale}/${route}/${view}/${width}: ${JSON.stringify(size)}`);cases++;
      if(screenshots.has(locale)&&view==='pro'&&[320,1024].includes(width)){await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:path.join(out,`expanded-${locale}-${name}-${width}.png`)});}
     }
    }
   }
   return cases;
  });
  await context.close();
 }
 await check('exact English residuals outside protected source/canonical content',async()=>{assert.deepEqual(residuals,[]);return residuals.length;});
 await check('no normal-journey console errors',async()=>{assert.deepEqual(errors,[]);return errors.length;});
 }finally{await browser.close();fs.writeFileSync(path.join(out,'independent-results.json'),JSON.stringify({results,findings,semantics,residuals,snapshots,errors},null,2));}
 console.log(`${results.filter(r=>r.status==='PASS').length}/${results.length} independent groups passed`);process.exitCode=results.some(r=>r.status==='FAIL')?1:0;
})().catch(e=>{console.error(e);process.exitCode=1});
