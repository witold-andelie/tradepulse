// Optional, separately installed audit tools are supplied by path. Project dependencies stay unchanged.
const { chromium } = require('playwright');
const fs = require('node:fs');const path = require('node:path');const cp = require('node:child_process');const crypto = require('node:crypto');const assert = require('node:assert/strict');
const root=path.resolve(__dirname,'../..');const base=process.env.TRADEPULSE_PREVIEW_URL||'http://127.0.0.1:5234';const out=path.resolve(process.env.TRADEPULSE_QA_DIR||'/tmp/tradepulse-v2-accessibility');fs.mkdirSync(out,{recursive:true});
const locales=(process.env.TRADEPULSE_LOCALES||'en,zh-CN,zh-TW,es,fr,de,pt-BR,ja,ko,cs,ar').split(',');
const routes=[['discover','/discover'],['leaderboard','/pool/us_equity'],['detail','/ticker/us_equity/SYN369'],['factors','/factors'],['regime','/regime'],['track-record','/track-record'],['trace','/trace']];
const stage=process.argv[2]||'axe';const results=[];
async function ready(p,url){await p.goto(base+url);await p.locator('h1').waitFor();if(url.startsWith('/ticker/'))await p.locator('#agent-research-guide').waitFor();if(url==='/trace')await p.locator('.trace-event-disclosure').waitFor();}
async function expand(p){for(let n=0;n<120;n++){const d=p.locator('main details:not([open]) > summary');if(!await d.count())break;await d.first().click();}for(let n=0;n<40;n++){const b=p.locator('.chart-figure button[aria-expanded=false]');if(!await b.count())break;await b.first().click();}}
async function check(locale,name,fn){try{const evidence=await fn();results.push({locale,name,status:'PASS',evidence});console.log('PASS',locale,name)}catch(e){results.push({locale,name,status:'FAIL',error:e.stack});console.log('FAIL',locale,name,e.message)}}
(async()=>{
let browser,context;
try{
 if(stage==='axe'){
  assert(process.env.TRADEPULSE_AXE_PATH,'Provide TRADEPULSE_AXE_PATH from external audit tooling');
  browser=await chromium.launch({executablePath:process.env.TRADEPULSE_CHROMIUM||'/usr/bin/chromium',args:['--no-sandbox']});
  for(const locale of locales){const c=await browser.newContext({viewport:{width:320,height:1000},reducedMotion:'reduce'});await c.addInitScript(l=>localStorage.setItem('tradepulse.locale',l),locale);const p=await c.newPage();p.setDefaultTimeout(15000);
   for(const[name,url]of routes)for(const mode of['simple','pro'])await check(locale,`${name}/${mode}/axe`,async()=>{
    await ready(p,url);const dict=require(path.join(root,'web/src/i18n',locale==='en'?'en.json':`locales/${locale}.json`));await p.getByRole('button',{name:dict[mode==='pro'?'Pro View':'Simple View'],exact:true}).click();await expand(p);
    await p.addScriptTag({path:process.env.TRADEPULSE_AXE_PATH});const result=await p.evaluate(async()=>await axe.run(document,{resultTypes:['violations','incomplete']}));
    const raw=JSON.stringify(result);fs.writeFileSync(path.join(out,`${locale}-${name}-${mode}.axe.json`),raw);
    const evidence={version:result.testEngine.version,url:result.url,timestamp:result.timestamp,rawSha256:crypto.createHash('sha256').update(raw).digest('hex'),violations:result.violations,incomplete:result.incomplete.map(x=>({id:x.id,impact:x.impact,help:x.help,targets:x.nodes.map(n=>n.target)}))};
    assert.equal(result.violations.filter(v=>['critical','serious'].includes(v.impact)).length,0,'Critical/serious axe violations: '+result.violations.map(x=>x.id).join(','));return evidence;
   });await c.close();}
 }else if(stage==='lighthouse'){
  assert(process.env.TRADEPULSE_LIGHTHOUSE_PATH,'Provide TRADEPULSE_LIGHTHOUSE_PATH from external audit tooling');
  const {default:lighthouse}=await import(process.env.TRADEPULSE_LIGHTHOUSE_PATH);const port=Number(process.env.TRADEPULSE_LIGHTHOUSE_PORT||9340);const profile=fs.mkdtempSync('/tmp/tradepulse-v2-lighthouse-');
  context=await chromium.launchPersistentContext(profile,{executablePath:process.env.TRADEPULSE_CHROMIUM||'/usr/bin/chromium',viewport:null,args:['--no-sandbox',`--remote-debugging-port=${port}`]});
  const p=context.pages()[0];await ready(p,'/discover');
  for(const locale of locales)for(const width of[1440,320])await check(locale,`detail/${width}/lighthouse`,async()=>{
   await p.goto(base+'/discover');await p.evaluate(({locale,width})=>{localStorage.setItem('tradepulse.locale',locale);localStorage.setItem('tradepulse.view',width===320?'simple':'pro')},{locale,width});
   const {lhr}=await lighthouse(base+'/ticker/us_equity/SYN369',{port,onlyCategories:['accessibility'],disableStorageReset:true,formFactor:'desktop',screenEmulation:{mobile:false,width,height:1000,deviceScaleFactor:1,disabled:false},logLevel:'error'});
   const raw=JSON.stringify(lhr);fs.writeFileSync(path.join(out,`${locale}-${width}.lighthouse.json`),raw);
   const failed=Object.values(lhr.audits).filter(a=>a.score===0&&a.scoreDisplayMode!=='notApplicable').map(a=>({id:a.id,title:a.title,description:a.description,details:a.details}));const score=lhr.categories.accessibility.score*100;
   const evidence={version:lhr.lighthouseVersion,fetchTime:lhr.fetchTime,requestedUrl:lhr.requestedUrl,finalDisplayedUrl:lhr.finalDisplayedUrl,score,runWarnings:lhr.runWarnings,failedAudits:failed,rawSha256:crypto.createHash('sha256').update(raw).digest('hex')};
   assert(score>=95,'Lighthouse accessibility below 95: '+score);return evidence;
  });
 }else if(stage==='zoom'){
  // Browser-owned zoom settings change CSS layout and DPR. No viewport emulation,
  // CSS font enlargement, device-scale override, or page-scale emulation is used.
  for(const locale of locales){
   const profile=fs.mkdtempSync('/tmp/tradepulse-v2-native-zoom-');
   const c=await chromium.launchPersistentContext(profile,{executablePath:process.env.TRADEPULSE_CHROMIUM||'/usr/bin/chromium',viewport:null,args:['--no-sandbox','--window-size=1440,1000']});
   try{
    const p=c.pages()[0];p.setDefaultTimeout(15000);await ready(p,'/discover');
    const initial=await p.evaluate(()=>({outer:outerWidth,inner:innerWidth,dpr:devicePixelRatio,font:getComputedStyle(document.documentElement).fontSize,visualScale:visualViewport.scale}));
    assert.equal(initial.inner,1440);assert.equal(initial.dpr,1);
    await p.evaluate(l=>localStorage.setItem('tradepulse.locale',l),locale);
    const settings=await c.newPage();await settings.goto('chrome://settings/appearance');await settings.waitForFunction(()=>typeof chrome.settingsPrivate?.setDefaultZoom==='function');await settings.evaluate(async()=>await chrome.settingsPrivate.setDefaultZoom(2));await settings.close();
    const session=await c.newCDPSession(p);const{windowId}=await session.send('Browser.getWindowForTarget');
    const dictionary=require(path.join(root,'web/src/i18n',locale==='en'?'en.json':`locales/${locale}.json`));
    for(const outer of[1440,640]){
     await session.send('Browser.setWindowBounds',{windowId,bounds:{width:outer,height:1000,windowState:'normal'}});
     for(const[name,url]of routes)for(const mode of['simple','pro'])await check(locale,`${name}/${outer/2}/${mode}/native-200-percent`,async()=>{
      await ready(p,url);await p.getByRole('button',{name:dictionary[mode==='pro'?'Pro View':'Simple View'],exact:true}).click();
      await p.waitForFunction(w=>innerWidth===w&&devicePixelRatio===2,outer/2);
      const geometry=await p.evaluate(()=>({outer:outerWidth,inner:innerWidth,dpr:devicePixelRatio,font:getComputedStyle(document.documentElement).fontSize,visualScale:visualViewport.scale,root:document.documentElement.scrollWidth,body:document.body.scrollWidth,lang:document.documentElement.lang}));
      assert.equal(geometry.lang,locale);assert.equal(geometry.font,'16px');assert.equal(geometry.visualScale,1);assert(geometry.root<=geometry.inner&&geometry.body<=geometry.inner,'native zoom overflow');assert(await p.locator('#app-language').isVisible());
      if(outer===640&&mode==='simple'&&['discover','detail'].includes(name))await p.screenshot({path:path.join(out,`${locale}-${name}-native-200.png`)});
      return{method:'Chrome settingsPrivate.setDefaultZoom(2), viewport:null',before:initial,after:geometry};
     });
    }
   }finally{await c.close();}
  }
 }else throw Error('Unknown audit stage');
}finally{await context?.close();await browser?.close();fs.writeFileSync(path.join(out,'results.json'),JSON.stringify({stage,revision:cp.execFileSync('git',['rev-parse','HEAD'],{cwd:root,encoding:'utf8'}).trim(),results},null,2));}
console.log(results.filter(x=>x.status==='PASS').length+'/'+results.length);process.exitCode=results.some(x=>x.status==='FAIL')?1:0;
})().catch(e=>{console.error(e);process.exitCode=1});
