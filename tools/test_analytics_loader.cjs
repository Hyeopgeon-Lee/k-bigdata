const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const script=fs.readFileSync(path.join(__dirname,'../analytics-loader.js'),'utf8');
function harness(narrow,complete=true){
  const handlers={},timers=[],nodes=[];
  const document={
    readyState:complete?'complete':'loading',
    head:{appendChild(node){nodes.push(node)}},
    createElement(tag){return {tag,async:false,src:null,setAttribute(k,v){this[k]=v}}},
    addEventListener(name,fn){handlers[name]=fn}
  };
  const window={
    matchMedia:()=>({matches:narrow}),
    setTimeout(fn,delay){timers.push({fn,delay})},
    addEventListener(name,fn){handlers[name]=fn}
  };
  vm.runInNewContext(script,{document,window});
  return {handlers,timers,nodes};
}
const mobile=harness(true);
assert.equal(mobile.timers[0].delay,2100);
assert.equal(mobile.nodes.length,0,'mobile analytics must not block first paint');
mobile.handlers.pointerdown();
assert.equal(mobile.nodes.length,1,'interaction must trigger analytics immediately');
mobile.timers[0].fn();
assert.equal(mobile.nodes.length,1,'timer and interaction must not double-load');
assert.equal(mobile.nodes[0].src,'https://www.googletagmanager.com/gtag/js?id=G-WN99333WLX');
assert.equal(mobile.nodes[0]['data-ga4-loader'],'home');

const desktop=harness(false);
assert.equal(desktop.timers[0].delay,0);
desktop.timers[0].fn();
assert.equal(desktop.nodes.length,1);
const delayed=harness(true,false);
assert.equal(delayed.timers.length,0);
delayed.handlers.load();
assert.equal(delayed.timers[0].delay,2100);
delayed.timers[0].fn();
assert.equal(delayed.nodes.length,1);
console.log('Homepage GA4 loader preserves one-time install, interaction priority and desktop behavior.');
