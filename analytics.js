(() => {
  'use strict';
  const measurementId = 'G-WN99333WLX';
  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
  // GA4 retains acquisition UTM parameters; canonicals are generated separately without query strings.
  window.gtag('js', new Date());
  window.gtag('config', measurementId, {cookie_domain:'auto'});
  const track = (name, params = {}) => window.gtag('event', name, params);
  const eventForLink = link => {
    const href=link.getAttribute('href') || '';
    if (href.startsWith('tel:')) return 'admission_phone_click';
    let url;try {url=new URL(link.href,location.href);} catch {return null;}
    if (link.hasAttribute('data-admission-link')) return link.getAttribute('data-admission-phase')==='open' ? 'admission_apply_click' : 'admission_guide_click';
    if (url.hostname==='apply.jinhakapply.com') return 'admission_apply_click';
    if (url.hostname==='open.kakao.com') return 'admission_kakao_click';
    if (url.hostname==='portfolio.k-bigdata.kr') return 'portfolio_click';
    if (url.hostname==='contest.k-bigdata.kr' || (url.hostname===location.hostname && url.pathname.startsWith('/projects/'))) return 'project_click';
    if (url.hostname===location.hostname && url.pathname.startsWith('/employment/')) return 'employment_click';
    if (url.hostname===location.hostname && (url.pathname.startsWith('/admission/') || url.hash==='#admission')) return 'admission_guide_click';
    if (['www.kopo.ac.kr','kopo.ac.kr'].includes(url.hostname)) {
      if (url.searchParams.get('menu')==='1547') return 'official_department_click';
      if (['321','1714'].includes(url.searchParams.get('menu')) || url.pathname.includes('Download.do')) return 'admission_guide_click';
    }
    if (['youtube.com','www.youtube.com','youtu.be'].includes(url.hostname)) return 'youtube_click';
    return null;
  };
  document.addEventListener('click',event=>{
    const link=event.target.closest?.('a');if(!link)return;
    const name=eventForLink(link);if(!name)return;
    const area=link.closest('.mobile-apply')?'mobile_cta':link.closest('header')?'header':link.closest('footer')?'footer':'content';
    // No URL, text, name, phone, email, student identifier or user input in event parameters.
    track(name,{click_area:area});
  });
  const seen=new Set();let queued=false;
  window.addEventListener('scroll',()=>{
    if(queued)return;queued=true;
    requestAnimationFrame(()=>{queued=false;const available=document.documentElement.scrollHeight-innerHeight;if(available<=0)return;
      const progress=scrollY/available*100;
      [50,90].forEach(level=>{if(progress>=level&&!seen.has(level)){seen.add(level);track(`scroll_${level}`);}});
    });
  },{passive:true});
  document.addEventListener('toggle',event=>{if(event.target.matches?.('details')&&event.target.open)track('faq_open');},true);
  if(location.pathname.startsWith('/admission/2027/'))track('admission_page_view');
})();
