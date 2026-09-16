const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname,'../admission.js'),'utf8');
const ctx={}; vm.runInNewContext(source,ctx);
const {getState,update}=ctx.Admissions;
const at=s=>getState(new Date(s));
for (const [date,phase,name] of [
 ['2026-09-06T23:59:59+09:00','upcoming','수시 1차'],
 ['2026-09-07T00:00:00+09:00','open','수시 1차'],
 ['2026-10-01T23:59:59.999+09:00','open','수시 1차'],
 ['2026-10-02T00:00:00+09:00','upcoming','수시 2차'],
 ['2026-11-10T23:59:59+09:00','upcoming','수시 2차'],
 ['2026-11-11T00:00:00+09:00','open','수시 2차'],
 ['2026-11-27T23:59:59+09:00','open','수시 2차'],
 ['2026-11-28T00:00:00+09:00','upcoming','정시모집'],
 ['2027-01-03T23:59:59+09:00','upcoming','정시모집'],
 ['2027-01-04T00:00:00+09:00','open','정시모집'],
 ['2027-01-22T23:59:59+09:00','open','정시모집'],
 ['2027-01-23T00:00:00+09:00','closed','입학 안내'],
 ['2028-09-16T00:00:00+09:00','closed','입학 안내']
]) { const s=at(date);assert.equal(s.phase,phase,date);assert.equal(s.name,name,date);if(phase!=='open')assert.ok(!s.href.includes('jinhakapply')); }
assert.equal(at('2026-09-16T12:00:00+09:00').countdown,'접수 마감 D-15');
assert.equal(at('2026-10-01T00:00:00+09:00').countdown,'오늘 23:59 접수 마감');
assert.equal(at('2026-11-10T15:00:00Z').phase,'open');
assert.match(at('2026-10-14T12:00:00+09:00').pending,/면접 2026.10.14/);
assert.match(at('2026-10-15T12:00:00+09:00').pending,/발표 2026.10.22/);
assert.equal(at('2026-10-23T12:00:00+09:00').pending,'');
assert.equal(at('2026-12-03T12:00:00+09:00').pending,'수시 2차 최초 합격자 발표 2026.12.17');
assert.equal(at('2027-01-28T12:00:00+09:00').pending,'정시모집 최초 합격자 발표 2027.02.04');
assert.match(at('2026-11-11T12:00:00+09:00').href,/menu=1714/);
// DOM binding: changing time updates the existing link and pending note, not only state.
const field={getAttribute:()=> 'name',textContent:''};
const link={setAttribute(k,v){this[k]=v;}}; const pending={};
const doc={querySelectorAll(s){return s==='[data-admission]'?[field]:s==='[data-admission-link]'?[link]:s==='[data-admission-pending]'?[pending]:[];}};
update(doc,new Date('2026-09-16T12:00:00+09:00'));assert.match(link.href,/5041044/);
update(doc,new Date('2026-10-02T12:00:00+09:00'));assert.match(link.href,/menu=321/);assert.equal(field.textContent,'수시 2차');assert.equal(pending.hidden,false);
update(doc,new Date('2026-11-11T12:00:00+09:00'));assert.match(link.textContent,/수시 2차 원서접수/);assert.equal(pending.hidden,true);
console.log('Admission date boundaries, KST, deadlines, waiting states and DOM transitions passed.');
