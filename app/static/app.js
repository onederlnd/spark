// --- theme ---
function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem("spark-theme", theme);
  const isDark = theme === "dark";
  const icon = isDark ? "🌙" : "☀️";
  const label = isDark ? "Light" : "Dark";
  const drawerLabel = isDark ? "Switch to Light" : "Switch to Dark";
  document.getElementById("themeIcon").textContent = icon;
  document.getElementById("themeLabel").textContent = label;
  document.getElementById("drawerThemeIcon").textContent = icon;
  document.getElementById("drawerThemeLabel").textContent = drawerLabel;
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "dark";
  applyTheme(current === "dark" ? "light" : "dark");
}

(function () {
  const t = localStorage.getItem("spark-theme") || "dark";
  applyTheme(t);
})();

// --- drawer ---
function openDrawer() {
  const overlay = document.getElementById("drawerOverlay");
  const drawer = document.getElementById("drawer");
  overlay.style.display = "block";
  requestAnimationFrame(() => {
    overlay.classList.add("open");
    drawer.classList.add("open");
  });
  document.body.style.overflow = "hidden";
}

function closeDrawer() {
  const overlay = document.getElementById("drawerOverlay");
  const drawer = document.getElementById("drawer");
  overlay.classList.remove("open");
  drawer.classList.remove("open");
  document.body.style.overflow = "";
  setTimeout(() => {
    overlay.style.display = "none";
  }, 250);
}

document.addEventListener("keydown", e => {
  if (e.key === "Escape") closeDrawer();
});

// --- flash auto-dismiss ---
setTimeout(() => {
  document.querySelectorAll('.flash').forEach(el => {
    el.style.transition = 'opacity 0.4s ease';
    el.style.opacity = '0';
    setTimeout(() => el.remove(), 400);
  });
}, 3000);

// --- avatar menu ---
function toggleAvatarMenu() {
  const menu = document.getElementById('avatar-menu');
  if (menu) menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
}

document.addEventListener('click', function (e) {
  const wrap = document.querySelector('.nav-avatar-wrap');
  if (wrap && !wrap.contains(e.target)) {
    const menu = document.getElementById('avatar-menu');
    if (menu) menu.style.display = 'none';
  }
});

// --- bbcode toolbar ---
document.addEventListener("click", function (e) {
  const btn = e.target.closest(".bb-btn");
  if (!btn) return;

  const toolbar = btn.closest(".bbcode-toolbar");
  if (!toolbar) return;
  const targetId = toolbar.dataset.target;
  const textarea = document.getElementById(targetId);
  if (!textarea) return;

  const open = btn.dataset.open;
  const close = btn.dataset.close;
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  const selected = textarea.value.slice(start, end);

  let insertion, cursorPos;
  if (open === "[url=]") {
    insertion = `[url=]${selected}[/url]`;
    cursorPos = start + 5;
  } else {
    insertion = open + selected + close;
    cursorPos = selected.length ? start + insertion.length : start + open.length;
  }

  textarea.value = textarea.value.slice(0, start) + insertion + textarea.value.slice(end);
  textarea.focus();
  textarea.setSelectionRange(cursorPos, cursorPos);
  textarea.dispatchEvent(new Event("input"));
});

// --- child avatars ---
document.querySelectorAll('.child-avatar').forEach(el => {
  el.style.background = el.dataset.bg;
});

// --- post type tabs ---
function setPostType(type) {
  document.getElementById('post_type').value = type;

  const tabPost = document.getElementById('tab-post');
  const tabAnn = document.getElementById('tab-announcement');
  const annFields = document.getElementById('announcement-fields');
  const topicField = document.getElementById('topic-field');
  const submitBtn = document.getElementById('submit-btn');
  const classroomSelect = document.getElementById('classroom_id');

  if (type === 'announcement') {
    tabPost.style.background = 'transparent';
    tabPost.style.color = 'var(--muted)';
    tabPost.style.borderColor = 'var(--border)';
    tabAnn.style.background = 'var(--teal)';
    tabAnn.style.color = 'white';
    tabAnn.style.borderColor = 'var(--teal)';
    annFields.style.display = 'block';
    topicField.style.display = 'none';
    if (classroomSelect) classroomSelect.required = true;
    submitBtn.textContent = 'Post Announcement 📢';
    submitBtn.style.background = 'var(--teal)';
  } else {
    tabPost.style.background = 'var(--blue)';
    tabPost.style.color = 'white';
    tabPost.style.borderColor = 'var(--blue)';
    tabAnn.style.background = 'transparent';
    tabAnn.style.color = 'var(--muted)';
    tabAnn.style.borderColor = 'var(--border)';
    annFields.style.display = 'none';
    topicField.style.display = 'block';
    if (classroomSelect) classroomSelect.required = false;
    submitBtn.textContent = 'Post ✦';
    submitBtn.style.background = 'var(--blue)';
  }
}

// --- mention autocomplete ---
(function () {
  let mentionDropdown = null;
  let activeTextarea = null;
  let mentionStart = -1;

  function createDropdown() {
    const el = document.createElement('div');
    el.id = 'mention-dropdown';
    el.style.cssText = `
      position: fixed;
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      box-shadow: var(--shadow-lg);
      z-index: 9999;
      min-width: 180px;
      max-width: 260px;
      overflow: hidden;
      display: none;
    `;
    document.body.appendChild(el);
    return el;
  }

  function getDropdown() {
    return document.getElementById('mention-dropdown') || createDropdown();
  }

  function hideDropdown() {
    const d = getDropdown();
    d.style.display = 'none';
    d.innerHTML = '';
    mentionStart = -1;
    activeTextarea = null;
  }

  function showDropdown(textarea, users) {
    const d = getDropdown();
    if (!users.length) { hideDropdown(); return; }

    d.innerHTML = '';
    users.forEach(username => {
      const item = document.createElement('div');
      item.style.cssText = `
        padding: 8px 14px;
        cursor: pointer;
        font-size: 0.88rem;
        font-weight: 600;
        color: var(--text);
        font-family: var(--font);
        transition: background 0.1s;
      `;
      item.textContent = '@' + username;
      item.addEventListener('mouseenter', () => item.style.background = 'var(--sky)');
      item.addEventListener('mouseleave', () => item.style.background = '');
      item.addEventListener('mousedown', (e) => {
        e.preventDefault();
        insertMention(textarea, username);
      });
      d.appendChild(item);
    });

    const coords = getCaretCoords(textarea, mentionStart);
    const rect = textarea.getBoundingClientRect();
    d.style.display = 'block';
    d.style.left = (rect.left + coords.left) + 'px';
    d.style.top = (rect.top + coords.top + 20) + 'px';
  }

  function insertMention(textarea, username) {
    const val = textarea.value;
    const before = val.slice(0, mentionStart);
    const after = val.slice(textarea.selectionStart);
    textarea.value = before + '@' + username + ' ' + after;
    const pos = mentionStart + username.length + 2;
    textarea.setSelectionRange(pos, pos);
    textarea.dispatchEvent(new Event('input'));
    hideDropdown();
    textarea.focus();
  }

  function getCaretCoords(textarea, position) {
    const mirror = document.createElement('div');
    const style = window.getComputedStyle(textarea);
    ['fontFamily','fontSize','fontWeight','lineHeight','padding',
     'border','boxSizing','width','whiteSpace','wordWrap'].forEach(p => {
      mirror.style[p] = style[p];
    });
    mirror.style.position = 'absolute';
    mirror.style.visibility = 'hidden';
    mirror.style.whiteSpace = 'pre-wrap';
    mirror.style.top = '0';
    mirror.style.left = '0';
    document.body.appendChild(mirror);

    const text = textarea.value.slice(0, position);
    mirror.textContent = text;
    const span = document.createElement('span');
    span.textContent = '|';
    mirror.appendChild(span);

    const coords = { left: span.offsetLeft, top: span.offsetTop };
    document.body.removeChild(mirror);
    return coords;
  }

  async function fetchUsers(query) {
    try {
      const res = await fetch(`/api/users/search?q=${encodeURIComponent(query)}`);
      return await res.json();
    } catch { return []; }
  }

  let debounceTimer = null;

  document.addEventListener('input', async (e) => {
    const textarea = e.target;
    if (textarea.tagName !== 'TEXTAREA') return;

    const val = textarea.value;
    const pos = textarea.selectionStart;

    let start = -1;
    for (let i = pos - 1; i >= 0; i--) {
      if (val[i] === '@') { start = i; break; }
      if (/\s/.test(val[i])) break;
    }

    if (start === -1) { hideDropdown(); return; }

    const query = val.slice(start + 1, pos);
    if (query.length === 0) { hideDropdown(); return; }
    if (!/^[\w.-]+$/.test(query)) { hideDropdown(); return; }

    mentionStart = start;
    activeTextarea = textarea;

    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(async () => {
      const users = await fetchUsers(query);
      showDropdown(textarea, users);
    }, 150);
  });

  document.addEventListener('keydown', (e) => {
    const d = getDropdown();
    if (d.style.display === 'none') return;
    const items = d.querySelectorAll('div');
    const active = d.querySelector('div[data-active]');
    const idx = active ? [...items].indexOf(active) : -1;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (active) active.removeAttribute('data-active');
      const next = items[idx + 1] || items[0];
      next.setAttribute('data-active', '1');
      next.style.background = 'var(--sky)';
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (active) active.removeAttribute('data-active');
      const prev = items[idx - 1] || items[items.length - 1];
      prev.setAttribute('data-active', '1');
      prev.style.background = 'var(--sky)';
    } else if (e.key === 'Enter' || e.key === 'Tab') {
      if (active && activeTextarea) {
        e.preventDefault();
        const username = active.textContent.slice(1);
        insertMention(activeTextarea, username);
      }
    } else if (e.key === 'Escape') {
      hideDropdown();
    }
  });

  document.addEventListener('click', (e) => {
    if (!e.target.closest('#mention-dropdown')) hideDropdown();
  });
  window.addEventListener('scroll', hideDropdown, true);

})();

// --- mention highlight ---
function initMentionHighlight(textarea) {
  const highlight = document.createElement('div');
  highlight.className = 'mention-highlight-bg';
  highlight.setAttribute('aria-hidden', 'true');
  document.body.appendChild(highlight);

  textarea.classList.add('mention-active');
  textarea.style.background = 'transparent';

  function sync() {
    const rect = textarea.getBoundingClientRect();
    const cs = window.getComputedStyle(textarea);
    highlight.style.cssText = `
      position: fixed;
      top: ${rect.top}px;
      left: ${rect.left}px;
      width: ${rect.width}px;
      height: ${rect.height}px;
      pointer-events: none;
      margin: 0;
      color: transparent;
      background: transparent;
      border: ${cs.borderWidth} solid transparent;
      overflow: hidden;
      white-space: pre-wrap;
      word-wrap: break-word;
      z-index: 0;
      font-family: ${cs.fontFamily};
      font-size: ${cs.fontSize};
      font-weight: ${cs.fontWeight};
      line-height: ${cs.lineHeight};
      padding: ${cs.padding};
      letter-spacing: ${cs.letterSpacing};
      border-radius: ${cs.borderRadius};
      box-sizing: border-box;
    `;

    const escaped = textarea.value
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
    highlight.innerHTML = escaped.replace(
      /@([\w.-]+)/g,
      '<mark class="mention-preview">@$1</mark>'
    );
    highlight.scrollTop = textarea.scrollTop;
  }

  textarea.addEventListener('input', sync);
  textarea.addEventListener('scroll', () => { highlight.scrollTop = textarea.scrollTop; });
  window.addEventListener('scroll', sync, true);
  window.addEventListener('resize', sync);
  sync();
}

document.querySelectorAll('textarea').forEach(initMentionHighlight);