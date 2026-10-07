/* Control Flex Wiki — language toggle, sidebar, active nav, copy buttons.
   Loaded with `defer`, so the DOM is parsed by the time this runs. */
(function () {
  var LANG_KEY = 'preferredLang';

  /* ---------- languages ----------
     To add a language: add its code to LANGS here, add a matching <option> to
     the language <select> in every page header, and wrap the new translations
     in [data-lang="xx"] blocks. Visibility rules are injected below for every
     entry, so the CSS in style.css never has to be edited for new languages
     (it only carries static fallback rules for no-JS visitors). */
  var LANGS = ['en', 'zh'];

  (function injectLangCss() {
    var css = LANGS.map(function (l) {
      return 'html[lang="' + l + '"] [data-lang]:not([data-lang="' + l + '"]) { display: none !important; }';
    }).join('\n');
    var style = document.createElement('style');
    style.textContent = css;
    document.head.appendChild(style);
  })();

  /* Fall back to the first supported language when the stored or
     auto-detected language has no content yet. */
  if (LANGS.indexOf(document.documentElement.lang) === -1) {
    document.documentElement.lang = LANGS[0];
  }

  var langSelect = document.getElementById('lang-select');
  if (langSelect) {
    langSelect.value = document.documentElement.lang;
    langSelect.addEventListener('change', function () {
      var next = langSelect.value;
      if (LANGS.indexOf(next) === -1) next = LANGS[0];
      document.documentElement.lang = next;
      try { localStorage.setItem(LANG_KEY, next); } catch (e) { /* private mode */ }
    });
  }

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
