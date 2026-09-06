const article = document.querySelector('#article-content');
const slug = new URLSearchParams(location.search).get('slug');
const esc = (value = '') => value.replace(/[&<>'"]/g, (char) => ({ '&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;' }[char]));

const setMeta = (selector, value) => {
  const element = document.querySelector(selector);
  if (element) element.setAttribute('content', value);
};

const setCanonical = (value) => {
  let canonical = document.querySelector('link[rel="canonical"]');
  if (!canonical) {
    canonical = document.createElement('link');
    canonical.rel = 'canonical';
    document.head.append(canonical);
  }
  canonical.href = value;
};

async function renderPost() {
  try {
    const response = await fetch(`data/posts.json?v=${Date.now()}`);
    if (!response.ok) throw new Error('load failed');
    const posts = await response.json();
    const post = posts.find((item) => item.slug === slug) || posts[0];
    if (!post) throw new Error('empty');
    document.title = `${post.title} | 빅데이터소프트웨어공학과`;
    const canonicalUrl = `https://ai.k-bigdata.kr/post.html?slug=${encodeURIComponent(post.slug)}`;
    setMeta('meta[name="description"]', post.excerpt);
    setMeta('meta[property="og:title"]', post.title);
    setMeta('meta[property="og:description"]', post.excerpt);
    setMeta('meta[property="og:url"]', canonicalUrl);
    setMeta('meta[name="twitter:title"]', post.title);
    setMeta('meta[name="twitter:description"]', post.excerpt);
    setCanonical(canonicalUrl);
    const paragraphs = (post.body || [post.excerpt]).map((paragraph) => `<p>${esc(paragraph)}</p>`).join('');
    article.innerHTML = `
      <header class="article-head">
        <p class="article-kicker">${esc(post.tag || 'AI · IT INSIGHT')}</p>
        <h1>${esc(post.title)}</h1>
        <div class="article-meta"><time datetime="${esc(post.date)}">${esc(post.date.replaceAll('-', '.'))}</time><span>${esc(post.source)}</span></div>
      </header>
      <div class="article-body">
        ${paragraphs}
        <aside class="article-connection"><strong>이 흐름이 우리 학과와 연결되는 이유</strong>${esc(post.connection)}</aside>
        <div class="source-box">원문 출처 · <a href="${esc(post.sourceUrl)}" target="_blank" rel="noopener noreferrer">${esc(post.source)}에서 확인하기 ↗</a></div>
        <section class="article-cta"><h2>트렌드를 읽는 데서 끝내지 마세요.</h2><p>AI·데이터·클라우드 기술을 직접 구현하고 포트폴리오로 완성하는 2년을 시작해 보세요.</p><a class="button button-primary" href="https://apply.jinhakapply.com/Notice/5041044/A" target="_blank" rel="noopener noreferrer">2027학년도 수시 1차 지원하기 ↗</a></section>
      </div>`;
  } catch (error) {
    article.innerHTML = '<p class="article-error">글을 불러오지 못했습니다. <a href="index.html#stories">인사이트 목록으로 돌아가기</a></p>';
  }
}

renderPost();
