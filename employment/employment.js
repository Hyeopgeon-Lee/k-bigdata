(() => {
  'use strict';
  const API = 'https://script.google.com/macros/s/AKfycbwMMOwofSybWFy3BYmPi9ol_VQsi_WFfjnEzvnrxUF4ncDZ5TQeS8tcRyOXcgCbgVU4/exec';
  const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  let rows = JSON.parse(document.querySelector('#employment-fallback')?.textContent || '[]');
  const render = () => {
    const query = document.querySelector('#employment-query').value.trim().toLowerCase();
    const year = document.querySelector('#employment-year').value;
    const filtered = rows.filter(row => (!year || row.graduation_year === year) && (!query || `${row.company} ${row.job}`.toLowerCase().includes(query)));
    document.querySelector('#employment-list').innerHTML = filtered.map(row => `<article class="employment-card"><span class="employment-year">${esc(row.graduation_year)}년 ${Number(row.graduation_year) > new Date().getFullYear() ? '졸업예정' : '졸업'}</span><h2>${esc(row.company)}</h2><p class="employment-role">${esc(row.job)}</p>${row.masked_name ? `<p class="employment-name">${esc(row.masked_name)} 동문</p>` : ''}</article>`).join('');
    document.querySelector('#employment-status').textContent = filtered.length ? `${filtered.length}건의 취업현황입니다.` : '조건에 맞는 취업현황이 없습니다.';
  };
  document.addEventListener('DOMContentLoaded', async () => {
    const form = document.querySelector('#employment-filters');
    form.addEventListener('input', render);
    form.addEventListener('reset', () => setTimeout(render));
    const updateYears = () => {
      const years = [...new Set(rows.map(row => String(row.graduation_year)).filter(Boolean))].sort().reverse();
      document.querySelector('#employment-year').innerHTML = '<option value="">전체</option>' + years.map(year => `<option value="${esc(year)}">${esc(year)}년</option>`).join('');
    };
    updateYears();
    try {
      const response = await fetch(`${API}?action=careerPublic`, { headers: { Accept: 'application/json' } });
      const result = await response.json();
      if (!response.ok || !result.success) throw new Error();
      rows = result.data || [];
      updateYears();
      render();
    } catch (_) {
      document.querySelector('#employment-status').textContent = '최신 자료 연결이 지연되어 최근 확인한 공개 취업 사례를 표시합니다.';
    }
  });
})();
