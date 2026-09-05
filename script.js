const header = document.querySelector('.site-header');
const menuButton = document.querySelector('.menu-toggle');
const nav = document.querySelector('.main-nav');

const closeMenu = () => {
  nav?.classList.remove('open');
  menuButton?.setAttribute('aria-expanded', 'false');
  menuButton?.setAttribute('aria-label', '메뉴 열기');
  document.body.classList.remove('menu-open');
};

menuButton?.addEventListener('click', () => {
  const isOpen = !nav.classList.contains('open');
  nav.classList.toggle('open', isOpen);
  menuButton.setAttribute('aria-expanded', String(isOpen));
  menuButton.setAttribute('aria-label', isOpen ? '메뉴 닫기' : '메뉴 열기');
  document.body.classList.toggle('menu-open', isOpen);
});

nav?.querySelectorAll('a').forEach((link) => link.addEventListener('click', closeMenu));
window.addEventListener('scroll', () => header?.classList.toggle('scrolled', window.scrollY > 24), { passive: true });

const countdown = document.querySelector('#countdown');
if (countdown) {
  const now = new Date();
  const start = new Date('2026-09-07T00:00:00+09:00');
  const end = new Date('2026-10-01T23:59:59+09:00');
  const days = (target) => Math.max(0, Math.ceil((target - now) / 86400000));
  if (now < start) countdown.textContent = `모집 시작 D-${days(start)}`;
  else if (now <= end) countdown.textContent = `접수 마감 D-${days(end)}`;
  else countdown.textContent = '수시 1차 접수 마감';
}

const escapeHtml = (value = '') => value.replace(/[&<>'"]/g, (char) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
}[char]));

async function loadStories() {
  const grid = document.querySelector('#story-grid');
  if (!grid) return;
  try {
    const response = await fetch(`data/posts.json?v=${Date.now()}`);
    if (!response.ok) throw new Error('게시물을 불러오지 못했습니다.');
    const posts = await response.json();
    grid.innerHTML = posts.slice(0, 6).map((post) => `
      <article class="story-card">
        <div class="story-meta">
          <span class="story-tag">${escapeHtml(post.tag || 'AI · IT')}</span>
          <time datetime="${escapeHtml(post.date)}">${escapeHtml(post.date.replaceAll('-', '.'))}</time>
        </div>
        <h3>${escapeHtml(post.title)}</h3>
        <p>${escapeHtml(post.excerpt)}</p>
        <a href="post.html?slug=${encodeURIComponent(post.slug)}" aria-label="${escapeHtml(post.title)} 자세히 읽기">인사이트 읽기 <span aria-hidden="true">→</span></a>
      </article>`).join('');
  } catch (error) {
    grid.innerHTML = '<p class="story-error">새 글을 불러오는 중입니다. 잠시 후 다시 확인해 주세요.</p>';
  }
}

loadStories();

const revealObserver = 'IntersectionObserver' in window
  ? new IntersectionObserver((entries, observer) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 })
  : null;

document.querySelectorAll('.reveal').forEach((element) => {
  if (revealObserver) revealObserver.observe(element);
  else element.classList.add('visible');
});
