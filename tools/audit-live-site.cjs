/* Live-site browser audit: actual rendered DOM, axe, interactions and screen captures.
   Audit is read-only: no submissions, no logins, no recorded personal data. */
const fs=require('node:fs');
const path=require('node:path');
const {chromium}=require('playwright');
const AxeBuilder=require('@axe-core/playwright').default;
const OUT=path.resolve(process.env.AUDIT_OUT||'audit-output');
const ORIGIN=process.env.AUDIT_URL||'https://ai.k-bigdata.kr';
fs.mkdirSync(OUT,{recursive:true});
const pages=[
 ['home','/'],['activities','/activities/'],
 ['activity-page-2','/activities/page/2/'],
 ['projects','/projects/'],['admission','/admission/2027/'],
 ['employment','/employment/']
];
const devices=[
 ['desktop',{width:1440,height:900},false],
 ['mobile',{width:390,height:844},true],
 ['small-mobile',{width:360,height:780},true],
 ['tablet',{width:768,height:1024},true]
];
const findings=[],summary=[];
const safe=(str)=>String(str||'').slice(0,500);
const fail=(level,kind,location,details)=>findings.push({level,kind,location,details:safe(details)});
const capture=async(browser,name,uri,viewport,mobile)=>{
 const ctx=await browser.newContext({viewport,isMobile:mobile,deviceScaleFactor:1,locale:'ko-KR',reducedMotion:'reduce'});
 const page=await ctx.newPage();
 let networkErrors=[],jsErrors=[];
 page.on('pageerror',e=>jsErrors.push(safe(e.message)));
 page.on('response',r=>{if(r.status()>=400&&new URL(r.url()).hostname===new URL(ORIGIN).hostname)networkErrors.push({status:r.status(),url:safe(r.url())});});
 let ok=false;
 try {
  const res=await page.goto(ORIGIN+uri,{waitUntil:'domcontentloaded',timeout:45000});
  if(!res||res.status()>=400)throw Error('HTTP '+(res?.status()||'no response'));
  await page.waitForTimeout(1000);
  await page.evaluate(()=>{document.fonts?.ready.catch(()=>{});});
  const dom=await page.evaluate(()=>{
   const ids=[...document.querySelectorAll('[id]')].map(x=>x.id);
   const dup=ids.filter((x,i)=>ids.indexOf(x)!==i);
   const links=[...document.querySelectorAll('a[href]')];
   const main=document.querySelector('main');
   const header=document.querySelector('.site-header');
   const nav=document.querySelector('.main-nav');
   const navLinks=[...(nav?.querySelectorAll('a')||[])];
   const overflowing=[...document.querySelectorAll('body *')].filter(el=>{
     const r=el.getBoundingClientRect(),cs=getComputedStyle(el);
     return r.width>0&&r.right>innerWidth+4 && cs.position!=='fixed' &&
       !el.closest('[aria-hidden="true"]') && r.left<innerWidth;
   }).slice(0,12).map(el=>({tag:el.tagName,cls:String(el.className||'').slice(0,80),right:Math.round(el.getBoundingClientRect().right)}));
   const tiny=[...document.querySelectorAll('main p,main a,main li,main button')].filter(el=>{
     const css=getComputedStyle(el),r=el.getBoundingClientRect();
     return r.width>0&&r.height>0&&parseFloat(css.fontSize)<13;
   }).slice(0,20).map(el=>({tag:el.tagName,text:(el.textContent||'').trim().slice(0,40),px:getComputedStyle(el).fontSize}));
   return {
     title:document.title,lang:document.documentElement.lang,
     mainCount:document.querySelectorAll('main').length,
     h1Count:document.querySelectorAll('h1').length,
     nav:navLinks.map(el=>el.textContent.trim()),
     navVisible:nav?getComputedStyle(nav).display!=='none':false,
     bodyScrollWidth:document.documentElement.scrollWidth,viewportWidth:innerWidth,
     overflows:overflowing,duplicateIds:[...new Set(dup)],tiny,
     imagesWithoutAlt:document.querySelectorAll('img:not([alt])').length,
     brokenImages:[...document.images].filter(img=>img.complete&&img.naturalWidth===0).length,
     sectionOrder:[...document.querySelectorAll('main > section')].map(el=>el.id||el.className),
     links:links.length,
     videoPoster:document.querySelector('#campus-film video')?.getAttribute('poster')||null,
     mediaCards:document.querySelectorAll('.activity-card').length,
     menuButton:document.querySelector('.menu-toggle')?.getAttribute('aria-expanded')||null,
     hasCookieNotice:Boolean(document.querySelector('[class*=cookie],[id*=cookie]')),
     gaConfigured:Boolean(window.gtag&&window.dataLayer)
   };
  });
  const ident=name+' '+viewport.width+'px';
  if(dom.bodyScrollWidth>viewport.width+3)fail('high','horizontal-overflow',ident,dom.bodyScrollWidth+' > '+viewport.width);
  if(dom.duplicateIds.length)fail('high','duplicate-id',ident,dom.duplicateIds.join(', '));
  if(dom.imagesWithoutAlt)fail('medium','missing-alt',ident,String(dom.imagesWithoutAlt));
  if(dom.brokenImages)fail('medium','broken-images',ident,String(dom.brokenImages));
  if(dom.mainCount!==1||dom.h1Count!==1)fail('medium','landmarks',ident,'main='+dom.mainCount+', h1='+dom.h1Count);
  if(dom.tiny.length)fail('low','small-fonts',ident,JSON.stringify(dom.tiny.slice(0,5)));
  if(jsErrors.length)fail('high','js-errors',ident,JSON.stringify(jsErrors.slice(0,5)));
  if(networkErrors.length)fail('medium','http-errors',ident,JSON.stringify(networkErrors.slice(0,5)));
  const axe=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21a','wcag21aa']).analyze();
  const violations=axe.violations.map(v=>({id:v.id,impact:v.impact,description:v.help,nodes:v.nodes.length,examples:v.nodes.slice(0,3).map(x=>({html:safe(x.html),failure:safe(x.failureSummary)}))}));
  for(const v of violations)fail(v.impact==='critical'||v.impact==='serious'?'high':'medium','axe-'+v.id,ident,v.nodes.length+' elements: '+v.description);
  fs.writeFileSync(path.join(OUT,ident.replace(/\W+/g,'-')+'.json'),JSON.stringify({url:page.url(),viewport,dom,violations,networkErrors,jsErrors},null,2));
  await page.screenshot({path:path.join(OUT,ident.replace(/\W+/g,'-')+'.png'),fullPage:name==='home'||name==='admission',animations:'disabled'});
  summary.push({page:name,viewport:viewport.width,httpStatus:res.status(),overflow:dom.bodyScrollWidth>viewport.width+3,axeViolations:violations.length,jsErrors:jsErrors.length,dom});
  ok=true;
  if(name==='home'&&mobile){
   const toggle=page.locator('.menu-toggle');
   if(await toggle.count()){
     await toggle.click();
     const expanded=await toggle.getAttribute('aria-expanded');
     const visible=await page.locator('.main-nav').isVisible();
     if(expanded!=='true'||!visible)fail('high','menu-open',ident,'expanded='+expanded+', visible='+visible);
     await page.keyboard.press('Escape');
     if(await toggle.getAttribute('aria-expanded')!=='false')fail('high','menu-close',ident,'escape did not collapse');
   }
  }
  if(name==='home'&&viewport.width===1440){
   const ga=await page.evaluate(()=>{
    const link=[...document.querySelectorAll('a')].find(el=>el.getAttribute('href')==='/admission/2027/');
    if(!link)return {test:false,reason:'missing CTA'};
    const before=window.dataLayer?.length||0;
    const stop=e=>e.preventDefault();link.addEventListener('click',stop,{once:true});
    link.click();
    const events=(window.dataLayer||[]).slice(before).filter(x=>x[0]==='event').map(x=>x[1]);
    return {test:true,events};
   });
   if(!ga.test||!ga.events.includes('admission_guide_click'))fail('high','ga-event','home',JSON.stringify(ga));
   fs.writeFileSync(path.join(OUT,'ga4-event-smoke.json'),JSON.stringify(ga,null,2));
  }
 }catch(e){fail('high','page-load-or-audit',name+' '+viewport.width+'px',String(e));}
 finally {await ctx.close();}
 return ok;
};
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
 try{
  for(const [device,viewport,mobile] of devices){
   for(const [name,uri] of pages){
    if(device==='tablet'&&name!=='home')continue;
    if(device==='small-mobile'&&name!=='home'&&name!=='activities')continue;
    await capture(browser,name,uri,viewport,mobile);
   }
  }
 }finally{await browser.close();}
 const results={at:new Date().toISOString(),origin:ORIGIN,checked:summary.length,
    high:findings.filter(x=>x.level==='high').length,
    medium:findings.filter(x=>x.level==='medium').length,
    low:findings.filter(x=>x.level==='low').length,
    findings,summary:summary.map(({page,viewport,httpStatus,overflow,axeViolations,jsErrors,dom})=>({
      page,viewport,httpStatus,overflow,axeViolations,jsErrors,
      sectionOrder:dom.sectionOrder,nav:dom.nav,mediaCards:dom.mediaCards,gaConfigured:dom.gaConfigured
    }))};
 fs.writeFileSync(path.join(OUT,'browser-audit-summary.json'),JSON.stringify(results,null,2));
 console.log(JSON.stringify({checked:results.checked,high:results.high,medium:results.medium,low:results.low,findings:findings.slice(0,20)},null,2));
 if(!summary.length)process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1;});
