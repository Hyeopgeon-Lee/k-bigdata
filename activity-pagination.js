(() => {
  'use strict';
  const grid = document.querySelector('.activity-card-grid');
  if (!grid) return;
  const cards = [...grid.querySelectorAll(':scope > .activity-card')];
  const perPage = 12;
  if (cards.length <= perPage) return;
  const total = Math.ceil(cards.length / perPage);
  const nav = document.createElement('nav');
  nav.className = 'activity-pagination';
  nav.setAttribute('aria-label', '학과 활동 페이지 선택');
  const heading = document.createElement('span');
  heading.className = 'activity-page-status';
  heading.setAttribute('aria-live', 'polite');
  nav.append(heading);
  const controls = document.createElement('div');
  controls.className = 'activity-page-buttons';
  nav.append(controls);
  let page = 1;
  function draw(next, scroll = false) {
    page = Math.max(1, Math.min(total, next));
    for (const [i, card] of cards.entries()) card.hidden = Math.floor(i / perPage) + 1 !== page;
    controls.replaceChildren();
    for (let n = 1; n <= total; n += 1) {
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = String(n);
      button.className = 'activity-page-button' + (n === page ? ' selected' : '');
      button.setAttribute('aria-label', n + '페이지');
      if (n === page) button.setAttribute('aria-current', 'page');
      button.addEventListener('click', () => draw(n, true));
      controls.append(button);
    }
    heading.textContent = '전체 ' + cards.length + '건 · ' + page + ' / ' + total + '페이지';
    if (scroll) {
      const anchor = document.querySelector('.activity-list-heading') || grid;
      anchor.scrollIntoView({behavior:'smooth',block:'start'});
    }
  }
  grid.parentElement.append(nav);
  draw(1);
})();
