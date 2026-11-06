/* Always-visible, layout-stable department introduction film.
   The site owns both the MP4 and WebP cover, so extra HEAD requests are unnecessary. */
(() => {
  'use strict';
  const section = document.getElementById('campus-film');
  const player = section?.querySelector('video');
  const source = player?.querySelector('source');
  if (!section || !player || !source) return;
  source.src = '/assets/media/department-campus-a-v11.mp4';
  player.preload = 'none';
  // Native controls load the MP4 on demand; calling load() eagerly triggers a
  // range request on Chrome even with preload=none.
  let started = false, completed = false;
  player.addEventListener('play', () => {
    if (started) return;
    started = true;
    window.gtag?.('event', 'department_video_play', {video_id:'campus_film_v11'});
  });
  player.addEventListener('ended', () => {
    if (completed) return;
    completed = true;
    window.gtag?.('event', 'department_video_complete', {video_id:'campus_film_v11'});
  });
  player.addEventListener('error', () => {
    const caption = section.querySelector('.campus-film-caption');
    if (caption) caption.textContent = '영상 재생에 문제가 발생했습니다. 학과 소개와 입학안내는 위 링크에서 확인해 주세요.';
  });
})();
