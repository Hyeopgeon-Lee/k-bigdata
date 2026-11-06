/* Department introduction video: native HTML source is the playback fallback.
   This script only improves cover interaction and measures voluntary playback. */
(() => {
  'use strict';
  const section = document.getElementById('campus-film');
  const player = section?.querySelector('video');
  const source = player?.querySelector('source');
  const playButton = section?.querySelector('.campus-film-play');
  if (!section || !player || !source) return;
  // The MP4 URL is deliberately defined in HTML: the video must play without JS.
  player.preload = 'none';
  const caption = section.querySelector('.campus-film-caption');
  const showFailure = () => {
    if (caption) {
      caption.innerHTML = '영상 재생에 문제가 발생했습니다. <a href="/assets/media/department-campus-a-v11.mp4" target="_blank" rel="noopener noreferrer">영상 파일 직접 열기</a>';
    }
  };
  if (playButton) {
    const wrapper = playButton.closest('.campus-film-player');
    wrapper?.classList.add('is-interactive');
    playButton.addEventListener('click', () => {
      const playResult = player.play();
      if (playResult && typeof playResult.catch === 'function') {
        playResult.catch(showFailure);
      }
    });
    player.addEventListener('playing', () => wrapper?.classList.add('is-started'));
  }
  let started = false, completed = false;
  player.addEventListener('play', () => {
    if (started) return;
    started = true;
    window.gtag?.('event', 'department_video_play', {video_id: 'campus_film_v11'});
  });
  player.addEventListener('ended', () => {
    if (completed) return;
    completed = true;
    window.gtag?.('event', 'department_video_complete', {video_id: 'campus_film_v11'});
  });
  player.addEventListener('error', showFailure);
  source.addEventListener('error', showFailure);
})();
