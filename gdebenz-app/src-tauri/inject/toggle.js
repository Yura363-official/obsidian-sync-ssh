// GdeBenz: плавающая кнопка переключения между gdebenz.ru и gdebenz.org
(function () {
  if (window.__GDEBENZ_TOGGLE__) return;
  window.__GDEBENZ_TOGGLE__ = true;

  function ready(fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }

  ready(function () {
    var isRu = /(^|\.)gdebenz\.ru$/.test(location.hostname);
    var btn = document.createElement('button');
    btn.id = '__gdebenz_toggle_btn';
    btn.type = 'button';
    btn.textContent = isRu ? '⇄ gdebenz.org' : '⇄ gdebenz.ru';
    btn.title = isRu
      ? 'Переключиться на gdebenz.org'
      : 'Переключиться на gdebenz.ru';
    btn.style.cssText = [
      'position:fixed',
      'right:16px',
      'bottom:16px',
      'z-index:2147483647',
      'padding:10px 16px',
      'border-radius:999px',
      'border:1px solid #d4af37',
      'background:#10121a',
      'color:#d4af37',
      'font:600 14px/1 system-ui,-apple-system,sans-serif',
      'cursor:pointer',
      'box-shadow:0 4px 14px rgba(0,0,0,.35)',
      'opacity:.92'
    ].join(';');
    btn.addEventListener('mouseenter', function () { btn.style.opacity = '1'; });
    btn.addEventListener('mouseleave', function () { btn.style.opacity = '.92'; });
    btn.addEventListener('click', function () {
      location.href = isRu ? 'https://gdebenz.org/' : 'https://gdebenz.ru/';
    });
    document.body.appendChild(btn);
  });
})();
