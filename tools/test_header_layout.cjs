/* Responsive header layout regression. Runs against generated _site via Chrome. */
'use strict';
const { chromium } = require('playwright-core');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const chrome = ['/usr/bin/google-chrome','/usr/bin/google-chrome-stable','/usr/bin/chromium'].find(p => fs.existsSync(p));
if (!chrome) throw new Error('Chrome executable missing');
const site = 'http://127.0.0.1:8765';
const paths = [['admission','/admission/2027/'],['home','/']];
const widths = [320,390,768,1024,1100,1101,1180,1280,1281,1440];
(async () => {
  const browser=await chromium.launch({executablePath:chrome,headless:true,args:['--no-sandbox','--disable-dev-shm-usage']});
  try {
    for (const [label,path] of paths) {
      for (const width of widths) {
        const page=await browser.newPage({viewport:{width,height:850}});
        const response=await page.goto(site+path,{waitUntil:'domcontentloaded',timeout:30000});
        const prefix=label+' at '+width+'px: ';
        assert.equal(response.status(),200,prefix+'HTTP');
        const layout=await page.evaluate(() => {
          const rect=el=>{
            const r=el.getBoundingClientRect();
            return {x:r.x,y:r.y,right:r.right,width:r.width,height:r.height,center:r.y+r.height/2};
          };
          const root=document.querySelector('header.site-header');
          const brand=root.querySelector('.brand'),nav=root.querySelector('.main-nav'),toggle=root.querySelector('.menu-toggle');
          return {screen:innerWidth,scroll:document.documentElement.scrollWidth,
            brand:rect(brand),nav:rect(nav),toggle:rect(toggle),
            navVisible:getComputedStyle(nav).display!=='none',
            toggleVisible:getComputedStyle(toggle).display!=='none',
            links:[...nav.querySelectorAll(':scope > a')].map(x=>({text:x.textContent.trim(),...rect(x)}))};
        });
        assert.ok(layout.scroll<=width+2,prefix+'horizontal overflow '+layout.scroll);
        assert.equal(layout.links.length,6,prefix+'unexpected menu count');
        if (width>1280) {
          assert.equal(layout.navVisible,true,prefix+'desktop nav hidden');
          assert.equal(layout.toggleVisible,false,prefix+'desktop toggle shown');
          assert.ok(layout.brand.right+8<=layout.nav.x,prefix+'overlapping brand/nav '+JSON.stringify(layout));
          assert.ok(layout.links.every(x=>Math.abs(x.center-layout.links[0].center)<=2),
            prefix+'links have different centers: '+JSON.stringify(layout.links));
          assert.ok(layout.links.every(x=>x.height>=44),prefix+'small link height');
        } else {
          assert.equal(layout.toggleVisible,true,prefix+'hamburger missing');
          assert.equal(layout.navVisible,false,prefix+'menu should be collapsed');
          await page.locator('.menu-toggle').click();
          const opened=await page.evaluate(()=>{
            const root=document.querySelector('header.site-header');
            const menu=root.querySelector('.main-nav');
            return {display:getComputedStyle(menu).display,
              expanded:root.querySelector('.menu-toggle').getAttribute('aria-expanded'),
              boxes:[...menu.querySelectorAll(':scope > a')].map(x=>{
                const r=x.getBoundingClientRect(); return {height:r.height,left:r.left,right:r.right};
              })};
          });
          assert.equal(opened.display,'flex',prefix+'menu did not open');
          assert.equal(opened.expanded,'true',prefix+'wrong ARIA expansion');
          assert.ok(opened.boxes.every(x=>x.height>=44&&x.left>=-2&&x.right<=width+2),
            prefix+'menu overflow or small target: '+JSON.stringify(opened));
          await page.keyboard.press('Escape');
          assert.equal(await page.locator('.menu-toggle').getAttribute('aria-expanded'),'false',
            prefix+'Escape did not close navigation');
        }
        console.log('HEADER_OK',label,width);
        await page.close();
      }
    }
  } finally { await browser.close(); }
})().catch(e=>{console.error(e);process.exitCode=1;});
