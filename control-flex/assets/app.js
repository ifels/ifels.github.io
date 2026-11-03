/* Control Flex Wiki — sidebar, active nav, copy buttons, language preference.
   Loaded with `defer`, so the DOM is parsed by the time this runs.

   Each language is a separate static tree (/en/..., /zh/...). Switching
   languages is a normal navigation, so there is nothing to swap at runtime;
   this file only remembers the visitor's choice so the redirect stubs that
   catch legacy URLs can honour it. */
(function () {
  var LANG_KEY = 'preferredLang';

  document.querySelectorAll('a[data-set-lang]').forEach(function (a) {
    a.addEventListener('click', function () {
      try { localStorage.setItem(LANG_KEY, a.getAttribute('data-set-lang')); } catch (e) { /* private mode */ }
    });
  });

  /* ---------- mobile sidebar ---------- */
  var sidebar = document.getElementById('sidebar');
  var navToggle = document.getElementById('nav-toggle');
  var backdrop = document.createElement('div');
  backdrop.className = 'backdrop';
  document.body.appendChild(backdrop);

  function closeNav() {
    if (sidebar) sidebar.classList.remove('open');
    backdrop.classList.remove('show');
  }
  if (navToggle && sidebar) {
    navToggle.addEventListener('click', function () {
      sidebar.classList.toggle('open');
      backdrop.classList.toggle('show');
    });
  }
  backdrop.addEventListener('click', closeNav);
  window.addEventListener('hashchange', closeNav);

  /* ---------- highlight the current page in the sidebar ---------- */
  function normPath(p) {
    return p.slice(-1) === '/' ? p + 'index.html' : p;
  }
  document.querySelectorAll('.sidebar a[href]').forEach(function (a) {
    try {
      var target = new URL(a.getAttribute('href'), location.href);
      if (target.origin === location.origin && normPath(target.pathname) === normPath(location.pathname)) {
        a.classList.add('active');
      }
    } catch (e) { /* ignore */ }
  });

  /* ---------- copy buttons on code blocks ---------- */
  function fallbackCopy(text, done) {
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand('copy'); } catch (e) { /* ignore */ }
    document.body.removeChild(ta);
    done();
  }

  document.querySelectorAll('pre').forEach(function (pre) {
    var b = document.createElement('button');
    b.type = 'button';
    b.className = 'copy-btn';
    b.textContent = 'Copy';
    b.addEventListener('click', function () {
      var code = pre.querySelector('code');
      var text = code ? code.innerText : pre.innerText;
      function done() {
        b.textContent = '✓';
        setTimeout(function () { b.textContent = 'Copy'; }, 1200);
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () { fallbackCopy(text, done); });
      } else {
        fallbackCopy(text, done);
      }
    });
    pre.appendChild(b);
  });
})();
