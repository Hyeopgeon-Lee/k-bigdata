(() => {
  'use strict';
  const API = 'https://script.google.com/macros/s/AKfycbwMMOwofSybWFy3BYmPi9ol_VQsi_WFfjnEzvnrxUF4ncDZ5TQeS8tcRyOXcgCbgVU4/exec';
  const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  document.addEventListener('DOMContentLoaded', async () => {
    const root = document.querySelector('#employment-preview-list');
    if (!root) return;
    try {
      const response = await fetch(`${API}?action=careerPublic`, { headers: { Accept: 'application/json' } });
      const result = await response.json();
      if (!response.ok || !result.success) throw new Error('취업현황을 불러오지 못했습니다.');
      const rows = (result.data || []).slice(0, 8);
      root.innerHTML = rows.length ? rows.map(row => `<article class="employment-mini-card"><span>${esc(row.graduation_year)}년 졸업</span><h3>${esc(row.company)}</h3><p>${esc(row.job)}</p><small>${esc(row.masked_name)} 동문</small></article>`).join('') : '<p class="employment-loading">공개된 취업현황을 준비 중입니다.</p>';
    } catch (_) {
      root.innerHTML = '<p class="employment-loading">취업현황은 전체 페이지에서 확인해 주세요.</p>';
    }
  });
})();
