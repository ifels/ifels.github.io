document.getElementById('sidebar').classList.add('open');
document.body.classList.add('nav-open');
setTimeout(function () {
  var sb = document.getElementById('sidebar');
  var chain = [];
  var el = sb;
  while (el && el !== document.documentElement) {
    var cs = getComputedStyle(el);
    var flag = '';
    if (cs.transform !== 'none') flag += ' transform=' + cs.transform;
    if (cs.filter !== 'none') flag += ' filter=' + cs.filter;
    if (cs.willChange && cs.willChange !== 'auto') flag += ' willChange=' + cs.willChange;
    if (cs.perspective !== 'none') flag += ' persp=' + cs.perspective;
    if (cs.contain && cs.contain !== 'none') flag += ' contain=' + cs.contain;
    if (cs.backdropFilter && cs.backdropFilter !== 'none') flag += ' bdf=' + cs.backdropFilter;
    chain.push(el.tagName + '.' + (el.className && el.className.baseVal !== undefined ? '' : el.className || '') + flag);
    el = el.parentElement;
  }
  var rules = [];
  try {
    for (var s = 0; s < document.styleSheets.length; s++) {
      var rs = document.styleSheets[s].cssRules;
      for (var i = 0; i < rs.length; i++) {
        var r = rs[i];
        if (r.selectorText && r.style && (r.style.transform || r.style.top !== '' || r.style.bottom !== '' || r.style.position)) {
          try { if (sb.matches(r.selectorText)) {
            rules.push(r.selectorText + ' {pos=' + (r.style.position||'-') + ' top=' + (r.style.top||'-') + ' bottom=' + (r.style.bottom||'-') + ' tf=' + (r.style.transform||'-') + '}');
          } } catch (e) {}
        }
        if (r.cssRules) {
          for (var j = 0; j < r.cssRules.length; j++) {
            var r2 = r.cssRules[j];
            if (r2.selectorText && r2.style && (r2.style.transform || r2.style.top !== '' || r2.style.bottom !== '' || r2.style.position)) {
              try { if (sb.matches(r2.selectorText)) {
                rules.push('@' + (r.conditionText||'') + ' ' + r2.selectorText + ' {pos=' + (r2.style.position||'-') + ' top=' + (r2.style.top||'-') + ' bottom=' + (r2.style.bottom||'-') + ' tf=' + (r2.style.transform||'-') + '}');
              } } catch (e) {}
            }
          }
        }
      }
    }
  } catch (e) { rules.push('ERR ' + e.message); }
  var rect = sb.getBoundingClientRect();
  var max = sb.scrollHeight - sb.clientHeight;
  document.title = rules.join('
') + '
RECT ' + JSON.stringify({t: rect.top, b: rect.bottom, h: rect.height, w: rect.width});
  sb.scrollTop = 400;
  var r = document.createElement('div');
  r.style.cssText = 'position:fixed;right:6px;bottom:6px;z-index:999;background:#ffec99;color:#000;font:12px/1.5 monospace;padding:6px 10px;border-radius:6px;max-width:360px';
  r.textContent = 'max=' + max + ' | ch=' + sb.clientHeight + ' sh=' + sb.scrollHeight + ' oh=' + sb.offsetHeight + ' ih=' + window.innerHeight + ' dch=' + document.documentElement.clientHeight + ' navH=' + sb.querySelector('nav').offsetHeight + ' | overflowY=' + getComputedStyle(sb).overflowY + ' | scrolledTo=' + sb.scrollTop +
    ' | bodyOverflow=' + getComputedStyle(document.body).overflow +
    ' | overscroll=' + getComputedStyle(sb).overscrollBehavior +
    ' | pos=' + getComputedStyle(sb).position + ' | RULES=' + document.title;
  document.body.appendChild(r);
}, 1500);
