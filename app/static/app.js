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
    ['fontFamily', 'fontSize', 'fontWeight', 'lineHeight', 'padding',
      'border', 'boxSizing', 'width', 'whiteSpace', 'wordWrap'].forEach(p => {
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

// --- feedback panel ---
(function () {
  const FIELDS = [
    { key: "classroom_experience", name: "Classroom experience" },
    { key: "student_engagement", name: "Student engagement" },
    { key: "ease_of_use", name: "Ease of use" },
    { key: "assignment_workflow", name: "Assignment workflow" },
    { key: "safety_moderation", name: "Safety & moderation" },
  ];

  const ratings = {};

  function starSVG(filled) {
    const fill = filled ? "var(--teal, #1d9e75)" : "none";
    const stroke = filled ? "var(--teal, #1d9e75)" : "var(--muted)";
    return `<svg viewBox="0 0 22 22" fill="${fill}" stroke="${stroke}" style="pointer-events:none;" stroke-width="1.8" xmlns="http://www.w3.org/2000/svg">
      <polygon points="11,2 13.9,8.1 20.5,8.7 15.5,13.4 17.1,19.8 11,16.3 4.9,19.8 6.5,13.4 1.5,8.7 8.1,8.1"/>
    </svg>`;
  }

  function renderStars(key) {
    const container = document.getElementById("fps-" + key);
    if (!container) return;
    const current = ratings[key] || 0;
    container.innerHTML = "";
    for (let i = 1; i <= 5; i++) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "fp-star";
      btn.setAttribute("aria-label", `${i} star`);
      btn.innerHTML = starSVG(i <= current);
      btn.onclick = function () {
        ratings[key] = i;
        renderStars(key);
      };
      container.appendChild(btn);
    }
  }

  function buildPanel() {
    const list = document.getElementById("fp-ratings");
    list.innerHTML = "";
    FIELDS.forEach(f => {
      const row = document.createElement("div");
      row.className = "fp-row";
      row.innerHTML = `
        <div class="fp-row-labels">
          <div class="fp-row-name">${f.name}</div>
        </div>
        <div class="fp-stars" id="fps-${f.key}"></div>`;
      list.appendChild(row);
      renderStars(f.key);
    });
  }

  window.openFeedback = function () {
    Object.keys(ratings).forEach(k => delete ratings[k]);
    buildPanel();
    document.getElementById("feedbackOverlay").style.display = "block";
    requestAnimationFrame(() => {
      document.getElementById("feedbackPanel").classList.add("open");
    });
  };

  window.closeFeedback = function () {
    document.getElementById("feedbackPanel").classList.remove("open");
    setTimeout(() => { document.getElementById("feedbackOverlay").style.display = "none"; }, 280);
    document.getElementById("fp-error").style.display = "none";
    document.getElementById("fp-body").style.display = "";
    document.getElementById("fp-success").style.display = "none";
    const btn = document.getElementById("fp-submit-btn");
    if (btn) { btn.disabled = false; btn.textContent = "Submit feedback"; }
  };

  window.submitFeedback = async function () {
    const missing = FIELDS.some(f => !ratings[f.key]);
    const errEl = document.getElementById("fp-error");
    if (missing) { errEl.style.display = "block"; return; }
    errEl.style.display = "none";

    const btn = document.getElementById("fp-submit-btn");
    btn.disabled = true;
    btn.textContent = "Submitting…";

    const payload = { ...ratings };
    payload.open_suggestions = document.getElementById("fp-suggestions").value.trim();
    payload.page_url = window.location.href;
    payload.page_context = document.title;

    try {
      const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
      const res = await fetch("/feedback/submit", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken
        },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        document.getElementById("fp-body").style.display = "none";
        document.getElementById("fp-success").style.display = "flex";
      } else {
        btn.disabled = false;
        btn.textContent = "Submit feedback";
        errEl.textContent = "Something went wrong — please try again.";
        errEl.style.display = "block";
      }
    } catch {
      btn.disabled = false;
      btn.textContent = "Submit feedback";
      errEl.textContent = "Network error — please check your connection.";
      errEl.style.display = "block";
    }
  };
})();

/**
 * SparK Messenger — Floating Chat Widget
 * Drop into static/messenger.js and add <script src="{{ url_for('static', filename='messenger.js') }}"></script>
 * near the bottom of base.html (after app.js).
 *
 * Requires:
 *  - /messages/          → JSON list of conversations  (GET, returns HTML — we use fetch + parse)
 *  - /messages/<id>      → conversation page (we use AJAX for messages only)
 *  - /messages/<id>/messages → JSON messages list
 *  - /messages/<id>/send → POST send message
 *
 * CSRF token read from <meta name="csrf-token"> in base.html.
 */

(function () {
  "use strict";

  // ─── Config ───────────────────────────────────────────────────────────────
  const POLL_INBOX_MS = 20_000;   // refresh inbox list
  const POLL_CHAT_MS = 4_000;    // poll for new messages in open chats
  const MAX_OPEN_CHATS = 2;        // how many chat panels can be open at once

  // ─── State ────────────────────────────────────────────────────────────────
  let inboxOpen = false;
  let conversations = [];          // [{id, title, classroom_name, unread_count, last_message_body, members}]
  let openChats = [];          // [{convId, el, pollTimer, lastMsgId, memberMap}]
  let totalUnread = 0;
  let inboxPollTimer = null;
  let csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";

  // ─── Bootstrap ────────────────────────────────────────────────────────────
  function init() {
    // Only mount if user is logged in (base.html sets data-user-id on body, or we check for nav-avatar)
    if (!document.querySelector(".nav-avatar")) return;

    buildLauncher();
    buildInboxPanel();
    buildStack();

    fetchInbox();
    inboxPollTimer = setInterval(fetchInbox, POLL_INBOX_MS);

    // Re-read CSRF on every request (flask-wtf rotates it)
    document.addEventListener("spark:csrf", (e) => { csrfToken = e.detail; });
  }

  // ─── DOM helpers ──────────────────────────────────────────────────────────
  function el(tag, cls, attrs = {}) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    Object.entries(attrs).forEach(([k, v]) => {
      if (k === "text") e.textContent = v;
      else if (k === "html") e.innerHTML = v;
      else e.setAttribute(k, v);
    });
    return e;
  }

  function fmtTime(iso) {
    if (!iso) return "";
    const d = new Date(iso.endsWith("Z") ? iso : iso + "Z");
    const now = new Date();
    const diff = (now - d) / 1000;
    if (diff < 60) return "now";
    if (diff < 3600) return Math.floor(diff / 60) + "m";
    if (diff < 86400) return Math.floor(diff / 3600) + "h";
    if (diff < 604800) return Math.floor(diff / 86400) + "d";
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
  }

  function fmtDate(iso) {
    if (!iso) return "";
    const d = new Date(iso.endsWith("Z") ? iso : iso + "Z");
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const msgDay = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    const diff = (today - msgDay) / 86400000;
    if (diff === 0) return "Today";
    if (diff === 1) return "Yesterday";
    return d.toLocaleDateString(undefined, { month: "short", day: "numeric", year: diff > 365 ? "numeric" : undefined });
  }

  function fmtClock(iso) {
    if (!iso) return "";
    const d = new Date(iso.endsWith("Z") ? iso : iso + "Z");
    return d.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
  }

  function avatarInitials(name) {
    if (!name) return "?";
    const parts = name.trim().split(/[\s.]+/);
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
    return name.slice(0, 2).toUpperCase();
  }

  function avatarColor(name) {
    // Cycle through teal / blue / amber / green based on name hash
    const colors = ["var(--teal)", "var(--blue)", "var(--amber)", "var(--green)"];
    let hash = 0;
    for (let i = 0; i < (name || "").length; i++) hash += name.charCodeAt(i);
    return colors[hash % colors.length];
  }

  async function apiFetch(url, opts = {}) {
    const headers = { "X-CSRFToken": csrfToken, ...(opts.headers || {}) };
    const res = await fetch(url, { ...opts, headers });
    return res;
  }

  // ─── Launcher (floating button) ──────────────────────────────────────────
  let launcherEl, launcherBadge, stackEl, inboxPanelEl;

  function buildLauncher() {
    launcherEl = el("div", "msg-launcher");

    const btn = el("button", "msg-launcher-btn", { "aria-label": "Messages", title: "Messages" });
    btn.innerHTML = `<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>`;

    launcherBadge = el("span", "msg-launcher-badge");
    launcherBadge.style.display = "none";
    btn.appendChild(launcherBadge);

    btn.addEventListener("click", toggleInbox);
    launcherEl.appendChild(btn);
    document.body.appendChild(launcherEl);
  }

  function buildStack() {
    stackEl = el("div", "msg-stack");
    document.body.appendChild(stackEl);
  }

  function updateLauncherBadge() {
    if (totalUnread > 0) {
      launcherBadge.textContent = totalUnread > 99 ? "99+" : totalUnread;
      launcherBadge.style.display = "flex";
    } else {
      launcherBadge.style.display = "none";
    }
  }

  // ─── Inbox panel ──────────────────────────────────────────────────────────
  function buildInboxPanel() {
    inboxPanelEl = el("div", "msg-panel msg-inbox-panel");

    const header = el("div", "msg-panel-header");
    const title = el("span", "msg-panel-title", { text: "Messages" });
    const actions = el("div", "msg-panel-actions");

    const newBtn = el("button", "msg-icon-btn", { title: "New message", "aria-label": "New message" });
    newBtn.innerHTML = `<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>`;
    newBtn.addEventListener("click", () => { window.location.href = "/messages/new"; });

    const closeBtn = el("button", "msg-icon-btn", { "aria-label": "Close" });
    closeBtn.innerHTML = `<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`;
    closeBtn.addEventListener("click", closeInbox);

    actions.append(newBtn, closeBtn);
    header.append(title, actions);

    const list = el("div", "msg-conv-list");
    list.id = "msg-conv-list";

    inboxPanelEl.append(header, list);
  }

  function toggleInbox() {
    inboxOpen ? closeInbox() : openInbox();
  }

  function openInbox() {
    inboxOpen = true;
    stackEl.insertBefore(inboxPanelEl, stackEl.firstChild);
    requestAnimationFrame(() => inboxPanelEl.classList.add("visible"));
    launcherEl.querySelector(".msg-launcher-btn").classList.add("open");
    renderConvList();
  }

  function closeInbox() {
    inboxOpen = false;
    inboxPanelEl.classList.remove("visible");
    launcherEl.querySelector(".msg-launcher-btn").classList.remove("open");
    setTimeout(() => {
      if (!inboxOpen && inboxPanelEl.parentNode === stackEl) {
        stackEl.removeChild(inboxPanelEl);
      }
    }, 260);
  }

  function renderConvList() {
    const list = document.getElementById("msg-conv-list");
    if (!list) return;
    list.innerHTML = "";

    if (conversations.length === 0) {
      const empty = el("div", "msg-empty");
      empty.innerHTML = `<div class="msg-empty-icon">💬</div><div class="msg-empty-text">No conversations yet</div>`;
      list.appendChild(empty);
      return;
    }

    conversations.forEach(conv => {
      const item = el("div", `msg-conv-item${conv.unread_count > 0 ? " unread" : ""}`);
      item.setAttribute("role", "button");
      item.setAttribute("tabindex", "0");

      const name = conv.title || conv.classroom_name || "Conversation";
      const initials = avatarInitials(name);
      const color = avatarColor(name);

      const avatar = el("div", "msg-conv-avatar");
      avatar.textContent = conv.avatar_emoji || initials;
      avatar.style.background = conv.avatar_emoji ? "var(--sky)" : color;
      if (conv.avatar_emoji) avatar.style.fontSize = "1.1rem";

      const info = el("div", "msg-conv-info");
      const nameEl = el("div", "msg-conv-name", { text: name });
      const preview = el("div", "msg-conv-preview", {
        text: conv.last_message_body
          ? conv.last_message_body.slice(0, 48) + (conv.last_message_body.length > 48 ? "…" : "")
          : "No messages yet"
      });
      info.append(nameEl, preview);

      const meta = el("div", "msg-conv-meta");
      const time = el("div", "msg-conv-time", { text: fmtTime(conv.last_message_at) });
      meta.appendChild(time);
      if (conv.unread_count > 0) {
        const dot = el("div", "msg-unread-dot");
        meta.appendChild(dot);
      }

      item.append(avatar, info, meta);
      item.addEventListener("click", () => openChat(conv));
      item.addEventListener("keydown", (e) => { if (e.key === "Enter") openChat(conv); });
      list.appendChild(item);
    });
  }

  // ─── Fetch inbox ──────────────────────────────────────────────────────────
  async function fetchInbox() {
    try {
      const res = await apiFetch("/messages/api/conversations");
      if (!res.ok) return;
      const data = await res.json();
      conversations = data;
      totalUnread = data.reduce((s, c) => s + (c.unread_count || 0), 0);
      updateLauncherBadge();
      if (inboxOpen) renderConvList();
      // Update open chat unread counts
      openChats.forEach(chat => pollMessages(chat));
    } catch (e) { /* network error — silently ignore */ }
  }

  // ─── Open a chat panel ────────────────────────────────────────────────────
  function openChat(conv) {
    // If already open, focus it
    const existing = openChats.find(c => c.convId === conv.id);
    if (existing) {
      existing.el.scrollTop = existing.el.querySelector(".msg-chat-body")?.scrollHeight || 0;
      return;
    }

    // Evict oldest if at max
    if (openChats.length >= MAX_OPEN_CHATS) {
      const oldest = openChats.shift();
      destroyChat(oldest);
    }

    const panel = buildChatPanel(conv);
    stackEl.appendChild(panel.el);
    requestAnimationFrame(() => panel.el.classList.add("visible"));

    openChats.push(panel);
    loadMessages(panel);

    // Close inbox on mobile
    if (window.innerWidth < 641) closeInbox();
  }

  function destroyChat(chat) {
    clearInterval(chat.pollTimer);
    chat.el.classList.remove("visible");
    setTimeout(() => chat.el.parentNode?.removeChild(chat.el), 260);
  }

  function buildChatPanel(conv) {
    const panel = el("div", "msg-panel msg-chat-panel");

    // Header
    const header = el("div", "msg-chat-header");
    const name = conv.title || conv.classroom_name || "Conversation";
    const initials = avatarInitials(name);
    const color = avatarColor(name);

    const avatar = el("div", "msg-chat-avatar");
    avatar.textContent = conv.avatar_emoji || initials;
    avatar.style.background = conv.avatar_emoji ? "var(--sky)" : color;
    if (conv.avatar_emoji) avatar.style.fontSize = "1rem";

    const headerInfo = el("div", "msg-chat-header-info", {});
    headerInfo.style.cssText = "flex:1;min-width:0;";
    const nameEl = el("div", "msg-chat-name", { text: name });
    const classroom = el("div", "msg-chat-classroom", { text: conv.classroom_name || "" });
    headerInfo.append(nameEl, classroom);

    const headerActions = el("div", "msg-panel-actions");
    const expandBtn = el("button", "msg-icon-btn", { title: "Open full view", "aria-label": "Open full view" });
    expandBtn.innerHTML = `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 3 21 3 21 9"/><polyline points="9 21 3 21 3 15"/><line x1="21" y1="3" x2="14" y2="10"/><line x1="3" y1="21" x2="10" y2="14"/></svg>`;
    expandBtn.addEventListener("click", (e) => { e.stopPropagation(); window.location.href = `/messages/${conv.id}`; });

    const closeBtn = el("button", "msg-icon-btn", { "aria-label": "Close chat" });
    closeBtn.innerHTML = `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`;
    closeBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      const idx = openChats.findIndex(c => c.convId === conv.id);
      if (idx !== -1) { destroyChat(openChats[idx]); openChats.splice(idx, 1); }
    });

    headerActions.append(expandBtn, closeBtn);
    header.append(avatar, headerInfo, headerActions);
    header.addEventListener("click", () => window.location.href = `/messages/${conv.id}`);

    // Body
    const body = el("div", "msg-chat-body");
    body.id = `msg-body-${conv.id}`;
    const loading = el("div", "msg-chat-loading");
    loading.innerHTML = `<div class="msg-typing-dot"><span></span><span></span><span></span></div>`;
    body.appendChild(loading);

    // Compose
    const compose = el("div", "msg-compose");
    const input = el("textarea", "msg-compose-input", { placeholder: "Write a message…", rows: "1", "aria-label": "Message input" });

    const sendBtn = el("button", "msg-send-btn", { "aria-label": "Send", disabled: "true" });
    sendBtn.innerHTML = `<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>`;

    input.addEventListener("input", () => {
      input.style.height = "auto";
      input.style.height = Math.min(input.scrollHeight, 96) + "px";
      sendBtn.disabled = !input.value.trim();
    });

    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        if (input.value.trim()) sendMessage(chatObj, input, sendBtn);
      }
    });

    sendBtn.addEventListener("click", () => {
      if (input.value.trim()) sendMessage(chatObj, input, sendBtn);
    });

    compose.append(input, sendBtn);
    panel.append(header, body, compose);

    const chatObj = {
      convId: conv.id,
      conv,
      el: panel,
      body,
      input,
      sendBtn,
      lastMsgId: 0,
      memberMap: {},
      pollTimer: null,
    };

    return chatObj;
  }

  // ─── Load & poll messages ─────────────────────────────────────────────────
  async function loadMessages(chat) {
    try {
      const res = await apiFetch(`/messages/${chat.convId}/messages`);
      if (!res.ok) {
        showChatError(chat, res.status === 403 ? "Access denied." : "Could not load messages.");
        return;
      }
      const msgs = await res.json();
      chat.body.innerHTML = "";

      if (msgs.length === 0) {
        const empty = el("div", "msg-empty");
        empty.innerHTML = `<div class="msg-empty-icon">👋</div><div class="msg-empty-text">Say hello!</div>`;
        chat.body.appendChild(empty);
      } else {
        renderMessages(chat, msgs, true);
      }

      // Start polling
      chat.pollTimer = setInterval(() => pollMessages(chat), POLL_CHAT_MS);
      markRead(chat.convId);
    } catch (e) {
      showChatError(chat, "Network error.");
    }
  }

  async function pollMessages(chat) {
    if (!chat.lastMsgId) return;
    try {
      const res = await apiFetch(`/messages/${chat.convId}/messages?after_id=${chat.lastMsgId}`);
      if (!res.ok) return;
      const msgs = await res.json();
      if (msgs.length > 0) {
        renderMessages(chat, msgs, false);
        markRead(chat.convId);
        // Update inbox unread counts
        const conv = conversations.find(c => c.id === chat.convId);
        if (conv) conv.unread_count = 0;
        totalUnread = conversations.reduce((s, c) => s + (c.unread_count || 0), 0);
        updateLauncherBadge();
        if (inboxOpen) renderConvList();
      }
    } catch (e) { /* silently ignore poll errors */ }
  }

  function renderMessages(chat, msgs, initialLoad) {
    const currentUserId = getCurrentUserId();
    let lastDate = null;

    // Build member map on first load
    if (initialLoad) {
      msgs.forEach(m => {
        if (m.sender_id && m.username) {
          chat.memberMap[m.sender_id] = { username: m.username, display_name: m.display_name, avatar_emoji: m.avatar_emoji };
        }
      });
    }

    // Remove empty state if present
    const empty = chat.body.querySelector(".msg-empty");
    if (empty) empty.remove();

    const wasAtBottom = chat.body.scrollHeight - chat.body.scrollTop - chat.body.clientHeight < 60;

    msgs.forEach(m => {
      const msgDate = fmtDate(m.created_at);
      if (msgDate !== lastDate) {
        const sep = el("div", "msg-date-sep", { text: msgDate });
        chat.body.appendChild(sep);
        lastDate = msgDate;
      }

      const isMine = m.sender_id === currentUserId;
      const wrap = el("div", `msg-bubble-wrap ${isMine ? "mine" : "theirs"}`);

      if (!isMine) {
        const senderName = m.display_name || m.username || "";
        if (senderName) {
          const nameLabel = el("div", "msg-sender-name", { text: senderName });
          wrap.appendChild(nameLabel);
        }
      }

      const bubble = el("div", `msg-bubble ${isMine ? "mine" : "theirs"}`, { text: m.body });
      const timeEl = el("div", "msg-bubble-time", { text: fmtClock(m.created_at) });

      wrap.append(bubble, timeEl);
      chat.body.appendChild(wrap);

      if (m.id > chat.lastMsgId) chat.lastMsgId = m.id;
    });

    if (initialLoad || wasAtBottom) {
      chat.body.scrollTop = chat.body.scrollHeight;
    }
  }

  function showChatError(chat, msg) {
    chat.body.innerHTML = `<div class="msg-empty"><div class="msg-empty-icon">⚠️</div><div class="msg-empty-text">${msg}</div></div>`;
  }

  // ─── Send message ─────────────────────────────────────────────────────────
  async function sendMessage(chat, input, sendBtn) {
    const body = input.value.trim();
    if (!body) return;

    sendBtn.disabled = true;
    const original = input.value;
    input.value = "";
    input.style.height = "auto";

    try {
      const form = new FormData();
      form.append("body", body);
      form.append("csrf_token", csrfToken);

      const res = await apiFetch(`/messages/${chat.convId}/send`, { method: "POST", body: form });

      if (res.ok || res.redirected) {
        // Optimistically render — poll will catch it if we miss it
        const now = new Date().toISOString();
        const currentUserId = getCurrentUserId();
        const fakeMsg = {
          id: Date.now(), // temp id — will be overwritten on next poll
          body,
          sender_id: currentUserId,
          username: getCurrentUsername(),
          display_name: getCurrentUsername(),
          avatar_emoji: null,
          created_at: now,
        };
        renderMessages(chat, [fakeMsg], false);

        // Also bump the inbox preview
        const conv = conversations.find(c => c.id === chat.convId);
        if (conv) { conv.last_message_body = body; conv.last_message_at = now; }
        if (inboxOpen) renderConvList();

        // Immediate poll to get real message id
        setTimeout(() => pollMessages(chat), 600);
      } else {
        input.value = original;
        sendBtn.disabled = false;
      }
    } catch (e) {
      input.value = original;
      sendBtn.disabled = false;
    }
  }

  // ─── Mark read ────────────────────────────────────────────────────────────
  async function markRead(convId) {
    try {
      const form = new FormData();
      form.append("csrf_token", csrfToken);
      await apiFetch(`/messages/${convId}/mark-read`, { method: "POST", body: form });
    } catch (e) { /* ignore */ }
  }

  // ─── Helpers ──────────────────────────────────────────────────────────────
  function getCurrentUserId() {
    // Read from data attribute we'll add to body in base.html
    return parseInt(document.body.dataset.userId || "0", 10);
  }

  function getCurrentUsername() {
    return document.body.dataset.username || "";
  }

  // ─── Boot ─────────────────────────────────────────────────────────────────
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

})();

function toggleCreateMenu() {
  const menu = document.getElementById('create-menu');
  if (!menu) return;
  menu.style.display = menu.style.display === 'block' ? 'none' : 'block';
}

document.addEventListener('click', function(e) {
  const wrap = document.getElementById('create-menu-wrap');
  if (wrap && !wrap.contains(e.target)) {
    const menu = document.getElementById('create-menu');
    if (menu) menu.style.display = 'none';
  }
});