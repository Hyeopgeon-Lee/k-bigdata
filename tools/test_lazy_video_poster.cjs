// Deterministic browser-only loading checks with no network requests.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname,'../lazy-video-poster.js'),'utf8');
const makeVideo = uri => {
  const attrs = {'data-lazy-poster':uri};
  return {
    attrs, poster:null, handlers:{},
    getAttribute(k){return this.attrs[k] || null;},
    removeAttribute(k){delete this.attrs[k];},
    addEventListener(k,fn){this.handlers[k]=fn;}
  };
};
const first=makeVideo('/assets/media/department-campus-cover.webp');
const second=makeVideo('/assets/media/education-overview-cover.webp');
let observer;
class FakeObserver {
  constructor(callback,options){this.callback=callback;this.options=options;this.observed=[];this.removed=[];observer=this;}
  observe(el){this.observed.push(el);}
  unobserve(el){this.removed.push(el);}
}
const ctx={document:{querySelectorAll:()=>[first,second]},window:{IntersectionObserver:FakeObserver},IntersectionObserver:FakeObserver};
vm.runInNewContext(source,ctx);
assert.equal(first.poster,null,'no eager poster load');
assert.equal(second.poster,null,'no eager poster load');
assert.equal(observer.observed.length,2);
assert.equal(observer.options.rootMargin,'80px 0px');
observer.callback([{target:first,isIntersecting:true}],observer);
assert.equal(first.poster,'/assets/media/department-campus-cover.webp');
assert.equal(first.attrs['data-lazy-poster'],undefined);
assert.equal(second.poster,null);
second.handlers.focusin();
assert.equal(second.poster,'/assets/media/education-overview-cover.webp');
assert.equal(observer.removed.length,1);

const fallback=makeVideo('/assets/media/department-campus-cover.webp');
vm.runInNewContext(source,{document:{querySelectorAll:()=>[fallback]},window:{}});
assert.equal(fallback.poster,'/assets/media/department-campus-cover.webp');
console.log('Lazy video poster behavior and fallback verified.');
