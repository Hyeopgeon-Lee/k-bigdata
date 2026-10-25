(() => {
  'use strict';
  const grid = document.querySelector('.activity-card-grid');
  if (!grid) return;
  const cards = Array.from(grid.querySelectorAll(':scope > .activity-card')).map((node, order) => ({
    node, order,
    title: node.querySelector('h3')?.textContent.trim() || '',
    summary: node.querySelector('.activity-card-body > p')?.textContent.trim() || '',
    category: node.querySelector('.activity-card-meta > span')?.textContent.trim() || '기타',
    date: node.querySelector('time')?.getAttribute('datetime') || '',
  }));
  const PAGE_SIZE = 12;
  const categories = Array.from(new Set(cards.map(c => c.category))).sort((a,b) => a.localeCompare(b,'ko'));
  const years = Array.from(new Set(cards.map(c => c.date.slice(0,4)))).sort((a,b) => b.localeCompare(a));
  const safe = (text) => String(text || '').trim().slice(0,80);
  const params = () => new URLSearchParams(location.search);
  function readURL() {
    const p = params(), possiblePage = Number(p.get('page'));
    return {
      query: safe(p.get('q')),
      category: categories.includes(p.get('category')) ? p.get('category') : 'all',
      year: years.includes(p.get('year')) ? p.get('year') : 'all',
      sort: p.get('sort') === 'old' ? 'old' : 'new',
      page: Number.isInteger(possiblePage) && possiblePage > 0 ? possiblePage : 1,
    };
  }
  let state = readURL();
  const toolbar = document.createElement('section');
  toolbar.className = 'activity-toolbar';
  toolbar.setAttribute('aria-label','학과 활동 검색 및 분류');
  const controls = document.createElement('div');
  controls.className = 'activity-toolbar-fields';
  const searchLabel = document.createElement('label');
  searchLabel.className = 'activity-search';
  const searchText = document.createElement('span');
  searchText.textContent = '학과 활동 검색';
  const searchInput = document.createElement('input');
  searchInput.type = 'search';
  searchInput.placeholder = '수상·기업·기술·활동 검색';
  searchInput.autocomplete = 'off';
  searchInput.maxLength = 80;
  searchLabel.append(searchText, searchInput);
  controls.append(searchLabel);
  function addSelect(caption, options, name) {
    const label = document.createElement('label');
    label.className = 'activity-select-wrap';
    const title = document.createElement('span');
    title.textContent = caption;
    const field = document.createElement('select');
    field.name = name;
    options.forEach(([value,label])=>{
      const opt = document.createElement('option');
      opt.value = value; opt.textContent = label; field.append(opt);
    });
    label.append(title,field); controls.append(label);
    return field;
  }
  const categorySelect = addSelect('활동 분야',[['all','전체 분야'],...categories.map(c=>[c,c])],'category');
  const yearSelect = addSelect('연도',[['all','전체 연도'],...years.map(y=>[y,y+'년'])],'year');
  const sortSelect = addSelect('정렬',[['new','최신순'],['old','오래된순']],'sort');
  toolbar.append(controls);
  const categoryShortcuts = document.createElement('div');
  categoryShortcuts.className = 'activity-shortcuts';
  categoryShortcuts.setAttribute('aria-label','주요 활동 바로 보기');
  const shortcutItems = [
    ['all','전체'],['수상·성과','수상·성과'],['취업·진로','취업·진로'],
    ['전문가 특강','기업·전문가 특강'],['진로체험','진로체험'],
    ['학생 프로젝트','학생 프로젝트'],
  ];
  shortcutItems.filter(([value])=>value==='all'||categories.includes(value)).forEach(([value,label])=>{
    const button = document.createElement('button');
    button.type = 'button'; button.className = 'activity-shortcut';
    button.textContent = label; button.dataset.category = value;
    button.addEventListener('click',()=>{
      state.category = value; state.page = 1; draw(false,'replace');
    });
    categoryShortcuts.append(button);
  });
  toolbar.append(categoryShortcuts);
  const toolbarFooter = document.createElement('div');
  toolbarFooter.className = 'activity-toolbar-footer';
  const matchHint = document.createElement('p');
  matchHint.className = 'activity-match-hint';
  matchHint.setAttribute('aria-live', 'polite');
  const clearFilters = document.createElement('button');
  clearFilters.type = 'button';
  clearFilters.className = 'activity-clear-filters';
  clearFilters.textContent = '검색·필터 초기화';
  clearFilters.addEventListener('click', () => {
    state = {query:'', category:'all', year:'all', sort:'new', page:1};
    draw(true, 'push');
    searchInput.focus({preventScroll:true});
  });
  toolbarFooter.append(matchHint, clearFilters);
  toolbar.append(toolbarFooter);
  const gridHeading = document.querySelector('.activity-list-heading');
  const headingCount = gridHeading?.querySelector(':scope > span');
  if (gridHeading) gridHeading.insertAdjacentElement('afterend',toolbar);
  else grid.before(toolbar);
  const empty = document.createElement('div');
  empty.className = 'activity-empty';
  empty.setAttribute('role','status');
  empty.innerHTML = '<strong>검색 결과가 없습니다.</strong><p>다른 검색어나 활동 분야를 선택해 보세요.</p>';
  grid.after(empty);
  const nav = document.createElement('nav');
  nav.className = 'activity-pagination';
  nav.setAttribute('aria-label', '학과 활동 페이지 선택');
  const status = document.createElement('span');
  status.className = 'activity-page-status';
  status.setAttribute('aria-live','polite');
  const pageButtons = document.createElement('div');
  pageButtons.className = 'activity-page-buttons';
  pageButtons.setAttribute('role','group');
  pageButtons.setAttribute('aria-label','페이지 이동 버튼');
  nav.append(status, pageButtons);
  empty.after(nav);
  const featured = document.querySelector('.activity-featured');
  const reduceMotion = typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;
  function writeURL(mode) {
    if (!mode) return;
    const url = new URL(location.href);
    for (const name of ['q','category','year','sort','page']) url.searchParams.delete(name);
    if (state.query) url.searchParams.set('q',state.query);
    if (state.category !== 'all') url.searchParams.set('category',state.category);
    if (state.year !== 'all') url.searchParams.set('year',state.year);
    if (state.sort !== 'new') url.searchParams.set('sort',state.sort);
    if (state.page > 1) url.searchParams.set('page',String(state.page));
    history[mode === 'push'?'pushState':'replaceState']({activity:true},'',url.pathname+url.search+url.hash);
  }
  function pageButton(label, page, selected, disabled) {
    const b = document.createElement('button');
    b.type = 'button'; b.textContent = label; b.className = 'activity-page-button';
    if (selected) { b.classList.add('selected'); b.setAttribute('aria-current','page'); }
    b.disabled = disabled;
    b.setAttribute('aria-label',label==='이전'?'이전 페이지':label==='다음'?'다음 페이지':page+'페이지');
    b.addEventListener('click',()=>{ state.page = page; draw(true,'push'); });
    pageButtons.append(b);
  }
  function ellipsis() {
    const span = document.createElement('span');span.className='activity-pagination-dots';
    span.textContent='…';span.setAttribute('aria-hidden','true');pageButtons.append(span);
  }
  function draw(scroll = false, historyMode = '') {
    searchInput.value = state.query;
    categorySelect.value = state.category;
    yearSelect.value = state.year;
    sortSelect.value = state.sort;
    for (const button of categoryShortcuts.querySelectorAll('button')) {
      const selected = button.dataset.category === state.category;
      button.classList.toggle('selected',selected);
      button.setAttribute('aria-pressed',String(selected));
    }
    const query = state.query.toLocaleLowerCase('ko').replace(/\s+/g,' ');
    const words = query.split(' ').filter(Boolean);
    const matches = cards.filter(c =>
      (state.category==='all'||c.category===state.category) &&
      (state.year==='all'||c.date.startsWith(state.year)) &&
      words.every(word=>(c.title+' '+c.summary+' '+c.category).toLocaleLowerCase('ko').includes(word)));
    matches.sort((a,b)=> state.sort === 'old' ? a.date.localeCompare(b.date)||a.order-b.order
                                              : b.date.localeCompare(a.date)||a.order-b.order);
    // All cards stay in the document for no-JS fallback and discoverability.
    // Reorder in place; filter using the hidden attribute for accessible pagination.
    const others = cards.filter(c=>!matches.includes(c));
    grid.append(...matches.map(c=>c.node),...others.map(c=>c.node));
    const total = Math.max(1,Math.ceil(matches.length/PAGE_SIZE));
    state.page = Math.min(Math.max(state.page,1),total);
    const shown = new Set(matches.slice((state.page-1)*PAGE_SIZE,state.page*PAGE_SIZE).map(c=>c.node));
    for (const c of cards) c.node.hidden = !shown.has(c.node);
    empty.hidden = matches.length !== 0;
    pageButtons.replaceChildren();
    if (matches.length>PAGE_SIZE) {
      // On narrow screens, reserve room for both previous and next buttons.
      const compact = typeof matchMedia === 'function' &&
                      matchMedia('(max-width: 640px)').matches;
      pageButton('이전',state.page-1,false,state.page===1);
      let start, end;
      if (compact && state.page > 3 && state.page < total-2) {
        // Middle pages retain first/current/last and both arrow controls.
        start = end = state.page;
      } else {
        const windowSize = compact ? 3 : 5;
        start = Math.max(1, state.page-Math.floor(windowSize/2));
        end = Math.min(total, start+windowSize-1);
        start = Math.max(1, end-windowSize+1);
      }
      if(start>1){pageButton('1',1,false,false);if(start>2)ellipsis();}
      for(let i=start;i<=end;i++)pageButton(String(i),i,i===state.page,false);
      if(end<total){if(end<total-1)ellipsis();pageButton(String(total),total,false,false);}
      pageButton('다음',state.page+1,false,state.page===total);
    }
    status.textContent = '전체 '+cards.length+'건 중 '+matches.length+'건 · '+state.page+' / '+total+'페이지';
    const filtering = Boolean(state.query) || state.category !== 'all' || state.year !== 'all' || state.sort !== 'new';
    if (featured) featured.hidden = filtering;
    clearFilters.hidden = !filtering;
    matchHint.textContent = filtering ? '조건에 맞는 활동 ' + matches.length + '건' : '2016년부터 이어진 학과 활동 ' + cards.length + '건';
    if (headingCount) headingCount.textContent = filtering ? '검색 결과 ' + matches.length + '건' : '2016–2026 · 전체 ' + cards.length + '건';
    writeURL(historyMode);
    if (scroll) (toolbar||grid).scrollIntoView({behavior:reduceMotion?'auto':'smooth',block:'start'});
  }
  searchInput.addEventListener('input',()=>{state.query=safe(searchInput.value);state.page=1;draw(false,'replace');});
  categorySelect.addEventListener('change',()=>{state.category=categorySelect.value;state.page=1;draw(false,'replace');});
  yearSelect.addEventListener('change',()=>{state.year=yearSelect.value;state.page=1;draw(false,'replace');});
  sortSelect.addEventListener('change',()=>{state.sort=sortSelect.value;state.page=1;draw(false,'replace');});
  addEventListener('popstate',()=>{state=readURL();draw(false,'');});
  const compactQuery = typeof matchMedia === 'function' ? matchMedia('(max-width: 640px)') : null;
  if (compactQuery) compactQuery.addEventListener('change',()=>draw(false,''));
  draw(false,'');
})();