#!/usr/bin/env node
/**
 * Read-only live-site verification: desktop & mobile screenshots, axe WCAG,
 * browser console/network diagnostics, navigation, events and Lighthouse.
 * The script never edits remote content or submits admissions forms.
 */
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { chromium } from 'playwright-core';

const require=createRequire(import.meta.url);
const ROOT=path.resolve('artifacts/site-live-audit');
fs.mkdirSync(ROOT,{recursive:true});
const BASE='https://ai.k-bigdata.kr';
const OUT={date:new Date().toISOString(),base:BASE,environment:{},browsers:[],lighthouse:[],summary:{}};
const CHROME=['/usr/bin/google-chrome','/usr/bin/google-chrome-stable','/opt/google/chrome/chrome','/usr/bin/chromium']
 .find(p=>fs.existsSync(p));
if(!CHROME)throw new Error('Chrome executable not found on runner');
OUT.environment.chrome=CHROME;
const axeJs=fs.readFileSync(require.resolve('axe-core/axe.min.js'),'utf8');
const profiles=[
 {name:'desktop',width:1440,height:900,isMobile:false,deviceScaleFactor:1},
 {name:'mobile',width:390,height:844,isMobile:true,hasTouch:true,deviceScaleFactor:2},
 {name:'small-mobile',width:320,height:700,isMobile:true,hasTouch:true,deviceScaleFactor:1},
 {name:'mobile-landscape',width:844,height:390,isMobile:true,hasTouch:true,deviceScaleFactor:1}
];
const routes=[
 {name:'home',path:'/'},
 {name:'activities',path:'/activities/'},
 {name:'admission',path:'/admission/2027/'},
 {name:'projects',path:'/projects/'},
 {name:'employment',path:'/employment/'}
];
const browser=await chromium.launch({headless:true,executablePath:CHROME,args:['--no-sandbox','--disable-dev-shm-usage']});
const failures=[];
for(const profile of profiles){
 for(const route of routes){
  if(profile.name!=='desktop'&&profile.name!=='mobile'&&route.name!=='home')continue;
  const context=await browser.newContext({viewport:{width:profile.width,height:profile.height},isMobile:profile.isMobile,
    deviceScaleFactor:profile.deviceScaleFactor,hasTouch:Boolean(profile.hasTouch),locale:'ko-KR',timezoneId:'Asia/Seoul'});
  const page=await context.newPage();
  const record={profile:profile.name,route:route.name,url:BASE+route.path,jsErrors:[],httpErrors:[],requestedGaEvents:[],
    failedRequests:[],issues:[],axe:[],warnings:[]};
  page.on('pageerror',e=>record.jsErrors.push(String(e).slice(0,250)));
  page.on('response',response=>{
    if(response.url().startsWith(BASE)&&response.status()>=400)record.httpErrors.push({status:response.status(),path:new URL(response.url()).pathname});
  });
  page.on('requestfailed',req=>{
    if(req.url().startsWith(BASE))record.failedRequests.push(req.failure()?.errorText+' '+new URL(req.url()).pathname);
  });
  page.on('request',req=>{
    if(/google-analytics\.com\/g\/collect/i.test(req.url())){
      try{const params=new URL(req.url()).searchParams;record.requestedGaEvents.push(params.get('en')||'page_view');}catch{}
    }
  });
  try{
    const response=await page.goto(record.url,{waitUntil:'domcontentloaded',timeout:55000});
    record.httpStatus=response?.status()||0;
    await page.waitForTimeout(1000);
    record.visual=await page.evaluate(()=>{
      const doc=document.documentElement;
      const header=document.querySelector('header');
      const nav=document.querySelector('.main-nav');
      const cta=document.querySelector('.nav-cta');
      const box=el=>{if(!el)return null;const r=el.getBoundingClientRect();return {x:Math.round(r.x),y:Math.round(r.y),width:Math.round(r.width),height:Math.round(r.height)};};
      const all=[...document.querySelectorAll('a,button,summary,input,select')];
      const touch=all.filter(el=>{
        const s=getComputedStyle(el),r=el.getBoundingClientRect();
        return r.width>0&&r.height>0&&s.visibility!=='hidden'&&s.display!=='none';
      });
      const smallTouch=touch.filter(el=>{let r=el.getBoundingClientRect();return r.width<44||r.height<44;});
      const textElements=[...document.querySelectorAll('p,li,a,span,small,button,h1,h2,h3,label')];
      const smallText=textElements.filter(el=>{
        let s=getComputedStyle(el), r=el.getBoundingClientRect();
        return s.display!=='none'&&s.visibility!=='hidden'&&r.width>0&&r.height>0&&parseFloat(s.fontSize)<14;
      });
      return {
        title:document.title, documentWidth:doc.scrollWidth,viewportWidth:innerWidth,
        overflowPx:Math.max(0,doc.scrollWidth-innerWidth),height:doc.scrollHeight,
        headings:{h1:document.querySelectorAll('h1').length,h2:document.querySelectorAll('h2').length},
        navLinks:[...nav?.querySelectorAll('a')||[]].map(x=>({text:x.textContent.trim(),url:x.getAttribute('href')})),
        navBox:box(nav),headerBox:box(header),ctaBox:box(cta),
        mainSections:document.querySelectorAll('main>section').length,
        activitiesCount:document.querySelectorAll('article.activity-card').length,
        videoPoster:document.querySelector('#campus-film video')?.poster||null,
        smallTouchCount:smallTouch.length,visibleControlCount:touch.length,
        smallTouchExamples:smallTouch.slice(0,8).map(x=>({tag:x.tagName,text:x.textContent.trim().slice(0,40),r:box(x)})),
        smallTextCount:smallText.length,smallTextExamples:smallText.slice(0,8).map(x=>({text:x.textContent.trim().slice(0,42),font:getComputedStyle(x).fontSize}))
      };
    });
    if(record.visual.overflowPx>2)record.issues.push('Horizontal overflow '+record.visual.overflowPx+'px');
    if(record.visual.headings.h1!==1)record.issues.push('H1 count '+record.visual.headings.h1);
    if(record.httpStatus!==200)record.issues.push('HTTP '+record.httpStatus);
    if(route.name==='home'&&record.visual.mainSections!==7)record.issues.push('Home sections expected 7, found '+record.visual.mainSections);
    if(route.name==='activities'&&record.visual.activitiesCount>12)record.issues.push('Archive cards exceeded 12');
    if(route.name==='admission'){
      record.breadcrumb=await page.evaluate(()=>{
        const nav=document.querySelector('nav.breadcrumb');
        if(!nav)return null;
        const parts=[...nav.children].map(el=>{
          const r=el.getBoundingClientRect();
          return {text:el.textContent.trim(),top:r.top,bottom:r.bottom,
            centerY:(r.top+r.bottom)/2,left:r.left,right:r.right,height:r.height};
        });
        const navBox=nav.getBoundingClientRect();
        return {parts,navWidth:navBox.width,viewport:innerWidth,
          flexWrap:getComputedStyle(nav).flexWrap,
          maxCenterDifference:parts.length?Math.max(...parts.map(p=>p.centerY))-Math.min(...parts.map(p=>p.centerY)):0};
      });
      if(!record.breadcrumb||record.breadcrumb.parts.length!==3)
        record.issues.push('Admission breadcrumb structure missing');
      else {
        if(record.breadcrumb.maxCenterDifference>2)
          record.issues.push('Admission breadcrumb not baseline-aligned');
        if(record.breadcrumb.parts.some(p=>p.right>record.breadcrumb.viewport+2))
          record.issues.push('Admission breadcrumb overflows viewport');
        if(record.breadcrumb.parts[0].height<43)
          record.issues.push('Admission breadcrumb home link tap height below 44px');
        if(record.breadcrumb.flexWrap!=='nowrap')
          record.issues.push('Admission breadcrumb is allowed to wrap');
      }
    }
    if(profile.name==='desktop'||profile.name==='mobile'){
      const screenshot=profile.name+'-'+route.name+'.png';
      await page.screenshot({path:path.join(ROOT,screenshot),fullPage:true,animations:'disabled',timeout:45000});
      record.screenshot=screenshot;
      await page.addScriptTag({content:axeJs});
      const result=await page.evaluate(async()=>window.axe.run(document,{runOnly:{type:'tag',
         values:['wcag2a','wcag2aa','wcag21a','wcag21aa']}}));
      record.axe=result.violations.map(x=>({id:x.id,impact:x.impact,description:x.description,
         affectedNodes:x.nodes.length,samples:x.nodes.slice(0,3).map(n=>({selector:n.target.join(' ').slice(0,140), failure:n.failureSummary?.slice(0,330), contrast:n.any?.[0]?.data}))}));
      record.axeIncomplete=result.incomplete.length;
      if(route.name==='home'&&profile.name==='mobile'){
        const menu=page.locator('.menu-toggle');
        if(await menu.count()){
          await menu.click();
          const mobileNav=await page.evaluate(()=>{
            const el=document.querySelector('.main-nav'), b=document.querySelector('.menu-toggle');
            return {expanded:b?.getAttribute('aria-expanded'),visible:el?getComputedStyle(el).display!=='none':false,
            canScroll:el?el.scrollHeight>el.clientHeight:false,lastLinkText:el?.querySelector('a:last-child')?.textContent.trim()};
          });
          record.mobileNav=mobileNav;
          if(mobileNav.expanded!=='true'||!mobileNav.visible)record.issues.push('Mobile navigation failed to open');
          await page.keyboard.press('Escape');
          record.mobileNav.closedAfterEscape=await menu.getAttribute('aria-expanded');
          if(record.mobileNav.closedAfterEscape!=='false')record.issues.push('Mobile navigation failed to close with Escape');
        }
      }
      if(route.name==='activities'&&profile.name==='mobile'){
        const input=page.locator('.activity-toolbar input[type="search"]');
        if(await input.count()){
          await input.fill('해커톤');
          await page.waitForTimeout(600);
          record.search={term:'해커톤',
            cards:await page.locator('.activity-card').count(),
            status:await page.locator('.activity-match-hint').innerText()};
          if(record.search.cards>12)record.issues.push('Search returned over 12 cards');
        }else record.issues.push('Search control missing');
      }
    }
    if(route.name==='home'&&profile.name==='desktop'){
      record.ga=await page.evaluate(()=>{
        const before=(window.dataLayer||[]).length;
        const target=document.querySelector('.main-nav .nav-cta');
        if(target) {
          document.addEventListener('click',e=>e.preventDefault(),{capture:true,once:true});
          target.click();
        }
        const events=[...(window.dataLayer||[])].slice(before).map(args=>Array.from(args)).filter(x=>x[0]==='event');
        return {configured:typeof window.gtag==='function',
          eventNames:events.map(x=>x[1]),params:events.map(x=>x[2]),
          loadedMeasurementIds:(window.dataLayer||[]).map(args=>Array.from(args)).filter(x=>x[0]==='config').map(x=>x[1])};
      });
      if(!record.ga.configured)record.issues.push('GA4 gtag not initialized');
      if(!record.ga.eventNames.includes('admission_guide_click'))record.issues.push('GA4 admission click not seen in dataLayer');
    }
    if(record.jsErrors.length||record.httpErrors.length)record.issues.push('JS/runtime or same-origin HTTP errors');
  }catch(err){record.issues.push('Audit could not complete: '+String(err).slice(0,550));failures.push(record.profile+'/'+record.route);}
  if (profile.name==='desktop'||profile.name==='mobile') {
    console.log('ACCESSIBILITY_DETAILS',JSON.stringify({profile:record.profile,route:record.route,violations:record.axe}));
    console.log('UI_DETAILS',JSON.stringify({profile:record.profile,route:record.route,visual:record.visual,
      menu:record.mobileNav,search:record.search,gaRequests:record.requestedGaEvents}));
  }
  OUT.browsers.push(record);
  console.log('BROWSER',JSON.stringify({profile:record.profile,route:record.route,http:record.httpStatus,
    overflow:record.visual?.overflowPx,sections:record.visual?.mainSections,archiveCards:record.visual?.activitiesCount,
    jsErrors:record.jsErrors.length,httpErrors:record.httpErrors.length,
    accessibilityViolations:record.axe.map(x=>({id:x.id,impact:x.impact,count:x.affectedNodes})),
    issues:record.issues,GA:record.ga}));
  await context.close();
 }
}
await browser.close();

const lighthouseTargets=[
 {name:'mobile-home',path:'/',mode:'mobile'},
 {name:'desktop-home',path:'/',mode:'desktop'},
 {name:'mobile-activities',path:'/activities/',mode:'mobile'},
 {name:'mobile-admission',path:'/admission/2027/',mode:'mobile'}
];
for(const target of lighthouseTargets){
 const filename=target.name+'.lighthouse.json';
 const args=['lighthouse',BASE+target.path,'--output=json','--output-path='+path.join(ROOT,filename),
   '--only-categories=performance,accessibility,best-practices,seo',
   '--chrome-flags=--headless=new --no-sandbox --disable-dev-shm-usage','--quiet'];
 if(target.mode==='desktop')args.push('--preset=desktop');
 const run=spawnSync('npx',args,{encoding:'utf8',timeout:180000,maxBuffer:3*1024*1024});
 const rec={name:target.name,route:target.path,mode:target.mode,code:run.status};
 if(fs.existsSync(path.join(ROOT,filename))){
   try{
     const data=JSON.parse(fs.readFileSync(path.join(ROOT,filename),'utf8'));
     rec.categories=Object.fromEntries(Object.entries(data.categories||{}).map(([k,v])=>[k,Math.round((v.score||0)*100)]));
     rec.metrics={
       LCP_ms:data.audits?.['largest-contentful-paint']?.numericValue||null,
       CLS:data.audits?.['cumulative-layout-shift']?.numericValue??null,
       TBT_ms:data.audits?.['total-blocking-time']?.numericValue??null,
       FCP_ms:data.audits?.['first-contentful-paint']?.numericValue??null,
       SpeedIndex_ms:data.audits?.['speed-index']?.numericValue??null
     };
     rec.topOpportunities=Object.values(data.audits||{}).filter(a=>
       a.details?.type==='opportunity'&&a.details.overallSavingsMs>100)
       .sort((a,b)=>b.details.overallSavingsMs-a.details.overallSavingsMs)
       .slice(0,6).map(x=>({name:x.title,savingsMs:x.details.overallSavingsMs}));
     rec.failedAudits=Object.values(data.audits||{}).filter(a=>a.score===0&&a.scoreDisplayMode==='binary')
       .slice(0,12).map(x=>x.id);
   }catch(e){rec.error='Cannot parse Lighthouse: '+String(e);}
 }else rec.error=(run.stderr||run.stdout||run.error||'Lighthouse output missing').toString().slice(-1400);
 OUT.lighthouse.push(rec);
 console.log('LIGHTHOUSE',JSON.stringify(rec));
}
OUT.summary={
 pagesChecked:OUT.browsers.length,
 pagesWithIssues:OUT.browsers.filter(x=>x.issues.length).length,
 accessibilityViolationTypes:[...new Set(OUT.browsers.flatMap(x=>x.axe.map(a=>a.id)))],
 auditIncomplete:failures,
 measuredLighthouse:OUT.lighthouse.filter(x=>x.categories).length
};
fs.writeFileSync(path.join(ROOT,'summary.json'),JSON.stringify(OUT,null,2));
console.log('FINAL_SUMMARY',JSON.stringify(OUT.summary));
