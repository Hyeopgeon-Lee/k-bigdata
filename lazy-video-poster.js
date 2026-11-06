/* Load each video cover shortly before it enters view, not during hero paint.
   Both videos retain native controls and preload=none; JS-disabled visitors can
   still play the education video from its existing <source> element. */
(() => {
  'use strict';
  const videos = [...document.querySelectorAll('video[data-lazy-poster]')];
  if (!videos.length) return;

  function showCover(video) {
    const url = video.getAttribute('data-lazy-poster');
    if (!url) return;
    video.poster = url;
    video.removeAttribute('data-lazy-poster');
  }
  if (!('IntersectionObserver' in window)) {
    videos.forEach(showCover);
    return;
  }
  const observer = new IntersectionObserver((entries, watcher) => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      showCover(entry.target);
      watcher.unobserve(entry.target);
    }
  }, {rootMargin:'80px 0px'});
  for (const video of videos) {
    observer.observe(video);
    video.addEventListener('pointerdown', () => showCover(video), {once:true, passive:true});
    video.addEventListener('focusin', () => showCover(video), {once:true});
  }
})();
