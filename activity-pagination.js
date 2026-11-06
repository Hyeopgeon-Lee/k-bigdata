/* Search 290 activity records without inserting them into the initial DOM.
   The first 12 cards and real page links are rendered statically for no-JS users. */
(() => {
  'use strict';
  const grid=document.querySelector('.activity-card-grid');
  const heading=document.querySelector('.activity-list-heading');
  if(!grid || !heading) return;
  const PAGE_SIZE=12;
  const staticNav=document.querySelector('.archive-static-pagination');
  const panel=document.createElement('div');
  panel.className='activity-toolbar activity-toolbar-compact';
  panel.setAttribute('role','search');
  panel.setAttribute('aria-label','학과 활동 검색');
  panel.innerHTML='<div class="activity-toolbar-fields">'
    +'<label class="activity-search"><span>활동 검색</span><input type="search" maxlength="80" placeholder="수상, 취업, AI, 기업명 검색" autocomplete="off" /></label>'
    +'<label class="activity-select-wrap"><span>분야</span><select data-filter="category"><option value="all">전체 분야</option></select></label>'
    +'<label class="activity-select-wrap"><span>연도</span><select data-filter="year"><option value="all">전체 연도</option></select></label>'
    +'<label class="activity-select-wrap"><span>정렬</span><select data-filter="sort"><option value="new">최신순</option><option value="old">오래된순</option></select></label>'
    +'</div><div class="activity-toolbar-footer"><p class="activity-match-hint" role="status" aria-live="polite">전체 학과 활동을 검색할 수 있습니다.</p>'
    +'<button type="button" class="activity-clear-filters">초기화</button></div>';
  heading.insertAdjacentElement('afterend',panel);
  const query=panel.querySelector('input[type=search]');
  const category=panel.querySelector('[data-filter=category]');
  const year=panel.querySelector('[data-filter=year]');
  const sort=panel.querySelector('[data-filter=sort]');
  const status=panel.querySelector('.activity-match-hint');
  const clear=panel.querySelector('.activity-clear-filters');
  const dynamicNav=document.createElement('nav');
  dynamicNav.className='activity-pagination';
  dynamicNav.setAttribute('aria-label','검색 결과 페이지');
  dynamicNav.hidden=true;
  if(staticNav)staticNav.insertAdjacentElement('afterend',dynamicNav);
  else grid.after(dynamicNav);
  const p=new URLSearchParams(location.search);
  const state={q:(p.get('q')||'').slice(0,80),category:p.get('category')||'all',
    year:p.get('year')||'all',sort:p.get('sort')==='old'?'old':'new',
    page:Math.max(1,parseInt(p.get('page')||'1',10)||1)};
  let rows=[],ready=false,queryDelay;
  const make=(tag,cls,value)=>{
    const x=document.createElement(tag);
    if(cls)x.className=cls;
    if(value!==undefined)x.textContent=String(value);
    return x;
  };
  function makeCard(r){
    const card=make('article','activity-card'),visual=make('a','activity-image-link');
    visual.href=r.url;visual.setAttribute('aria-label',r.title+' 자세히 보기');
    const img=document.createElement('img');
    img.src=r.image;img.alt=r.alt||'';img.loading='lazy';img.decoding='async';
    img.width=r.width||600;img.height=r.height||450;visual.append(img);
    const body=make('div','activity-card-body'),meta=make('div','activity-card-meta');
    const dt=make('time','',r.date.replaceAll('-','.'));dt.dateTime=r.date;
    meta.append(make('span','',r.category),dt);
    const title=make('h3',''),a=make('a','',r.title);a.href=r.url;title.append(a);
    const more=make('a','activity-read-more','활동 자세히 보기 →');more.href=r.url;
    body.append(meta,title,make('p','',r.summary),more);card.append(visual,body);
    return card;
  }
  function updateURL(){
    const q=new URLSearchParams();
    if(state.q.trim())q.set('q',state.q.trim());
    if(state.category!=='all')q.set('category',state.category);
    if(state.year!=='all')q.set('year',state.year);
    if(state.sort!=='new')q.set('sort',state.sort);
    if(state.page>1)q.set('page',String(state.page));
    history.replaceState({},'','/activities/'+(q.size?'?'+q.toString():'')+'#activity-archive');
  }
  function draw(){
    if(!ready)return;
    query.value=state.q;category.value=state.category;
    year.value=state.year;sort.value=state.sort;
    const words=state.q.toLocaleLowerCase('ko').trim().split(/\s+/).filter(Boolean);
    let results=rows.filter(r=>
      (state.category==='all'||r.category===state.category) &&
      (state.year==='all'||r.date.startsWith(state.year)) &&
      words.every(w=>(r.title+' '+r.summary+' '+r.category).toLocaleLowerCase('ko').includes(w))
    );
    if(state.sort==='old')results=[...results].reverse();
    const pages=Math.max(1,Math.ceil(results.length/PAGE_SIZE));
    state.page=Math.min(state.page,pages);
    grid.replaceChildren(...results.slice((state.page-1)*PAGE_SIZE,state.page*PAGE_SIZE).map(makeCard));
    status.textContent=results.length?results.length+'건 · '+state.page+' / '+pages+'페이지':'검색 결과가 없습니다.';
    const group=make('div','activity-page-buttons');
    function pageButton(label,n,disabled,selected){
      const b=make('button','activity-page-button',label);
      b.type='button';b.disabled=disabled;
      if(selected)b.setAttribute('aria-current','page');
      b.addEventListener('click',()=>{state.page=n;updateURL();draw();panel.scrollIntoView({behavior:'instant',block:'start'});});
      group.append(b);
    }
    if(pages>1){
      pageButton('이전',state.page-1,state.page===1,false);
      const compact=matchMedia('(max-width: 640px)').matches;
      const start=Math.max(1,state.page-(compact?0:2));
      const end=Math.min(pages,start+(compact?0:4));
      if(start>1)pageButton('1',1,false,false);
      for(let n=start;n<=end;n++)pageButton(String(n),n,false,n===state.page);
      if(end<pages)pageButton(String(pages),pages,false,false);
      pageButton('다음',state.page+1,state.page===pages,false);
    }
    dynamicNav.replaceChildren(group);dynamicNav.hidden=pages<=1;
    if(staticNav)staticNav.hidden=true;clear.hidden=false;
  }
  const change=()=>{
    state.q=query.value.slice(0,80);state.category=category.value;
    state.year=year.value;state.sort=sort.value;state.page=1;
    updateURL();draw();
  };
  query.addEventListener('input',()=>{clearTimeout(queryDelay);queryDelay=setTimeout(change,140);});
  [category,year,sort].forEach(el=>el.addEventListener('change',change));
  clear.addEventListener('click',()=>{location.href='/activities/#activity-archive';});
  clear.hidden=true;
  fetch('/assets/data/activity-index.json',{headers:{Accept:'application/json'}})
    .then(r=>{if(!r.ok)throw new Error('Search index unavailable');return r.json();})
    .then(data=>{
      if(!Array.isArray(data)||!data.length)throw new Error('Empty search index');
      rows=data;
      const cats=[...new Set(rows.map(r=>r.category))].sort((a,b)=>a.localeCompare(b,'ko'));
      const years=[...new Set(rows.map(r=>r.date.slice(0,4)))].sort().reverse();
      cats.forEach(v=>{const op=make('option','',v);op.value=v;category.append(op);});
      years.forEach(v=>{const op=make('option','',v+'년');op.value=v;year.append(op);});
      ready=true;
      if(!cats.includes(state.category))state.category='all';
      if(!years.includes(state.year))state.year='all';
      if(state.q||state.category!=='all'||state.year!=='all'||state.sort!=='new'||p.has('page'))draw();
      else status.textContent='총 '+rows.length+'건 · 페이지당 '+PAGE_SIZE+'건 표시';
    })
    .catch(()=>{
      status.textContent='검색 연결이 지연 중입니다. 아래 페이지 링크로 전체 활동을 살펴보세요.';
      [query,category,year,sort].forEach(x=>x.disabled=true);
    });
})();
