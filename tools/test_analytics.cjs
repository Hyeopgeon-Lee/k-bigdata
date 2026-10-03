const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const events=[],handlers={};
const ctx={URL,location:{href:'https://ai.k-bigdata.kr/admission/2027/?utm_source=youtube',hostname:'ai.k-bigdata.kr',pathname:'/admission/2027/'},innerHeight:500,scrollY:600,requestAnimationFrame:fn=>fn(),
window:{gtag:(...args)=>events.push(args),addEventListener:(type,fn)=>handlers[type]=fn},document:{documentElement:{scrollHeight:1500},addEventListener:(type,fn)=>handlers[type]=fn}};
vm.runInNewContext(fs.readFileSync(require('node:path').join(__dirname,'../analytics.js'),'utf8'),ctx);
const click=(href,attrs={})=>handlers.click({target:{closest:()=>({href,getAttribute:k=>k==='href'?href:attrs[k],hasAttribute:k=>k in attrs,closest:()=>null})}});
for(const [href,name] of [['https://apply.jinhakapply.com/Notice/5041044/A','admission_apply_click'],['https://open.kakao.com/o/gEd0JIad','admission_kakao_click'],['tel:0221865815','admission_phone_click'],['https://contest.k-bigdata.kr/','project_click'],['https://portfolio.k-bigdata.kr/','portfolio_click'],['https://ai.k-bigdata.kr/employment/','employment_click'],['https://www.kopo.ac.kr/kangseo/content.do?menu=1547','official_department_click'],['https://www.kopo.ac.kr/kangseo/content.do?menu=321','admission_guide_click']]){click(href);assert.equal(events.at(-1)[1],name);assert.deepEqual(Object.keys(events.at(-1)[2]),['click_area']);}
click('https://ai.k-bigdata.kr/admission/2027/',{'data-admission-link':'','data-admission-phase':'upcoming'});assert.equal(events.at(-1)[1],'admission_guide_click');
handlers.scroll();assert.ok(events.some(e=>e[1]==='scroll_50'));ctx.scrollY=950;handlers.scroll();assert.ok(events.some(e=>e[1]==='scroll_90'));
handlers.toggle({target:{matches:()=>true,open:true}});assert.equal(events.at(-1)[1],'faq_open');assert.ok(events.some(e=>e[1]==='admission_page_view'));
assert.ok(!JSON.stringify(events).includes('0221865815'));console.log('GA4 conversion events and parameter privacy passed.');
