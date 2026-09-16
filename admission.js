/* 2027 admissions. Source: Seoul Gangseo official prospectus, p.7 (2026-09-16).
 * Keep identical copies in the department, portfolio and professor sites.
 * All dates have an explicit Korea offset; never infer an unannounced admission round.
 */
(function (root) {
  'use strict';
  const GUIDE = 'https://www.kopo.ac.kr/kangseo/content.do?menu=321';
  const APPLY = 'https://www.kopo.ac.kr/kangseo/content.do?menu=1714';
  const rounds = [
    {name:'수시 1차', start:'2026-09-07', end:'2026-10-01', interview:'2026-10-14', result:'2026-10-22', seats:23,
      apply:'https://apply.jinhakapply.com/Notice/5041044/A'},
    {name:'수시 2차', start:'2026-11-11', end:'2026-11-27', interview:'2026-12-02', result:'2026-12-17', seats:4, apply:APPLY},
    {name:'정시모집', start:'2027-01-04', end:'2027-01-22', interview:'2027-01-27', result:'2027-02-04', seats:3, apply:APPLY}
  ];
  const instant = (day) => Date.parse(day + 'T00:00:00+09:00');
  const koreaDay = (now) => new Date(Number(now) + 9*3600000).toISOString().slice(0,10);
  const shortDate = (day) => day.slice(5).replace('-', '.');
  const fullDate = (day) => day.replaceAll('-', '.');
  function getState(now = new Date()) {
    const today = koreaDay(now);
    const round = rounds.find(r => today <= r.end);
    const previous = [...rounds].reverse().find(r => today > r.end);
    let pending = '';
    if (previous && today <= previous.result) {
      pending = today <= previous.interview
        ? `${previous.name} 면접 ${fullDate(previous.interview)}`
        : `${previous.name} 최초 합격자 발표 ${fullDate(previous.result)}`;
    }
    if (!round) return {phase:'closed', name:'입학 안내', title:'입학 안내', countdown:'2027학년도 정규 원서접수 종료',
      button:'추가모집·입학 공지 확인', href:GUIDE, period:'추가모집 여부는 공식 안내 확인', pending,
      interview:today <= '2027-03-01' ? '2027.01.27' : '공식 모집요강 확인',
      result:today <= '2027-03-01' ? '2027.02.04' : '공식 모집요강 확인',
      seats:'모집인원은 공식 모집요강 확인', start:'—', end:'—'};
    const open = today >= round.start;
    const days = Math.round((instant(open ? round.end : round.start) - instant(today))/86400000);
    return {phase:open?'open':'upcoming', name:round.name, title:`2027학년도 ${round.name}`,
      countdown:open ? (days===0?'오늘 23:59 접수 마감':`접수 마감 D-${days}`) : `접수 시작 D-${days}`,
      button:open?`${round.name} 원서접수`:`${round.name} 모집일정 확인`, href:open?round.apply:GUIDE,
      period:`${fullDate(round.start)} ~ ${fullDate(round.end)} 23:59`, pending,
      interview:fullDate(round.interview), result:fullDate(round.result),
      seats:`${round.name} ${round.seats}명`, start:shortDate(round.start), end:shortDate(round.end)};
  }
  function update(doc = root.document, now = new Date()) {
    const state = getState(now);
    doc.querySelectorAll('[data-admission]').forEach(el => {
      const value = state[el.getAttribute('data-admission')];
      if (value !== undefined) el.textContent = value;
    });
    doc.querySelectorAll('[data-admission-link]').forEach(el => {
      el.href = state.href;
      el.setAttribute('data-admission-phase', state.phase);
      el.textContent = state.button + ' ↗';
      el.setAttribute('aria-label', state.button + ' (새 창)');
    });
    doc.querySelectorAll('[data-admission-pending]').forEach(el => {
      el.textContent = state.pending;
      el.hidden = !state.pending;
    });
    doc.querySelectorAll('[data-admission-card]').forEach(el => el.setAttribute('aria-label', state.title + ' 일정'));
    return state;
  }
  root.Admissions = {getState, update, rounds};
  if (typeof module !== 'undefined' && module.exports) module.exports = root.Admissions;
  if (root.document) {
    const start = () => { update(); root.setInterval(() => update(), 30000); };
    if (root.document.readyState === 'loading') root.document.addEventListener('DOMContentLoaded', start);
    else start();
    root.document.addEventListener('visibilitychange', () => { if (!root.document.hidden) update(); });
  }
})(typeof window !== 'undefined' ? window : globalThis);
