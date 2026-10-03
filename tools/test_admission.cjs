const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const admissions = require('../admission.js');
const {getState,update,rounds,roundStatus,data}=admissions;
const at=s=>getState(new Date(s));
for(const [date,phase,name] of [
 ['2026-09-06T23:59:59+09:00','upcoming','수시1차'],['2026-09-07T00:00:00+09:00','open','수시1차'],
 ['2026-10-01T23:59:59.999+09:00','open','수시1차'],['2026-10-02T00:00:00+09:00','upcoming','수시2차'],
 ['2026-11-10T23:59:59+09:00','upcoming','수시2차'],['2026-11-11T00:00:00+09:00','open','수시2차'],
 ['2026-11-27T23:59:59.999+09:00','open','수시2차'],['2026-11-28T00:00:00+09:00','upcoming','정시모집'],
 ['2027-01-03T23:59:59+09:00','upcoming','정시모집'],['2027-01-04T00:00:00+09:00','open','정시모집'],
 ['2027-01-22T23:59:59.999+09:00','open','정시모집'],['2027-01-23T00:00:00+09:00','closed','정규모집 종료'],
 ['2028-09-16T00:00:00+09:00','closed','정규모집 종료']
]) {const s=at(date);assert.equal(s.phase,phase,date);assert.equal(s.name,name,date);if(phase!=='open')assert.ok(!s.href.includes('jinhakapply'));}
assert.equal(at('2026-09-16T12:00:00+09:00').countdown,'접수 마감 D-15');
assert.equal(at('2026-10-01T00:00:00+09:00').countdown,'오늘 23:59 접수 마감');
assert.equal(at('2026-11-10T15:00:00Z').phase,'open');
assert.match(at('2026-10-14T12:00:00+09:00').pending,/면접 2026.10.14/);
assert.match(at('2026-10-15T12:00:00+09:00').pending,/발표 2026.10.22/);
assert.equal(at('2026-10-23T12:00:00+09:00').pending,'');
assert.equal(at('2026-12-03T12:00:00+09:00').pending,'수시2차 최초 합격자 발표 2026.12.17');
assert.equal(at('2027-01-28T12:00:00+09:00').pending,'정시모집 최초 합격자 발표 2027.02.04');
assert.equal(roundStatus(rounds[0],new Date('2026-10-14T12:00:00+09:00')),'INTERVIEW');
assert.equal(roundStatus(rounds[0],new Date('2026-10-15T12:00:00+09:00')),'RESULT_WAIT');
assert.match(at('2026-11-11T12:00:00+09:00').href,/5041044/);
const field={getAttribute:()=> 'name',textContent:''};const link={setAttribute(k,v){this[k]=v;}};const pending={};
const doc={querySelectorAll(s){return s==='[data-admission]'?[field]:s==='[data-admission-link]'?[link]:s==='[data-admission-pending]'?[pending]:[];}};
update(doc,new Date('2026-09-16T12:00:00+09:00'));assert.match(link.href,/5041044/);
update(doc,new Date('2026-10-02T12:00:00+09:00'));assert.equal(link.href,'/admission/2027/');assert.equal(field.textContent,'수시2차');assert.equal(pending.hidden,false);
update(doc,new Date('2026-11-11T12:00:00+09:00'));assert.match(link.textContent,/수시2차 원서접수/);assert.equal(pending.hidden,true);
// Browser and build use exactly the same data/state engine.
const ctx={ADMISSIONS_DATA:data};vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../admission.js'),'utf8'),ctx);
for(const time of ['2026-10-03T06:00:00+09:00','2026-11-11T00:00:00+09:00','2027-01-23T00:00:00+09:00'])assert.equal(JSON.stringify(ctx.Admissions.getState(new Date(time))),JSON.stringify(at(time)));
console.log('Admission JSON, KST boundaries, round transitions, pending states, browser/build parity and DOM binding passed.');
