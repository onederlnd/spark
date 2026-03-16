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
- [x] Dark/light theme toggle
- [x] Mobile sidebar hamburger menu
- [x] BBCode preview while typing
- [x] Character counters on title, bio, topic name fields
- [x] Empty state illustrations
- [x] Input sanitization / XSS prevention `[Alpha]`
- [x] Brute force protection `[Alpha]`
- [x] Session timeout — auto-logout after inactivity `[Alpha]`

---

## Alpha / Closed Beta
### Phase 1 — Safety Core (ship before any public users)
- [x] Rate limiting on registration — prevent bot account creation `[Alpha]`
- [ ] Report system — flag posts/users for moderation review `[Alpha]`
- [ ] Content moderation queue — hold flagged content for teacher review `[Alpha]`
- [ ] User blocking — filter content from blocked users `[Alpha]`
- [ ] Age-appropriate content filtering — baseline keyword/content rules `[Alpha]`
- [i] COPPA compliance — Terms of Service and Privacy Policy pages `[Alpha]`

### Phase 2 — Classroom System (core product differentiator)
- [x] Classroom DB models — `classrooms`, `classroom_students`, `lessons`, `assignments`, `submissions` `[Alpha]`
- [x] Classroom dashboard — teacher overview of all classes `[Alpha]`
- [x] Create/join classroom — teacher creates, students join via code `[Alpha]`
- [x] Lessons — rich BBCode content pages with auto-created discussion thread `[Alpha]`
- [x] Assignments — instructions + due date + submissions + auto-created discussion thread `[Alpha]`
- [x] Student submissions — submit work, one per student per assignment `[Alpha]`
- [x] Grading UI — teacher grades submissions with feedback, next/prev student navigation `[Alpha]`
- [x] Submission grid — teacher sees all students + status at a glance `[Alpha]`
- [x] Role gating — teacher/student/parent role enforcement across all classroom routes `[Alpha]`

---

## Beta / Trust & Verification
### Phase 3 — Trust & Verification (makes it real for parents and schools)
- [ ] Email verification on register `[Beta]`
- [ ] Admin dashboard — proper moderation UI, not just CLI tools `[Beta]`
- [ ] Parent dashboard — visibility into student activity `[Beta]`
- [ ] Topic moderators — role-based permissions per topic `[Beta]`
- [ ] School/district accounts — umbrella accounts managing multiple classrooms `[Beta]`
- [ ] Safety visibility modes — teacher can toggle full view vs flagged-only `[Beta]`
- [ ] Auto-hide flagged content — hold for review, notify teacher immediately `[Beta]`

---

## Public Release / Growth & Engagement
### Phase 4 — Growth & Engagement (once the platform is trusted)
- [ ] Onboarding flow — guide new users on first login `[PR]`
- [ ] User mentions — @username triggers a notification `[PR]`
- [ ] Achievement badges — lightweight engagement without dark patterns `[PR]`
- [ ] Direct messages — teacher↔student only initially, not peer-to-peer `[PR]`
- [ ] Landing page — public-facing marketing site `[PR]`
- [ ] Data export — users can download their own data `[PR]`
- [ ] Trending algorithm — weight by votes, reply count, and time decay `[PR]`

---

## Ops & Hardening
### Phase 5 — Ops & Hardening (runs alongside other phases)
- [ ] Full audit log — track all data changes with who/when/what `[Alpha/Beta]`
- [ ] Structured logging — replace print statements with proper log levels `[Alpha/Beta]`
- [ ] Health check endpoint — /health returns app and DB status `[Alpha/Beta]`
- [ ] Database backups — scheduled backup script with rotation `[Alpha/Beta]`
- [ ] Dependency vulnerability scanning — pip-audit in CI pipeline `[Alpha/Beta]`
- [ ] Feature flags — toggle features on/off without deploying `[Alpha/Beta]`

---

## Backlog
- [ ] Rubric grading — structured scoring within assignments
- [ ] Multiple choice / checkbox assignment types — minimize required typing for younger students
- [ ] Homeschool mode — parent receives notifications instead of teacher
- [ ] BBCode Install
- [ ] PWA support — manifest.json, service worker, home screen icon
- [ ] Penpals
- [x] User not found returns white "User not found" error page instead of formatted 
- [ ] Upgrade COPPA
- [ ] Update API
- [ ] Use Websockets to update "COPPA pending" screen to feed without logging out