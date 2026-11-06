/* Campus representative film: reveal only after the actual MP4 is publicly available. */
(() => {
  'use strict';
  const section = document.getElementById('campus-film');
  const player = section?.querySelector('video');
  const source = player?.querySelector('source');
  if (!section || !player || !source) return;

  const videoUrl = '/assets/media/department-campus-a-v11.mp4';
  fetch(videoUrl, { method: 'HEAD' })
    .then(response => {
      const contentType = response.headers.get('content-type') || '';
      if (!response.ok || contentType.includes('text/html')) return;
      source.src = videoUrl;
      section.hidden = false;
      player.load();

      let started = false;
      let completed = false;
      player.addEventListener('play', () => {
        if (!started) {
          started = true;
          window.gtag?.('event', 'department_video_play', { video_id: 'campus_film_v11' });
        }
      });
      player.addEventListener('ended', () => {
        if (!completed) {
          completed = true;
          window.gtag?.('event', 'department_video_complete', { video_id: 'campus_film_v11' });
        }
      });
      player.addEventListener('error', () => { section.hidden = true; });
    })
    .catch(() => { /* No unfinished or broken player should be displayed. */ });
})();
