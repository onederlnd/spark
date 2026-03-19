# Devstack Feature Tracker

## Completed

- [x] User auth (register/login/logout)
- [x] Posts, replies, voting
- [x] Topics
- [x] Bookmarks
- [x] User profiles
- [x] Post editing & deletion
- [x] Feed pagination
- [x] Full-text search (FTS5)
- [x] User following & personalized feed
- [x] Notifications
- [x] Docker & CI/CD
- [x] Dev workflow scripts
- [x] Rate limiting
- [x] Error pages
- [x] REST API
- [x] CSRF protection
- [x] Bcrypt password hashing
- [x] Admin CLI tool
- [x] Alembic migrations
- [x] User settings page
- [x] Dark/light theme toggle
- [x] Mobile sidebar hamburger menu
- [x] BBCode preview while typing
- [x] Character counters on title, bio, topic name fields
- [x] Empty state illustrations
- [x] Input sanitization / XSS prevention
- [x] Brute force protection
- [x] Session timeout — auto logout after inactivity

---

## Alpha / Closed Beta

### Phase 1 — Safety Core

- [x] Rate limiting on registration — prevent bot account creation
- [ ] Report system — flag posts/users for moderation review
- [ ] Content moderation queue — hold flagged content for teacher review
- [ ] User blocking — filter content from blocked users
- [ ] Age-appropriate content filtering — baseline keyword/content rules
- [x] COPPA compliance — Terms of Service and Privacy Policy pages

---

### Phase 2 — Classroom System

- [x] Classroom DB models — `classrooms`, `classroom_students`, `lessons`, `assignments`, `submissions`
- [x] Classroom dashboard — teacher overview of all classes
- [x] Create/join classroom — teacher creates, students join via code
- [x] Lessons — rich BBCode content pages with auto-created discussion thread
- [x] Assignments — instructions + due date + submissions + auto-created discussion thread
- [x] Student submissions — submit work, one per student per assignment
- [x] Grading UI — teacher grades submissions with feedback
- [x] Submission grid — teacher sees all students and status at a glance
- [x] Role gating — teacher/student/parent enforcement across classroom routes

---

## Beta / Trust & Verification

### Phase 3 — Trust & Verification

- [ ] Email verification on register
- [ ] Admin dashboard — proper moderation UI
- [ ] Parent dashboard — visibility into student activity
- [ ] Topic moderators — role-based permissions per topic
- [ ] School/district accounts — umbrella accounts managing multiple classrooms
- [ ] Safety visibility modes — teacher can toggle full view vs flagged-only
- [ ] Auto-hide flagged content — hold for review and notify teacher

---

## Public Release / Growth & Engagement

### Phase 4 — Growth & Engagement

- [ ] Onboarding flow — guide new users on first login
- [ ] User mentions — `@username` triggers notification
- [ ] Achievement badges — lightweight engagement without dark patterns
- [ ] Direct messages — teacher ↔ student only initially
- [ ] Landing page — public marketing site
- [ ] Data export — users can download their own data
- [ ] Trending algorithm — weight by votes, replies, and time decay

---

## Ops & Hardening

### Phase 5 — Ops & Hardening

- [ ] Full audit log — track all data changes with who/when/what
- [ ] Structured logging — replace print statements with proper log levels
- [ ] Health check endpoint — `/health` returns app and DB status
- [ ] Database backups — scheduled backup script with rotation
- [ ] Dependency vulnerability scanning — `pip-audit` in CI pipeline
- [ ] Feature flags — toggle features without deploying

---

## Backlog

- [ ] Rubric grading — structured scoring within assignments
- [ ] Multiple choice / checkbox assignment types
- [ ] Homeschool mode — parent receives notifications instead of teacher
- [ ] BBCode install
- [ ] PWA support — manifest.json + service worker
- [ ] Penpals
- [x] User not found page returns formatted error instead of white page
- [ ] Upgrade COPPA
- [ ] Update API
- [ ] WebSocket update for "COPPA pending" screen instead of relogging in. (similar to netflix/xbox on /activate)
- [ ] Add teacher_required() decorator