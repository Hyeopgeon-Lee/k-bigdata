/* Shared Node/browser state engine. Dates live only in admissions.json. */
(function (root) {
  'use strict';
  const data = typeof module !== 'undefined' && module.exports ? require('./data/admissions.json') : root.ADMISSIONS_DATA;
  if (!data) return;
  const rounds = data.rounds;
  const instant = day => Date.parse(day + 'T00:00:00+09:00');
  const koreaDay = now => new Date(Number(now) + 9 * 3600000).toISOString().slice(0, 10);
  const fullDate = day => day.replaceAll('-', '.');
  const shortDate = day => day.slice(5).replace('-', '.');
  const format = (text, round) => text.replaceAll('{round}', round);
  function roundStatus(round, now = new Date()) {
    const today = koreaDay(now);
    if (Number(now) < instant(round.start)) return 'UPCOMING';
    if (Number(now) <= Date.parse(`${round.end}T${round.deadlineTime}:59.999+09:00`)) return 'OPEN';
    if (today <= round.interview) return 'INTERVIEW';
    if (today < round.result) return 'RESULT_WAIT';
    return 'CLOSED';
  }
  function getState(now = new Date()) {
    const today = koreaDay(now);
    const round = rounds.find(r => ['UPCOMING', 'OPEN'].includes(roundStatus(r, now)));
    const previous = [...rounds].reverse().find(r => today > r.end);
    let pending = '';
    if (previous && today <= previous.result) pending = today <= previous.interview
      ? `${previous.name} 면접 ${fullDate(previous.interview)}`
      : `${previous.name} 최초 합격자 발표 ${fullDate(previous.result)}`;
    const name = round ? round.name : '정규모집 종료';
    const status = round ? roundStatus(round, now) : 'CLOSED';
    const open = status === 'OPEN';
    const days = round ? Math.round((instant(open ? round.end : round.start) - instant(today)) / 86400000) : 0;
    const period = round ? `${fullDate(round.start)} ~ ${fullDate(round.end)} ${round.deadlineTime}` : '추가모집 및 입학 공지 확인';
    return {status, phase:status.toLowerCase(), roundId: round?.id || 'closed', name, title: `${data.year}학년도 ${name}`,
      countdown: round ? (open ? (days === 0 ? `오늘 ${round.deadlineTime} 접수 마감` : `접수 마감 D-${days}`) : `${name} 접수 시작 D-${days}`) : `${data.year}학년도 정규모집 종료`,
      announcement: round ? (open ? `${Number(round.end.slice(5,7))}월 ${Number(round.end.slice(8))}일 ${round.deadlineTime} 마감` : `${Number(round.start.slice(5,7))}월 ${Number(round.start.slice(8))}일 원서접수 시작`) : '추가모집 및 입학 공지 확인',
      button: format(data.cta[status], name), href: open ? data.applyUrl : round ? data.admissionUrl : data.guideUrl,
      period, pending, interview: round ? fullDate(round.interview) : '공식 입학 공지 확인',
      result: round ? fullDate(round.result) : '공식 입학 공지 확인', seats: round ? `${name} ${round.seats}명` : '공식 입학 공지 확인',
      start: round ? shortDate(round.start) : '—', end: round ? shortDate(round.end) : '—',
      seoTitle: format(data.seoTitle, name), seoDescription: format(data.seoDescription, name),
      ogDescription: format(data.ogDescription, name).replace('{period}', period),
      socialImage: round ? round.socialImage : 'og-department.png',
      previousStatus: previous ? roundStatus(previous, now) : null};
  }
  function update(doc = root.document, now = new Date()) {
    const state = getState(now);
    doc.querySelectorAll('[data-admission]').forEach(el => {
      const value = state[el.getAttribute('data-admission')];
      if (value !== undefined) el.textContent = value;
    });
    doc.querySelectorAll('[data-admission-link]').forEach(el => {
      el.href = state.phase === 'upcoming' && doc.location?.pathname === data.admissionUrl ? '#schedule' : state.href;
      el.setAttribute('data-admission-phase', state.phase);
      el.textContent = state.button + ' →';
      if (state.href.startsWith('/')) { el.removeAttribute?.('target'); el.removeAttribute?.('rel'); }
      else { el.setAttribute('target', '_blank'); el.setAttribute('rel', 'noopener noreferrer'); }
      el.setAttribute('aria-label', state.button + (state.href.startsWith('/') ? '' : ' (새 창)'));
    });
    doc.querySelectorAll('[data-admission-pending]').forEach(el => { el.textContent = state.pending; el.hidden = !state.pending; });
    doc.querySelectorAll('[data-admission-card]').forEach(el => el.setAttribute('aria-label', state.title + ' 일정'));
    doc.querySelectorAll('[data-round-status]').forEach(el => {
      const status = roundStatus(rounds.find(r => r.id === el.getAttribute('data-round-status')), now);
      el.textContent = status === 'OPEN' ? '접수중' : status === 'UPCOMING' ? '예정' : '접수 종료';
      el.setAttribute('data-status', status.toLowerCase());
    });
    return state;
  }
  root.Admissions = {getState, update, rounds, roundStatus, data};
  if (typeof module !== 'undefined' && module.exports) module.exports = root.Admissions;
  if (root.document) {
    const start = () => { update(); root.setInterval(() => update(), 30000); };
    if (root.document.readyState === 'loading') root.document.addEventListener('DOMContentLoaded', start); else start();
    root.document.addEventListener('visibilitychange', () => { if (!root.document.hidden) update(); });
  }
})(typeof window !== 'undefined' ? window : globalThis);
