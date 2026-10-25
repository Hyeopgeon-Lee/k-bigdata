(() => {
  'use strict';
  const grid=document.querySelector('.activity-card-grid');
  if(!grid)return;
  const cards=[...grid.querySelectorAll(':scope > .activity-card')];
  const perPage=12, total=Math.ceil(cards.length/perPage);
  if(total<=1)return;
  const nav=document.createElement('nav');
  nav.className='activity-pagination';
  nav.setAttribute('aria-label','학과 활동 페이지 선택');
  const status=document.createElement('span');
  status.className='activity-page-status';
  status.setAttribute('aria-live','polite');
  const controls=document.createElement('div');
  controls.className='activity-page-buttons';
  nav.append(status,controls);
  grid.parentElement.append(nav);
  let page=1;
  function currentFromUrl(){
    const value=Number(new URLSearchParams(location.search).get('page'));
    return Number.isInteger(value)&&value>=1&&value<=total?value:1;
  }
  function makeButton(label,target,selected=false,disabled=false) {
    const button=document.createElement('button');
    button.type='button';button.className='activity-page-button'+(selected?' selected':'');
    button.textContent=label;button.disabled=disabled;
    button.setAttribute('aria-label',label==='이전'?'이전 페이지':label==='다음'?'다음 페이지':target+'페이지');
    if(selected)button.setAttribute('aria-current','page');
    if(!disabled)button.addEventListener('click',()=>draw(target,true,true));
    controls.append(button);
  }
  function draw(n,scroll=false,updateUrl=false){
    page=Math.max(1,Math.min(total,n));
    for(let i=0;i<cards.length;i++)cards[i].hidden=Math.floor(i/perPage)+1!==page;
    controls.replaceChildren();
    makeButton('이전',page-1,false,page===1);
    let start=Math.max(1,page-2),end=Math.min(total,start+4);
    start=Math.max(1,end-4);
    if(start>1){makeButton('1',1);if(start>2){const dots=document.createElement('span');dots.textContent='…';dots.className='activity-pagination-dots';controls.append(dots);}}
    for(let i=start;i<=end;i++)makeButton(String(i),i,i===page);
    if(end<total){if(end<total-1){const dots=document.createElement('span');dots.textContent='…';dots.className='activity-pagination-dots';controls.append(dots);}makeButton(String(total),total);}
    makeButton('다음',page+1,false,page===total);
    status.textContent='전체 '+cards.length+'건 · '+page+' / '+total+'페이지';
    if(updateUrl){
      const u=new URL(location.href);
      if(page===1)u.searchParams.delete('page');else u.searchParams.set('page',String(page));
      history.pushState({page},'',u.pathname+u.search+u.hash);
    }
    if(scroll)(document.querySelector('.activity-list-heading')||grid).scrollIntoView({behavior:'smooth',block:'start'});
  }
  addEventListener('popstate',()=>draw(currentFromUrl()));
  draw(currentFromUrl());
})();