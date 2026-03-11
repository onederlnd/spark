# Devstack Feature Tracker

## Completed
- [x] User auth (register/login/logout) `[PR]`
- [x] Posts, replies, voting `[PR]`
- [x] Topics `[PR]`
- [x] Bookmarks `[PR]`
- [x] User profiles `[PR]`
- [x] Post editing & deletion `[PR]`
- [x] Feed pagination `[PR]`
- [x] Full-text search (FTS5) `[PR]`
- [x] User following & personalized feed `[PR]`
- [x] Notifications `[PR]`
- [x] Docker & CI/CD `[PR]`
- [x] Dev workflow scripts `[PR]`
- [x] Rate limiting `[PR]`
- [x] Error pages `[PR]`
- [x] REST API `[PR]`
- [x] CSRF protection `[PR]`
- [x] Bcrypt password hashing `[PR]`
- [x] Admin CLI tool `[PR]`
- [x] Alembic migrations `[PR]`
- [x] User settings page `[PR]`

---

## Up Next (after brute force)
ALMOST ALL HTML/JS/CSS (c/p)
- [ ] Dark/light theme toggle
- [ ] Mobile sidebar hamburger menu
- [ ] BBCode preview while typing
- [ ] Character counters on title, bio, topic name fields
- [ ] Empty state illustrations



## Alpha / Early Testing
### Phase 1 — Safety Core (ship before any public users)
- [x] Input sanitization / XSS prevention — sanitize all user input before rendering `[Alpha]`
- [x] Brute force protection — lockout after failed login attempts `[Alpha]`
- [ ] Rate limiting on registration — prevent bot account creation `[Alpha]`
- [ ] Session timeout — auto-logout after inactivity for shared school computers `[Alpha]`
- [ ] Report system — flag posts/users for moderation review `[Alpha]`
- [ ] Content moderation queue — hold flagged content for review before visible `[Alpha]`
- [ ] User blocking — filter content from blocked users `[Alpha]`
- [ ] Age-appropriate content filtering — baseline keyword/content rules `[Alpha]`
- [ ] COPPA compliance — Terms of Service and Privacy Policy pages (legally required for minors) `[Alpha]`

---

## Beta / Trust & Verification
### Phase 2 — Trust & Verification (makes it real for parents and schools)
- [ ] Email verification on register `[Beta]`
- [ ] Admin dashboard — proper moderation UI, not just CLI tools `[Beta]`
- [ ] Parent dashboard — visibility into student activity `[Beta]`
- [ ] Teacher pages — dedicated hosted pages for educators `[Beta]`
- [ ] Class/group channels — private spaces for classrooms `[Beta]`
- [ ] Topic moderators — role-based permissions per topic `[Beta]`
- [ ] School/district accounts — umbrella accounts managing multiple teacher pages `[Beta]`

---

## Public Release / Growth & Engagement
### Phase 3 — Growth & Engagement (once the platform is trusted)
- [ ] Onboarding flow — guide new users to follow topics and people on first login `[PR]`
- [ ] User mentions — @username triggers a notification `[PR]`
- [ ] Achievement badges — lightweight engagement without dark patterns `[PR]`
- [ ] Direct messages — teacher↔student only initially, not peer-to-peer `[PR]`
- [ ] Landing page — public-facing marketing site `[PR]`
- [ ] Data export — users can download their own data `[PR]`
- [ ] Trending algorithm — weight posts by votes, reply count, and time decay instead of raw vote count `[PR]`

---

## Ops & Hardening
### Phase 4 — Ops & Hardening (runs alongside other phases)
- [ ] Full audit log — track all data changes with who/when/what `[Alpha/Beta]`
- [ ] Structured logging — replace print statements with proper log levels `[Alpha/Beta]`
- [ ] Health check endpoint — /health returns app and DB status `[Alpha/Beta]`
- [ ] Database backups — scheduled backup script with rotation `[Alpha/Beta]`
- [ ] Dependency vulnerability scanning — pip-audit in CI pipeline `[Alpha/Beta]`
- [ ] Feature flags — toggle features on/off without deploying `[Alpha/Beta]`

## Add to list



## Backlog
- [ ] Convert pasted HTML to BBCode on input (e.g. `<b>` → `[b]`, `<a href="">` → `[url=]`)
- [ ] BBCode toolbar in post/reply composer
- [ ] Homeschool mode — parent receives lockout notifications instead of teacher
- [ ] PWA support — manifest.json, service worker, home screen icon (2-3hrs)
- [ ] Penpals