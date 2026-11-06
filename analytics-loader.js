/* Homepage-only GA4 loader: let the hero finish painting before loading
   the 180KB gtag library on narrow screens. analytics.js immediately installs
   the dataLayer queue and the privacy-preserving click event handlers.
   First genuine interaction starts the loader without waiting for the timer.
   Admission and other destination pages retain their normal eager GA4 setup. */
(() => {
  'use strict';
  const ID = 'G-WN99333WLX';
  let started = false;
  function start() {
    if (started) return;
    started = true;
    const script = document.createElement('script');
    script.async = true;
    script.src = 'https://www.googletagmanager.com/gtag/js?id=' + ID;
    script.setAttribute('data-ga4-loader', 'home');
    document.head.appendChild(script);
  }
  // Prompt interaction (tap, click or keyboard) is more important than the
  // passive optimization timer. Keep analytic events queued in dataLayer.
  document.addEventListener('pointerdown', start, {capture:true, passive:true, once:true});
  document.addEventListener('keydown', start, {capture:true, once:true});
  const schedule = () => {
    const narrow = window.matchMedia?.('(max-width: 700px)').matches;
    // The hero is generally painted by this point; shorten the gap to count
    // brief visits while keeping the large GA4 evaluation off critical paint.
    window.setTimeout(start, narrow ? 1300 : 0);
  };
  if (document.readyState === 'complete') schedule();
  else window.addEventListener('load', schedule, {once:true});
})();
