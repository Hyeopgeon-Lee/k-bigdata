(() => {
  'use strict';
  const API = 'https://script.google.com/macros/s/AKfycbwMMOwofSybWFy3BYmPi9ol_VQsi_WFfjnEzvnrxUF4ncDZ5TQeS8tcRyOXcgCbgVU4/exec';
  const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  let rows = [];
  const render = () => {
    const query = document.querySelector('#employment-query').value.trim().toLowerCase();
    const year = document.querySelector('#employment-year').value;
    const filtered = rows.filter(row => (!year || row.graduation_year === year) && (!query || `${row.company} ${row.job}`.toLowerCase().includes(query)));
    document.querySelector('#employment-list').innerHTML = filtered.map(row => `<article class="employment-card"><span class="employment-year">${esc(row.graduation_year)}년 졸업</span><h2>${esc(row.company)}</h2><p class="employment-role">${esc(row.job)}</p><p class="employment-name">${esc(row.masked_name)} 동문</p></article>`).join('');
    document.querySelector('#employment-status').textContent = filtered.length ? `${filtered.length}건의 취업현황입니다.` : '조건에 맞는 취업현황이 없습니다.';
  };
  document.addEventListener('DOMContentLoaded', async () => {
    const form = document.querySelector('#employment-filters');
    form.addEventListener('input', render);
    form.addEventListener('reset', () => setTimeout(render));
    try {
      const response = await fetch(`${API}?action=careerPublic`, { headers: { Accept: 'application/json' } });
      const result = await response.json();
      if (!response.ok || !result.success) throw new Error();
      rows = result.data || [];
      const years = [...new Set(rows.map(row => row.graduation_year).filter(Boolean))].sort((a,b) => b.localeCompare(a));
      document.querySelector('#employment-year').insertAdjacentHTML('beforeend', years.map(year => `<option value="${esc(year)}">${esc(year)}년</option>`).join(''));
      render();
    } catch (_) {
      document.querySelector('#employment-status').textContent = '취업현황을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.';
    }
  });
})();
